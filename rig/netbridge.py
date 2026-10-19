"""The sandbox side of the network: a TCP-to-Unix bridge before the agent.

    /usr/bin/python3 -I netbridge.py SOCKET -- AGENT ARGV...

The sandbox has its own network namespace with loopback only. This
listens on 127.0.0.1:3128, where the agent's HTTPS_PROXY points, and
copies each connection to SOCKET, the rig's proxy socket bound in from
the host. Then it starts the agent as its child, passes SIGTERM, SIGINT,
and SIGHUP on, and exits with the agent's exit code.

It runs on the system Python in isolated mode and imports nothing from
the rig, because the sandbox hides the rig package and a venv may sit
first on PATH.
"""
import contextlib
import select
import signal
import socket
import subprocess
import sys
import threading

ADDRESS = ("127.0.0.1", 3128)


def _pump(one, two):
    """Copy bytes both ways until both sides close."""
    other = {one: two, two: one}
    open_ = [one, two]
    while open_:
        readable, _, _ = select.select(open_, [], [])
        for side in readable:
            data = side.recv(65536)
            if data:
                other[side].sendall(data)
                continue
            open_.remove(side)
            with contextlib.suppress(OSError):
                other[side].shutdown(socket.SHUT_WR)


def _bridge(client, path):
    with client, socket.socket(socket.AF_UNIX) as upstream, \
            contextlib.suppress(OSError):
        upstream.connect(path)
        _pump(client, upstream)


def _serve(listener, path):
    while True:
        client, _ = listener.accept()
        threading.Thread(target=_bridge, args=(client, path), daemon=True).start()


def main(argv):
    if len(argv) < 4 or argv[2] != "--":
        sys.exit("usage: netbridge.py SOCKET -- AGENT ARGV...")
    path, command = argv[1], argv[3:]
    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(ADDRESS)
    listener.listen(64)
    threading.Thread(target=_serve, args=(listener, path), daemon=True).start()
    child = subprocess.Popen(command)
    for number in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(number, lambda received, _: child.send_signal(received))
    code = child.wait()
    # A child ended by a signal gets the shell's code for it.
    return code if code >= 0 else 128 - code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
