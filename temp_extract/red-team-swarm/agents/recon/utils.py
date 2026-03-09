"""
Utility functions for the Recon Agent
"""
import socket
import dns.resolver
import logging

logger = logging.getLogger(__name__)


def resolve_dns(target):
    """Resolve DNS name to IP address"""
    try:
        result = socket.gethostbyname(target)
        logger.info(f"Resolved {target} to {result}")
        return result
    except socket.gaierror as e:
        logger.error(f"Failed to resolve {target}: {e}")
        return None


def get_dns_records(domain, record_type='A'):
    """Get DNS records for a domain"""
    try:
        answers = dns.resolver.resolve(domain, record_type)
        records = [str(rdata) for rdata in answers]
        logger.info(f"Found {len(records)} {record_type} records for {domain}")
        return records
    except Exception as e:
        logger.error(f"Failed to get {record_type} records for {domain}: {e}")
        return []


def is_valid_target(target):
    """Validate if target is a valid IP or domain"""
    # Check if it's a valid IP
    try:
        socket.inet_aton(target)
        return True
    except socket.error:
        pass

    # Check if it's a valid domain
    if '.' in target and len(target) > 3:
        return True

    return False


def sanitize_target(target):
    """Sanitize target input to prevent injection"""
    # Remove any potentially dangerous characters
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-:/')
    sanitized = ''.join(c for c in target if c in allowed_chars)
    return sanitized


def parse_nmap_output(xml_output):
    """Parse Nmap XML output and extract relevant information"""
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(xml_output)
        hosts = []

        for host in root.findall('host'):
            host_info = {
                'address': host.find('address').get('addr') if host.find('address') is not None else None,
                'status': host.find('status').get('state') if host.find('status') is not None else 'unknown',
                'ports': []
            }

            ports = host.find('ports')
            if ports is not None:
                for port in ports.findall('port'):
                    port_info = {
                        'port': port.get('portid'),
                        'protocol': port.get('protocol'),
                        'state': port.find('state').get('state') if port.find('state') is not None else 'unknown',
                        'service': port.find('service').get('name') if port.find('service') is not None else 'unknown'
                    }
                    host_info['ports'].append(port_info)

            hosts.append(host_info)

        return hosts
    except ET.ParseError as e:
        logger.error(f"Failed to parse Nmap XML: {e}")
        return []
