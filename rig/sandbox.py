"""Wrap a command in bubblewrap.

The root file system is read-only. Home, /data, /tmp, /run, and /var are
replaced by empty folders, so an agent cannot read the rig repo, the hidden
tests, the person's files, or a Docker or LXD socket. The rig repo and its
state folder are emptied too, wherever they are, for a checkout under /root
or /opt. Only the paths a run names come back.

The sandbox always has its own network namespace, with loopback only. A
run that names a proxy socket (rig/proxy.py) gets it bound in, and the
command starts behind rig/netbridge.py, which listens on 127.0.0.1:3128
and forwards to that socket. The proxy variables point there. Without a
proxy there is no network at all, and no name resolution.
"""
import hashlib
import shutil
from pathlib import Path

from . import ROOT, STATE

EMPTIED = ("/home", "/data", "/tmp", "/run", "/var", "/mnt", "/media", "/srv", "/snap")
PATH = "/usr/local/bin:/usr/bin:/bin"
BRIDGE = Path(__file__).with_name("netbridge.py")
# Fixed paths inside the sandbox, so no host path shows in the agent's env.
INSIDE_BRIDGE = "/run/rig/netbridge.py"
INSIDE_SOCKET = "/run/rig/proxy.sock"
SYSTEM_PYTHON = "/usr/bin/python3"
PROXY_URL = "http://127.0.0.1:3128"
PROXY_ENV = {
    **{name: PROXY_URL for name in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY",
                                    "https_proxy", "http_proxy", "all_proxy")},
    "NO_PROXY": "localhost,127.0.0.1", "no_proxy": "localhost,127.0.0.1",
}


def opaque(text):
    """A folder name that tells an agent nothing. Agents read the work
    folder's name as a hint when it named the scenario."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def hidden():
    """The folders the sandbox empties: the fixed list, then the rig repo
    and its state folder when no folder on that list holds them."""
    out = [Path(path) for path in EMPTIED]
    for path in (ROOT, STATE):
        path = Path(path)
        if (path != Path("/") and path.exists()
                and not any(path.is_relative_to(folder) for folder in out)):
            out.append(path)
    return out


def command(argv, *, cwd, read=(), write=(), env=None, proxy=None):
    """Return the bwrap argv. `write` binds in order, so a later bind may
    sit inside an earlier one. `proxy` is the host path of a running
    proxy's socket, or None for no network."""
    bwrap = shutil.which("bwrap")
    if bwrap is None:
        raise RuntimeError("bubblewrap (bwrap) is not installed")
    out = [bwrap, "--ro-bind", "/", "/"]
    for path in hidden():
        if path.exists():
            out += ["--tmpfs", str(path)]
    out += ["--dev", "/dev", "--proc", "/proc"]
    for path in read:
        out += ["--ro-bind", str(path), str(path)]
    for path in write:
        out += ["--bind", str(path), str(path)]
    environment = {"PATH": PATH, "LANG": "C.UTF-8"}
    environment.update(env or {})
    if proxy:
        out += ["--ro-bind", str(BRIDGE), INSIDE_BRIDGE,
                "--bind", str(proxy), INSIDE_SOCKET]
        environment.update(PROXY_ENV)
        argv = [SYSTEM_PYTHON, "-I", INSIDE_BRIDGE, INSIDE_SOCKET, "--", *argv]
    out += ["--unshare-net", "--unshare-pid", "--unshare-ipc", "--unshare-uts",
            "--die-with-parent", "--new-session", "--clearenv"]
    for key, value in environment.items():
        out += ["--setenv", key, str(value)]
    out += ["--chdir", str(cwd), "--", *map(str, argv)]
    return out
