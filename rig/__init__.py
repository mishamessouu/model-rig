"""model-rig: run coding agents on planted-defect scenarios and score them."""
import os
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent


def _root():
    """The checkout that holds `scenarios/`, `config/`, and `results/`.

    MODEL_RIG_ROOT wins. An editable install finds the checkout next to
    the package. A plain install (for example `uv tool install .`) has no
    checkout next to it, so it uses the current folder.
    """
    if os.environ.get("MODEL_RIG_ROOT"):
        return Path(os.environ["MODEL_RIG_ROOT"]).resolve()
    if (PACKAGE.parent / "scenarios").is_dir():
        return PACKAGE.parent
    return Path.cwd()


ROOT = _root()
# Machine state outside the repo: sign-in folders and run work folders.
STATE = Path(os.environ.get("MODEL_RIG_HOME", Path.home() / ".model-rig"))
