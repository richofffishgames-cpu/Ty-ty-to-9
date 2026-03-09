import os
import json
import logging
import base64
from datetime import datetime
from flask import Flask, request, jsonify
from google.cloud import pubsub_v1, firestore
import nmap
import requests
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize GCP clients
project_id = os.environ.get('PROJECT_ID')
publisher = pubsub_v1.PublisherClient()
db = firestore.Client()

# Topic paths
validated_topic = publisher.topic_path(project_id, 'validated-targets')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "validation-agent"}), 200

@app.route('/', methods=['POST'])
def validate_hypothesis():
    try:
        # Handle Pub/Sub message
        envelope = request.get_json()
        if not envelope:
            return jsonify({"error": "No Pub/Sub message"}), 400

        # Decode message
        message_data = base64.b64decode(envelope['message']['data']).decode('utf-8')
        hypothesis = json.loads(message_data)

        logger.info(f"Validating hypothesis for {hypothesis['target']}:{hypothesis['port']}")

        # Perform validation based on service type
        validation_result = perform_validation(hypothesis)

        # Log validation attempt
        validation_doc = {
            'scan_id': hypothesis['scan_id'],
            'target': hypothesis['target'],
            'port': hypothesis['port'],
            'service': hypothesis['service'],
            'validation_result': validation_result,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'agent': 'validation'
        }
        db.collection('validations').add(validation_doc)

        # If validation successful, publish to validated targets
        if validation_result['is_vulnerable']:
            validated_target = {
                'scan_id': hypothesis['scan_id'],
                'target': hypothesis['target'],
                'port': hypothesis['port'],
                'service': hypothesis['service'],
                'vulnerability': validation_result['vulnerability'],
                'severity': validation_result['severity'],
                'exploit_path': validation_result.get('exploit_path'),
                'validation_timestamp': datetime.utcnow().isoformat()
            }
            message_data = json.dumps(validated_target).encode('utf-8')
            publisher.publish(validated_topic, message_data)
            logger.info(f"Published validated target: {hypothesis['target']}:{hypothesis['port']}")

        return jsonify({"status": "validation_complete"}), 200

    except Exception as e:
        logger.error(f"Error in validation: {str(e)}")
        return jsonify({"error": str(e)}), 500

def perform_validation(hypothesis):
    """Perform actual validation checks based on service type"""
    target = hypothesis['target']
    port = hypothesis['port']
    service = hypothesis['service']

    validation_result = {
        'is_vulnerable': False,
        'vulnerability': None,
        'severity': 'low',
        'details': {}
    }

    try:
        # HTTP/HTTPS services
        if service in ['http', 'https'] or port in [80, 443, 8080, 8443]:
            validation_result = validate_web_service(target, port, service)
        # SSH services
        elif service == 'ssh' or port == 22:
            validation_result = validate_ssh_service(target, port)
        # FTP services
        elif service == 'ftp' or port == 21:
            validation_result = validate_ftp_service(target, port)
        # SMB services
        elif service == 'microsoft-ds' or port in [139, 445]:
            validation_result = validate_smb_service(target, port)
        # Generic port validation
        else:
            validation_result = validate_generic_service(target, port, service)
    except Exception as e:
        logger.error(f"Validation error for {target}:{port} - {str(e)}")
        validation_result['details']['error'] = str(e)

    return validation_result

def validate_web_service(target, port, service):
    """Validate web services for common vulnerabilities"""
    result = {'is_vulnerable': False, 'vulnerability': None, 'severity': 'low', 'details': {}}

    try:
        # Basic HTTP response check
        protocol = 'https' if service == 'https' or port == 443 else 'http'
        url = f"{protocol}://{target}:{port}"
        response = requests.get(url, timeout=10, verify=False)

        result['details']['status_code'] = response.status_code
        result['details']['headers'] = dict(response.headers)

        # Check for common misconfigurations
        if 'Server' in response.headers:
            server = response.headers['Server'].lower()
            result['details']['server'] = server

            # Check for outdated servers
            if 'apache/2.2' in server or 'nginx/1.0' in server:
                result['is_vulnerable'] = True
                result['vulnerability'] = 'outdated_server'
                result['severity'] = 'medium'

        # Check for directory listing
        if 'index of /' in response.text.lower():
            result['is_vulnerable'] = True
            result['vulnerability'] = 'directory_listing'
            result['severity'] = 'low'

        # Check for default pages
        if any(phrase in response.text.lower() for phrase in ['welcome to apache', 'nginx default page', 'iis default']):
            result['is_vulnerable'] = True
            result['vulnerability'] = 'default_page'
            result['severity'] = 'low'

    except requests.exceptions.RequestException as e:
        result['details']['connection_error'] = str(e)

    return result

