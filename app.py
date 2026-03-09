import os
import json
import logging
import re
import socket
from datetime import datetime
from flask import Flask, request, jsonify
from google.cloud import pubsub_v1, firestore, storage
import nmap
import subprocess
import uuid

# Configure logging
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
recon_topic = publisher.topic_path(project_id, 'recon-hypotheses')

def is_valid_target(target):
    """
    Validates that the target is a valid IP address or hostname.
    Prevents command/argument injection into nmap.
    """
    if not target or len(target) > 255:
        return False

    # Check if it's a valid IP address (v4 or v6)
    try:
        socket.inet_aton(target)
        return True
    except socket.error:
        pass

    try:
        socket.inet_pton(socket.AF_INET6, target)
        return True
    except socket.error:
        pass

    # Check if it's a valid hostname
    # Hostnames can contain letters, numbers, hyphens, and dots.
    # They must not start or end with a hyphen.
    # Labels must be 1-63 characters.
    hostname_regex = re.compile(
        r"^"                             # Start of line
        r"(?:[a-zA-Z0-9]"                # First character of a label
        r"(?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*" # Middle labels
        r"[a-zA-Z0-9]"                   # First character of last label
        r"(?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?" # Last label
        r"$"                             # End of line
    )

    return bool(hostname_regex.match(target))

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "recon-agent"}), 200

@app.route('/', methods=['POST'])
def scan_target():
    try:
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        target = data.get('target')
        scan_type = data.get('scan_type', 'basic')
        
        if not target:
            return jsonify({"error": "Target is required"}), 400
        
        # 🛡️ Sentinel: Validate target to prevent injection
        if not is_valid_target(target):
            logger.warning(f"Invalid target attempt: {target}")
            return jsonify({"error": "Invalid target format. Use a valid IP or hostname."}), 400

        logger.info(f"Starting recon scan for target: {target}")
        
        # Generate unique scan ID
        scan_id = str(uuid.uuid4())
        
        # Log scan initiation
        scan_doc = {
            'scan_id': scan_id,
            'target': target,
            'scan_type': scan_type,
            'status': 'initiated',
            'timestamp': firestore.SERVER_TIMESTAMP,
            'agent': 'recon'
        }
        db.collection('scans').document(scan_id).set(scan_doc)
        
        # Perform Nmap scan
        nm = nmap.PortScanner()
        if scan_type == 'basic':
            scan_args = '-sV -sC -O --top-ports 1000'
        elif scan_type == 'comprehensive':
            scan_args = '-sV -sC -O -A --script vuln'
        else:
            scan_args = '-sV --top-ports 100'
        
        logger.info(f"Running nmap scan with args: {scan_args}")
        scan_result = nm.scan(target, arguments=scan_args)
        
        # Process results and extract hypotheses
        hypotheses = []
        for host in nm.all_hosts():
            host_info = {
                'host': host,
                'state': nm[host].state(),
                'protocols': list(nm[host].all_protocols())
            }
            
            for proto in nm[host].all_protocols():
                ports = nm[host][proto].keys()
                for port in ports:
                    port_info = nm[host][proto][port]
                    if port_info['state'] == 'open':
                        hypothesis = {
                            'scan_id': scan_id,
                            'target': host,
                            'port': port,
                            'protocol': proto,
                            'service': port_info.get('name', 'unknown'),
                            'version': port_info.get('version', ''),
                            'product': port_info.get('product', ''),
                            'extrainfo': port_info.get('extrainfo', ''),
                            'confidence': port_info.get('conf', ''),
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        hypotheses.append(hypothesis)
        
        # Upload full scan results to Storage
        scan_filename = f"recon/{scan_id}/{target}_scan.xml"
        blob = bucket.blob(scan_filename)
        blob.upload_from_string(nm.get_nmap_last_output())
        
        # Update scan document
        db.collection('scans').document(scan_id).update({
            'status': 'completed',
            'hypotheses_count': len(hypotheses),
            'artifact_path': scan_filename,
            'completion_timestamp': firestore.SERVER_TIMESTAMP
        })
        
        # Publish hypotheses to Pub/Sub
        for hypothesis in hypotheses:
            message_data = json.dumps(hypothesis).encode('utf-8')
            future = publisher.publish(recon_topic, message_data)
            logger.info(f"Published hypothesis for {hypothesis['target']}:{hypothesis['port']}")
        
        logger.info(f"Recon scan completed. Generated {len(hypotheses)} hypotheses")
        
        return jsonify({
            'scan_id': scan_id,
            'target': target,
            'hypotheses_generated': len(hypotheses),
            'status': "completed"
        }), 200
        
    except Exception as e:
        # 🛡️ Sentinel: Generic error message to prevent info leakage
        logger.error(f"Error in recon scan: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal error occurred while processing the scan."}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
