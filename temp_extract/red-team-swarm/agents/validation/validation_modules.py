"""
Validation modules for different service types
"""
import requests
import socket
import ftplib
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class WebValidator:
    """Validator for HTTP/HTTPS services"""

    COMMON_PATHS = [
        '/admin', '/login', '/wp-admin', '/phpmyadmin',
        '/api', '/swagger', '/.env', '/config',
        '/robots.txt', '/sitemap.xml', '/.git'
    ]

    @staticmethod
    def check_headers(response):
        """Check for security headers"""
        security_headers = {
            'X-Frame-Options': 'missing',
            'X-Content-Type-Options': 'missing',
            'X-XSS-Protection': 'missing',
            'Content-Security-Policy': 'missing',
            'Strict-Transport-Security': 'missing'
        }

        for header in security_headers:
            if header in response.headers:
                security_headers[header] = 'present'

        return security_headers

    @staticmethod
    def check_common_paths(base_url):
        """Check for common sensitive paths"""
        found_paths = []

        for path in WebValidator.COMMON_PATHS:
            try:
                url = f"{base_url}{path}"
                response = requests.get(url, timeout=5, verify=False)
                if response.status_code in [200, 401, 403]:
                    found_paths.append({
                        'path': path,
                        'status': response.status_code
                    })
            except:
                pass

        return found_paths

    @staticmethod
    def detect_wappalyzer(response):
        """Basic technology detection from response"""
        technologies = []

        # Server header
        if 'Server' in response.headers:
            technologies.append(response.headers['Server'])

        # X-Powered-By header
        if 'X-Powered-By' in response.headers:
            technologies.append(response.headers['X-Powered-By'])

        # Common framework indicators
        indicators = {
            'WordPress': 'wp-content',
            'Drupal': 'drupal',
            'Joomla': 'joomla',
            'React': 'react',
            'Angular': 'ng-',
            'Vue.js': 'vue'
        }

        for tech, indicator in indicators.items():
            if indicator in response.text.lower():
                technologies.append(tech)

        return list(set(technologies))


class SSHValidator:
    """Validator for SSH services"""

    @staticmethod
    def check_banner_grabbing(target, port=22):
        """Perform SSH banner grabbing"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((target, port))
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            sock.close()
            return banner
        except Exception as e:
            logger.error(f"Banner grabbing failed: {e}")
            return None

    @staticmethod
    def check_weak_algorithms(target, port=22):
        """Check for weak SSH algorithms"""
        weak_algos = {
            'kex_algorithms': ['diffie-hellman-group1-sha1', 'diffie-hellman-group14-sha1'],
            'cipher_algorithms': ['3des-cbc', 'blowfish-cbc', 'arcfour'],
            'mac_algorithms': ['hmac-md5', 'hmac-sha1-96']
        }

        # This would require paramiko or similar library for full implementation
        return weak_algos


class FTPValidator:
    """Validator for FTP services"""

    @staticmethod
    def check_anonymous_login(target, port=21):
        """Check for anonymous FTP login"""
        try:
            ftp = ftplib.FTP()
            ftp.connect(target, port, timeout=10)
            ftp.login('anonymous', 'anonymous@example.com')

            # Try to list directory
            files = []
            ftp.retrlines('LIST', files.append)

            ftp.quit()
            return {
                'anonymous_access': True,
                'files_accessible': len(files) > 0,
                'file_count': len(files)
            }
        except ftplib.error_perm:
            return {'anonymous_access': False}
        except Exception as e:
            logger.error(f"FTP check failed: {e}")
            return {'anonymous_access': False, 'error': str(e)}

    @staticmethod
    def check_write_access(target, port=21):
        """Check for anonymous write access"""
        try:
            ftp = ftplib.FTP()
            ftp.connect(target, port, timeout=10)
            ftp.login('anonymous', 'anonymous@example.com')

            # Try to create a test directory
            test_dir = 'test_write_access'
            try:
                ftp.mkd(test_dir)
                ftp.rmd(test_dir)
                return {'write_access': True}
            except ftplib.error_perm:
                return {'write_access': False}
        except Exception as e:
            return {'write_access': False, 'error': str(e)}


class SMBValidator:
    """Validator for SMB services"""

    @staticmethod
    def check_null_session(target, port=445):
        """Check for SMB null session"""
        # This would require impacket or similar library
        # Placeholder for implementation
        return {
            'null_session_possible': False,
            'note': 'Requires impacket library for full implementation'
        }

    @staticmethod
    def enumerate_shares(target):
        """Enumerate SMB shares"""
        # Placeholder for implementation
        return []


class DatabaseValidator:
    """Validator for database services"""

    COMMON_CREDENTIALS = [
        ('root', ''),
        ('root', 'root'),
        ('admin', 'admin'),
        ('sa', ''),
        ('postgres', 'postgres')
    ]

    @staticmethod
    def check_default_credentials(target, port, service):
        """Check for default database credentials"""
        # Placeholder - would require specific database drivers
        return {
            'default_creds_work': False,
            'note': 'Requires database-specific drivers for full implementation'
        }


def get_validator(service_type):
    """Factory function to get appropriate validator"""
    validators = {
        'http': WebValidator,
        'https': WebValidator,
        'ssh': SSHValidator,
        'ftp': FTPValidator,
        'smb': SMBValidator,
        'microsoft-ds': SMBValidator
    }

    return validators.get(service_type.lower(), None)
