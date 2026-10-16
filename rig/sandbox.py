"""Wrap a command in bubblewrap.

The root file system is read-only. Home, /data, /tmp, /run, and /var are
replaced by empty folders, so an agent cannot read the rig repo, the hidden
tests, the person's files, or a Docker or LXD socket. Only the paths a run
names come back.
"""
import shutil
from pathlib import Path

EMPTIED = ("/home", "/data", "/tmp", "/run", "/var", "/mnt", "/media", "/srv", "/snap")
RESOLVER = Path("/run/systemd/resolve")
PATH = "/usr/local/bin:/usr/bin:/bin"


def command(argv, *, cwd, read=(), write=(), env=None, network=False):
    """Return the bwrap argv. `write` binds in order, so a later bind may
    sit inside an earlier one."""
    bwrap = shutil.which("bwrap")
    if bwrap is None:
        raise RuntimeError("bubblewrap (bwrap) is not installed")
    out = [bwrap, "--ro-bind", "/", "/"]
    for path in EMPTIED:
        if Path(path).exists():
            out += ["--tmpfs", path]
    out += ["--dev", "/dev", "--proc", "/proc"]
    if network and RESOLVER.is_dir():
        out += ["--ro-bind", str(RESOLVER), str(RESOLVER)]
    for path in read:
        out += ["--ro-bind", str(path), str(path)]
    for path in write:
        out += ["--bind", str(path), str(path)]
    out += ["--unshare-pid", "--unshare-ipc", "--unshare-uts",
            "--die-with-parent", "--new-session", "--clearenv"]
    if not network:
        out.append("--unshare-net")
    environment = {"PATH": PATH, "LANG": "C.UTF-8"}
    environment.update(env or {})
    for key, value in environment.items():
        out += ["--setenv", key, str(value)]
    out += ["--chdir", str(cwd), "--", *map(str, argv)]
    return out
