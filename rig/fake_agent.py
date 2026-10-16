"""A stand-in agent for the rig's own tests. No model call.

    fake_agent.py none                 change nothing
    fake_agent.py probe                report what the sandbox lets it see
    fake_agent.py <defect> <solution>  copy a reference fix into the repo
"""
import json
import shutil
import sys
from pathlib import Path

mode = sys.argv[1]
final = f"CHOICE: fake {mode}"
if mode == "probe":
    seen = [path for path in sys.argv[2:] if Path(path).exists()]
    final = "PROBE " + json.dumps(seen)
elif len(sys.argv) > 2:
    source = Path(sys.argv[2])
    for path in source.rglob("*"):
        if path.is_file():
            target = Path.cwd() / path.relative_to(source)
            shutil.copy2(path, target)
print(json.dumps({
    "type": "result", "is_error": False, "num_turns": 1, "result": final,
    "total_cost_usd": 0.01,
    "modelUsage": {"claude-opus-5-5": {
        "inputTokens": 1000, "outputTokens": 2000,
        "cacheReadInputTokens": 100000, "cacheCreationInputTokens": 10000}},
}))
