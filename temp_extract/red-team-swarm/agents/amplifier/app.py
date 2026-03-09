import os
import json
import logging
import base64
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify
from google.cloud import pubsub_v1, firestore, storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize GCP clients
project_id = os.environ.get('PROJECT_ID')
publisher = pubsub_v1.PublisherClient()
db = firestore.Client()
storage_client = storage.Client()
bucket = storage_client.bucket(os.environ.get('ARTIFACT_BUCKET'))

# Topic paths
foothold_topic = publisher.topic_path(project_id, 'foothold-achieved')
human_decision_topic = publisher.topic_path(project_id, 'human-decision-point')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "amplifier-agent"}), 200

@app.route('/', methods=['POST'])
def exploit_target():
    try:
        # Handle Pub/Sub message
        envelope = request.get_json()
        if not envelope:
            return jsonify({"error": "No Pub/Sub message"}), 400

        # Decode message
        message_data = base64.b64decode(envelope['message']['data']).decode('utf-8')
        validated_target = json.loads(message_data)

        logger.info(f"Attempting exploitation of {validated_target['target']}:{validated_target['port']}")

        # Perform exploitation attempt
        exploit_result = attempt_exploitation(validated_target)

        # Log exploitation attempt
        exploit_doc = {
            'scan_id': validated_target['scan_id'],
            'target': validated_target['target'],
            'port': validated_target['port'],
            'service': validated_target['service'],
            'vulnerability': validated_target['vulnerability'],
            'exploit_result': exploit_result,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'agent': 'amplifier'
        }
        db.collection('exploitations').add(exploit_doc)

        # If exploitation successful, trigger human decision point
        if exploit_result['success']:
            foothold_data = {
                'scan_id': validated_target['scan_id'],
                'target': validated_target['target'],
                'port': validated_target['port'],
                'access_level': exploit_result['access_level'],
                'payload_type': exploit_result['payload_type'],
                'timestamp': datetime.utcnow().isoformat(),
                'requires_decision': True
            }

            # Publish foothold achievement
            message_data = json.dumps(foothold_data).encode('utf-8')
            publisher.publish(foothold_topic, message_data)

            # Request human decision
            decision_request = {
                'type': 'foothold_achieved',
                'target': validated_target['target'],
                'details': exploit_result,
                'options': ['continue_lateral_movement', 'gather_intelligence', 'stop_engagement'],
                'timestamp': datetime.utcnow().isoformat()
            }
            decision_data = json.dumps(decision_request).encode('utf-8')
            publisher.publish(human_decision_topic, decision_data)

            logger.info(f"Foothold achieved on {validated_target['target']} - Awaiting human decision")

        return jsonify({"status": "exploitation_complete", "success": exploit_result['success']}), 200

    except Exception as e:
        logger.error(f"Error in exploitation: {str(e)}")
        return jsonify({"error": str(e)}), 500

def attempt_exploitation(target_info):
    """Attempt exploitation based on vulnerability type"""
    exploit_result = {
        'success': False,
        'access_level': None,
        'payload_type': None,
        'output': '',
        'error': None
    }

    target = target_info['target']
    port = target_info['port']
    vulnerability = target_info['vulnerability']
    service = target_info['service']

    try:
        # **CRITICAL: Only perform safe, non-destructive proofs of concept**
        # This is a demonstration - real implementations should have strict controls

        if vulnerability == 'anonymous_ftp':
            exploit_result = exploit_anonymous_ftp(target, port)
        elif vulnerability == 'smb_null_session':
            exploit_result = exploit_smb_null_session(target, port)
        elif vulnerability == 'directory_listing':
            exploit_result = exploit_directory_listing(target, port, service)
        elif vulnerability == 'outdated_server':
            exploit_result = exploit_outdated_server(target, port, service)
        else:
            # Generic exploitation attempt (minimal impact)
            exploit_result = generic_exploitation_attempt(target, port, service)

    except Exception as e:
        exploit_result['error'] = str(e)
        logger.error(f"Exploitation error: {str(e)}")

    return exploit_result

def exploit_anonymous_ftp(target, port):
    """Safely exploit anonymous FTP access"""
    result = {'success': False, 'access_level': None, 'payload_type': 'ftp_access', 'output': ''}

    try:
        import ftplib
        ftp = ftplib.FTP()
        ftp.connect(target, port, timeout=10)
        ftp.login('anonymous', 'test@example.com')

        # List directories (read-only operation)
        file_list = []
        ftp.retrlines('LIST', file_list.append)

        result['success'] = True
        result['access_level'] = 'anonymous_read'
        result['output'] = '\n'.join(file_list[:10])  # Limit output
        ftp.quit()
    except Exception as e:
        result['error'] = str(e)

    return result

def exploit_smb_null_session(target, port):
    """Safely exploit SMB null session"""
    result = {'success': False, 'access_level': None, 'payload_type': 'smb_enum', 'output': ''}

    try:
        # Use smbclient for enumeration (read-only)
        cmd = f"smbclient -L //{target} -N"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

        if process.returncode == 0:
            result['success'] = True
            result['access_level'] = 'information_disclosure'
            result['output'] = process.stdout[:500]  # Limit output
        else:
            result['error'] = process.stderr
    except subprocess.TimeoutExpired:
        result['error'] = 'Command timeout'
    except Exception as e:
        result['error'] = str(e)

    return result

def exploit_directory_listing(target, port, service):
    """Exploit directory listing vulnerability"""
    result = {'success': False, 'access_level': None, 'payload_type': 'web_enum', 'output': ''}

    try:
        import requests
        protocol = 'https' if service == 'https' or port == 443 else 'http'
        url = f"{protocol}://{target}:{port}/"
        response = requests.get(url, timeout=10, verify=False)

        if response.status_code == 200 and 'index of' in response.text.lower():
            result['success'] = True
            result['access_level'] = 'information_disclosure'
            result['output'] = 'Directory listing accessible'

            # Extract file names (limited)
            import re
            files = re.findall(r'href="([^"]*)"', response.text)
            result['output'] += f"\nFiles found: {files[:5]}"  # Limit to 5 files
    except Exception as e:
        result['error'] = str(e)

    return result

def exploit_outdated_server(target, port, service):
    """Check for known vulnerabilities in outdated servers"""
    result = {'success': False, 'access_level': None, 'payload_type': 'vuln_scan', 'output': ''}

    try:
        # Use nmap vulnerability scripts (safe scanning only)
        import nmap
        nm = nmap.PortScanner()
        scan_result = nm.scan(target, str(port), arguments='--script vuln --script-args safe=1')

        if target in nm.all_hosts():
            port_info = nm[target]['tcp'].get(port, {})
            if 'script' in port_info:
                result['success'] = True
                result['access_level'] = 'vulnerability_confirmed'
                result['output'] = str(port_info['script'])[:500]  # Limit output
    except Exception as e:
        result['error'] = str(e)

    return result

def generic_exploitation_attempt(target, port, service):
    """Generic safe exploitation attempt"""
    result = {'success': False, 'access_level': None, 'payload_type': 'connection_test', 'output': ''}

    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        if sock.connect_ex((target, port)) == 0:
            result['success'] = True
            result['access_level'] = 'network_access'
            result['output'] = f'Confirmed access to {target}:{port}'
        sock.close()
    except Exception as e:
        result['error'] = str(e)

    return result

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
