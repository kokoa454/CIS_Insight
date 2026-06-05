import urllib.parse
import socket
import ipaddress
import logging

logger = logging.getLogger(__name__)


def is_safe_url(url):
    try:
        parsed_url = urllib.parse.urlparse(url)
        host = parsed_url.hostname
        if not host:
            return False

        ip_addresses = socket.getaddrinfo(host, None)
        
        for item in ip_addresses:
            ip_str = item[4][0]
            ip = ipaddress.ip_address(ip_str)

            if (ip.is_private or          # 10.x.x.x, 172.16.x.x, 192.168.x.x
                ip.is_loopback or         # 127.0.0.1 (self)
                ip.is_link_local or       # 169.254.x.x (metadata server)
                ip.is_unspecified or      # 0.0.0.0
                ip.is_multicast):         # multicast
                
                logger.warning(f"SSRF prevention triggered: Blocked URL pointing to internal IP {ip_str} ({url})")
                return False

        return True
    except Exception as e:
        logger.error(f"URL safety check failed for {url}: {e}")
        return False