def validate_ssh_service(target, port):
    """Validate SSH services"""
    result = {'is_vulnerable': False, 'vulnerability': None, 'severity': 'low', 'details': {}}

    try:
        # Use nmap to get SSH version info
        nm = nmap.PortScanner()
        scan_result = nm.scan(target, str(port), arguments='-sV --script ssh2-enum-algos')

        if target in nm.all_hosts():
            port_info = nm[target]['tcp'].get(port, {})
            if port_info:
                result['details']['version'] = port_info.get('version', '')
                result['details']['product'] = port_info.get('product', '')

                # Check for weak algorithms or old versions
                if 'openssh' in port_info.get('product', '').lower():
                    version = port_info.get('version', '')
                    if version and any(old_ver in version for old_ver in ['4.', '5.', '6.0', '6.1']):
                        result['is_vulnerable'] = True
                        result['vulnerability'] = 'outdated_ssh'
                        result['severity'] = 'medium'
    except Exception as e:
        result['details']['scan_error'] = str(e)

    return result

def validate_ftp_service(target, port):
    """Validate FTP services"""
    result = {'is_vulnerable': False, 'vulnerability': None, 'severity': 'low', 'details': {}}

    try:
        # Check for anonymous FTP access
        import ftplib
        ftp = ftplib.FTP()
        ftp.set_debuglevel(0)
        ftp.connect(target, port, timeout=10)
        try:
            ftp.login('anonymous', 'anonymous@test.com')
            result['is_vulnerable'] = True
            result['vulnerability'] = 'anonymous_ftp'
            result['severity'] = 'high'
            result['details']['anonymous_access'] = True
            ftp.quit()
        except ftplib.error_perm:
            result['details']['anonymous_access'] = False
    except Exception as e:
        result['details']['connection_error'] = str(e)

    return result

def validate_smb_service(target, port):
    """Validate SMB services"""
    result = {'is_vulnerable': False, 'vulnerability': None, 'severity': 'low', 'details': {}}

    try:
        # Use nmap SMB scripts for enumeration
        nm = nmap.PortScanner()
        scan_result = nm.scan(target, str(port), arguments='--script smb-enum-shares,smb-os-discovery')

        if target in nm.all_hosts():
            port_info = nm[target]['tcp'].get(port, {})
            if 'script' in port_info:
                scripts = port_info['script']
                # Check for null session access
                if 'smb-enum-shares' in scripts:
                    shares_output = scripts['smb-enum-shares']
                    if 'anonymous access' in shares_output.lower():
                        result['is_vulnerable'] = True
                        result['vulnerability'] = 'smb_null_session'
                        result['severity'] = 'high'
                        result['details']['smb_scripts'] = scripts
    except Exception as e:
        result['details']['scan_error'] = str(e)

    return result

def validate_generic_service(target, port, service):
    """Generic validation for other services"""
    result = {'is_vulnerable': False, 'vulnerability': None, 'severity': 'low', 'details': {}}

    try:
        # Basic connectivity test
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        connection_result = sock.connect_ex((target, port))
        sock.close()

        if connection_result == 0:
            result['details']['port_open'] = True
            # For now, just mark as potential target for further investigation
            result['is_vulnerable'] = True
            result['vulnerability'] = 'open_port'
            result['severity'] = 'low'
        else:
            result['details']['port_open'] = False
    except Exception as e:
        result['details']['connection_error'] = str(e)

    return result

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
