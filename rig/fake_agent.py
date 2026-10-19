"""A stand-in agent for the rig's own tests. No model call.

    fake_agent.py none                 change nothing
    fake_agent.py probe                report what the sandbox lets it see
    fake_agent.py netprobe [host:port ...]
                                       report what the network lets it reach
    fake_agent.py <defect> <solution>  copy a reference fix into the repo
    ... --commit                       then commit it, as some agents do
"""
import errno
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path


def _error(error):
    return errno.errorcode.get(error.errno, str(error)) if error.errno else str(error)


def _connect_via(proxy, target):
    """CONNECT through the proxy. Return the reply status and the socket."""
    address = urllib.parse.urlsplit(proxy)
    client = socket.create_connection((address.hostname, address.port), timeout=5)
    client.sendall(f"CONNECT {target} HTTP/1.1\r\nHost: {target}\r\n\r\n".encode())
    head = b""
    while b"\r\n\r\n" not in head:
        chunk = client.recv(1)
        if not chunk:
            break
        head += chunk
    return int(head.split()[1]) if head else 0, client


def netprobe(targets):
    seen = {}
    started = time.time()
    try:
        socket.create_connection(("1.1.1.1", 443), timeout=5).close()
        seen["direct"] = "open"
    except OSError as error:
        seen["direct"] = _error(error)
    seen["direct_seconds"] = round(time.time() - started, 3)
    try:
        socket.getaddrinfo("example.com", 443)
        seen["dns"] = "resolves"
    except OSError:
        seen["dns"] = "fails"
    seen["proxy"] = os.environ.get("HTTPS_PROXY")
    if not seen["proxy"]:
        # Nothing may listen where the bridge would.
        try:
            socket.create_connection(("127.0.0.1", 3128), timeout=5).close()
            seen["bridge"] = "open"
        except OSError as error:
            seen["bridge"] = _error(error)
        return seen
    seen["allowed"] = {}
    for target in targets:
        status, client = _connect_via(seen["proxy"], target)
        with client:
            if status == 200:
                client.sendall(b"ping")
                status = "echo" if client.recv(4) == b"ping" else status
        seen["allowed"][target] = status
    status, client = _connect_via(seen["proxy"], "denied.example.invalid:443")
    client.close()
    seen["denied"] = status
    return seen


mode = sys.argv[1]
final = f"CHOICE: fake {mode}"
if mode == "probe":
    seen = [path for path in sys.argv[2:] if Path(path).exists()]
    final = "PROBE " + json.dumps(seen)
elif mode == "netprobe":
    final = "NETPROBE " + json.dumps(netprobe(sys.argv[2:]))
elif len(sys.argv) > 2:
    source = Path(sys.argv[2])
    for path in source.rglob("*"):
        if path.is_file():
            target = Path.cwd() / path.relative_to(source)
            shutil.copy2(path, target)
    if "--commit" in sys.argv:
        subprocess.run(["git", "-c", "user.name=fake", "-c", "user.email=fake@example.invalid",
                        "commit", "-qam", "fake fix"], check=True)
print(json.dumps({
    "type": "result", "is_error": False, "num_turns": 1, "result": final,
    "total_cost_usd": 0.01,
    "modelUsage": {"claude-opus-5-5": {
        "inputTokens": 1000, "outputTokens": 2000,
        "cacheReadInputTokens": 100000, "cacheCreationInputTokens": 10000}},
}))
