"""Network operations. No GUI dependency; TCP lab binds only to loopback."""
import ipaddress
import json
import socket
import ssl
import threading
import time
import urllib.request


def inspect_ip(value):
    ip = ipaddress.ip_address(value.strip())
    if ip.is_loopback:
        kind = 'Loopback'
    elif ip.is_multicast:
        kind = 'Multicast'
    elif ip.is_link_local:
        kind = 'Link-local'
    elif ip.is_unspecified:
        kind = 'Unspecified'
    elif ip.is_reserved:
        kind = 'Reserved'
    elif ip.is_private:
        kind = 'Private / special use'
    elif ip.is_global:
        kind = 'Public (global)'
    else:
        kind = 'Non-global / special use'
    return {'IP address': str(ip), 'Version': f'IPv{ip.version}',
            'Classification': kind, 'Global': str(ip.is_global),
            'Loopback': str(ip.is_loopback), 'Private flag': str(ip.is_private)}


def resolve_dns(host):
    host = host.strip()
    if not host or len(host) > 253 or any(c.isspace() for c in host) or '/' in host:
        raise ValueError('Enter a hostname, not a URL.')
    addresses = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    return {'Hostname': host, 'Addresses': '\n'.join(sorted({a[4][0] for a in addresses}))}


def local_identity():
    host = socket.gethostname()
    try:
        addresses = resolve_dns(host)['Addresses']
    except OSError:
        addresses = 'Hostname could not be resolved on this system'
    return {'Hostname': host, 'Resolved local addresses': addresses}


def public_metadata(value):
    ip = ipaddress.ip_address(value.strip())
    if not ip.is_global or ip.is_multicast or ip.is_reserved:
        raise ValueError('Online lookup requires a public unicast IP.')
    url = f'https://ipapi.co/{ip}/json/'
    request = urllib.request.Request(url, headers={'User-Agent': 'NetScope-Lab/2.0'})
    with urllib.request.urlopen(request, timeout=10, context=ssl.create_default_context()) as reply:
        data = json.loads(reply.read(65536))
    if data.get('error'):
        raise ValueError(str(data.get('reason') or 'Provider returned an error'))
    return {'IP address': str(ip), 'Country (approx.)': data.get('country_name') or 'N/A',
            'Region (approx.)': data.get('region') or 'N/A', 'Network / ISP': data.get('org') or 'N/A',
            'ASN': data.get('asn') or 'N/A', 'Timezone (approx.)': data.get('timezone') or 'N/A',
            'Source': 'ipapi.co / HTTPS', 'Note': 'Network estimates, not a person’s physical location.'}


def parse_port(value):
    port = int(value)
    if not 1 <= port <= 65535:
        raise ValueError('Port must be 1–65535.')
    return port


def check_local_ports(start, end):
    start, end = parse_port(start), parse_port(end)
    if end < start or end - start >= 32:
        raise ValueError('Choose an ascending range of at most 32 ports.')
    results = {'Target': '127.0.0.1'}
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            code = sock.connect_ex(('127.0.0.1', port))
        results[str(port)] = 'OPEN' if code == 0 else f'Not connected (code {code})'
    return results


class EchoServer:
    def __init__(self):
        self.listener = None
        self.thread = None
        self.stop_event = threading.Event()
        self.port = None

    def start(self, port):
        if self.listener is not None:
            raise ValueError('Stop the running server first.')
        port = parse_port(port)
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.bind(('127.0.0.1', port))
            listener.listen(5)
            listener.settimeout(0.2)
        except Exception:
            listener.close()
            raise
        self.stop_event.clear()
        self.listener, self.port = listener, port
        self.thread = threading.Thread(target=self._serve, args=(listener,), daemon=True)
        self.thread.start()
        return {'Server': 'Started', 'Address': f'127.0.0.1:{port}'}

    def _serve(self, listener):
        while not self.stop_event.is_set():
            try:
                conn, _ = listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with conn:
                conn.settimeout(0.3)
                while not self.stop_event.is_set():
                    try:
                        data = conn.recv(1024)
                        if not data:
                            break
                        conn.sendall(data)
                    except socket.timeout:
                        continue
                    except OSError:
                        break

    def stop(self):
        self.stop_event.set()
        if self.listener is not None:
            self.listener.close()
            self.thread.join(timeout=1)
            self.listener = None
            self.port = None
        return {'Server': 'Stopped'}


def echo_test(port, message):
    port = parse_port(port)
    payload = message.encode('utf-8')
    if not 1 <= len(payload) <= 4096:
        raise ValueError('Enter a message of 1–4096 bytes.')
    start = time.perf_counter()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(2)
        client.connect(('127.0.0.1', port))
        client.sendall(payload)
        chunks = bytearray()
        while len(chunks) < len(payload):
            data = client.recv(len(payload) - len(chunks))
            if not data:
                break
            chunks.extend(data)
    elapsed = (time.perf_counter() - start) * 1000
    return {'Protocol': 'TCP', 'Target': f'127.0.0.1:{port}', 'Sent': message,
            'Received': chunks.decode('utf-8', errors='replace'),
            'Match': str(bytes(chunks) == payload), 'Elapsed (connect + echo)': f'{elapsed:.2f} ms'}
