"""The rig reads its state folder at import, so every test module shares
one scratch folder, set here before any module imports the rig."""
import os
import tempfile

os.environ["MODEL_RIG_HOME"] = tempfile.mkdtemp(prefix="model-rig-state-")
