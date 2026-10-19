"""A host-side HTTP CONNECT proxy with a host allowlist.

The agent sandbox has no network of its own (bwrap --unshare-net). Its one
way out is a Unix socket that the runner binds in, and this proxy listens
on that socket on the host. It resolves names on the host, so the sandbox
needs no resolver.

The rule: an allowlist entry is `host` or `host:port`. A bare host allows
port 443 only. An entry that starts with "*." allows every subdomain of
the rest, but not the rest itself: "*.example.com" allows a.example.com,
not example.com. Names compare in lower case, without a trailing dot. An
IPv6 literal needs brackets: "[::1]:8080".

Only `CONNECT host:port` that matches the list opens a tunnel. Everything
else gets 403, and the connection closes. Each request writes one JSON
line to the log: time, host, port, allowed.
"""
import contextlib
import datetime
import json
import select
import shutil
import socket
import socketserver
import tempfile
import threading
import urllib.parse
from pathlib import Path

HEAD_LIMIT = 8192
CONNECT_TIMEOUT = 15
FORBIDDEN = b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
BAD_GATEWAY = b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
ESTABLISHED = b"HTTP/1.1 200 Connection Established\r\n\r\n"


def _name(host):
    return host.strip().strip("[]").rstrip(".").lower()


def _entry(entry):
    """Split an allowlist entry into a name and a port."""
    host, colon, port = entry.rpartition(":")
    if colon and port.isdigit() and (host.endswith("]") or ":" not in host):
        return _name(host), int(port)
    return _name(entry), 443


def allowed(host, port, hosts):
    """True when `host:port` matches an entry of `hosts` (see the rule above)."""
    host = _name(host)
    for entry in hosts:
        name, want = _entry(entry)
        if port != want:
            continue
        if name.startswith("*.") and host.endswith(name[1:]):
            return True
        if host == name:
            return True
    return False


def _target(line):
    """Return (method, host, port) of a request line. Port 0 means unreadable."""
    parts = line.split()
    if len(parts) != 3:
        return "", line[:100], 0
    method, target = parts[0].upper(), parts[1]
    if method == "CONNECT":
        host, colon, port = target.rpartition(":")
        if not colon or not port.isdigit():
            return method, target[:255], 0
        return method, _name(host), int(port)
    # A proxied plain request names a URL. Log its host, then refuse it.
    url = urllib.parse.urlsplit(target)
    try:
        port = url.port or (443 if url.scheme == "https" else 80)
    except ValueError:
        port = 0
    return method, _name(url.hostname or target[:255]), port


def _pump(one, two, stopping):
    """Copy bytes both ways until both sides close or the proxy stops."""
    other = {one: two, two: one}
    open_ = [one, two]
    while open_ and not stopping.is_set():
        readable, _, _ = select.select(open_, [], [], 0.5)
        for side in readable:
            data = side.recv(65536)
            if data:
                other[side].sendall(data)
                continue
            # One side finished sending: pass the end on, keep the other way.
            open_.remove(side)
            with contextlib.suppress(OSError):
                other[side].shutdown(socket.SHUT_WR)


class _Handler(socketserver.BaseRequestHandler):
    def handle(self):
        gate, client = self.server.gate, self.request
        client.settimeout(30)
        head = b""
        with contextlib.suppress(OSError):
            while b"\r\n\r\n" not in head and len(head) < HEAD_LIMIT:
                chunk = client.recv(4096)
                if not chunk:
                    break
                head += chunk
        if not head:
            return
        head, _, rest = head.partition(b"\r\n\r\n")
        method, host, port = _target(head.split(b"\r\n", 1)[0].decode("latin-1"))
        ok = method == "CONNECT" and bool(port) and allowed(host, port, gate.hosts)
        record = {"host": host, "port": port, "allowed": ok}
        if not ok:
            gate.log(record)
            with contextlib.suppress(OSError):
                client.sendall(FORBIDDEN)
            return
        try:
            upstream = socket.create_connection((host, port), timeout=CONNECT_TIMEOUT)
        except OSError as error:
            gate.log({**record, "error": str(error)[:200]})
            with contextlib.suppress(OSError):
                client.sendall(BAD_GATEWAY)
            return
        gate.log(record)
        with upstream, contextlib.suppress(OSError):
            client.settimeout(None)
            upstream.settimeout(None)
            client.sendall(ESTABLISHED)
            if rest:
                upstream.sendall(rest)
            _pump(client, upstream, gate.stopping)


class _Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


class Proxy:
    """One proxy for one run. `socket` is the path to bind into the sandbox."""

    def __init__(self, hosts, log_path):
        self.hosts = list(hosts)
        self.log_path = Path(log_path)
        self.stopping = threading.Event()
        self._lock = threading.Lock()
        # A socket path has a 108-byte limit, and a run folder can be deeper,
        # so the socket lives in a short private folder (mode 0700).
        self._folder = Path(tempfile.mkdtemp(prefix="rig-net-"))
        self.socket = self._folder / "proxy.sock"
        self._server = None

    def log(self, record):
        stamp = datetime.datetime.now(datetime.UTC).isoformat(timespec="milliseconds")
        line = json.dumps({"time": stamp, **record})
        with self._lock, self.log_path.open("a") as out:
            out.write(line + "\n")

    def start(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.touch()
        self._server = _Server(str(self.socket), _Handler)
        self._server.gate = self
        threading.Thread(target=self._server.serve_forever, daemon=True,
                         name="rig-proxy").start()
        return self

    def stop(self):
        self.stopping.set()
        if self._server:
            self._server.shutdown()
            self._server.server_close()
        shutil.rmtree(self._folder, ignore_errors=True)


@contextlib.contextmanager
def serve(hosts, log_path):
    """Run a proxy for the length of a `with` block. It stops on any exit."""
    gate = Proxy(hosts, log_path)
    try:
        yield gate.start()
    finally:
        gate.stop()


def summary(log_path):
    """The hosts a run reached and the hosts it was refused, sorted, unique."""
    allowed_hosts, denied = set(), set()
    path = Path(log_path)
    if path.exists():
        for line in path.read_text().splitlines():
            record = json.loads(line)
            (allowed_hosts if record["allowed"] else denied).add(record["host"])
    return {"allowed": sorted(allowed_hosts), "denied": sorted(denied)}
