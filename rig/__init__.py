"""model-rig: run coding agents on planted-defect scenarios and score them."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Machine state outside the repo: sign-in folders and run work folders.
STATE = Path(os.environ.get("MODEL_RIG_HOME", Path.home() / ".model-rig"))
