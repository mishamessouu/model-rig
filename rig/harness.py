"""How to start each agent CLI headless, and how to read its token use.

A harness returns an Invocation. The runner wraps it in the sandbox. Each
harness normalises usage to four kinds of tokens per model:
input (not cached), output, cache_read, cache_write.
"""
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from . import PACKAGE, ROOT, STATE


@dataclass
class Invocation:
    argv: list
    env: dict
    read: list = field(default_factory=list)
    # (master file, run file) pairs: copied in before the run, and copied
    # back after it when the agent refreshed its sign-in.
    auth: list = field(default_factory=list)
    # Hosts the agent may reach through the rig's proxy (rig/proxy.py).
    # Empty means no network at all. They come from config/network.toml.
    hosts: list = field(default_factory=list)
    final_file: Path | None = None


def _real(name):
    found = shutil.which(name)
    if found is None:
        raise RuntimeError(f"{name} is not installed")
    return Path(found).resolve()


# --- Claude Code -------------------------------------------------------------

CLAUDE_FOLDER = STATE / "claude-config"

# Scaffolding for Claude Code 2.1.280 in headless mode. A model that starts
# a background helper and then waits for its notification ends the run with
# no change, because no notification arrives in `-p` mode (batch
# 20261016T203032Z, Sonnet). So runs are one agent, like Codex exec, with no
# scheduling tools and no web lookup of the defect. Revisit when the CLI
# waits for background work before it exits.
CLAUDE_DENIED = ("Agent", "Task", "ScheduleWakeup", "Monitor", "CronCreate",
                 "CronDelete", "CronList", "RemoteTrigger", "PushNotification",
                 "SendMessage", "ListAgents", "TaskStop", "Workflow",
                 "AskUserQuestion", "WebSearch", "WebFetch", "EnterWorktree",
                 "ExitWorktree")


def claude(cell, prompt, run_dir, budget_usd):
    config = run_dir / "claude-config"
    config.mkdir()
    account = CLAUDE_FOLDER / ".claude.json"
    if account.exists():
        shutil.copy2(account, config / ".claude.json")
    argv = [_real("claude"), "-p", prompt, "--output-format", "stream-json",
            "--verbose",
            "--model", cell["model"], "--permission-mode", "bypassPermissions",
            "--no-session-persistence", "--strict-mcp-config",
            "--max-budget-usd", str(budget_usd),
            "--disallowedTools", ",".join(CLAUDE_DENIED)]
    if cell.get("effort"):
        argv += ["--effort", cell["effort"]]
    env = {
        "HOME": run_dir / "home",
        "CLAUDE_CONFIG_DIR": config,
        "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
        "ENABLE_CLAUDEAI_MCP_SERVERS": "false",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "DISABLE_TELEMETRY": "1",
        "DISABLE_AUTOUPDATER": "1",
    }
    return Invocation(
        argv=argv, env=env, read=[argv[0]],
        auth=[(CLAUDE_FOLDER / ".credentials.json", config / ".credentials.json")],
        hosts=list(cell.get("hosts", [])),
    )


def parse_claude(stdout, final_file=None):
    """Read the last `result` event of a stream-json log."""
    results = [line for line in stdout.splitlines() if '"type":"result"' in
               line.replace(" ", "")]
    if not results:
        raise ValueError("no result event in the agent output")
    data = json.loads(results[-1])
    by_model = {}
    for model, use in (data.get("modelUsage") or {}).items():
        by_model[model] = {
            "input": use.get("inputTokens", 0),
            "output": use.get("outputTokens", 0),
            "cache_read": use.get("cacheReadInputTokens", 0),
            "cache_write": use.get("cacheCreationInputTokens", 0),
        }
    if not by_model and data.get("usage"):
        use = data["usage"]
        by_model["unknown"] = {
            "input": use.get("input_tokens", 0),
            "output": use.get("output_tokens", 0),
            "cache_read": use.get("cache_read_input_tokens", 0),
            "cache_write": use.get("cache_creation_input_tokens", 0),
        }
    return {
        "by_model": by_model,
        "usd_reported": data.get("total_cost_usd"),
        "turns": data.get("num_turns"),
        # `subtype` can say "success" on a failed run, so name the reason.
        "error": (f"{data.get('terminal_reason') or data.get('subtype')}: "
                  f"{(data.get('result') or '')[:200]}") if data.get("is_error") else None,
        "raw_usage": data.get("usage"),
        "final": data.get("result") or "",
    }


# --- Codex -------------------------------------------------------------------

CODEX_FOLDER = STATE / "codex-home"


def codex(cell, prompt, run_dir, budget_usd):
    home = run_dir / "codex-home"
    home.mkdir()
    package = _real("codex").parents[1]
    final = run_dir / "final.txt"
    argv = [_real("node"), package / "bin" / "codex.js", "exec", "--json",
            "--ephemeral", "--ignore-user-config", "--skip-git-repo-check",
            "--dangerously-bypass-approvals-and-sandbox", "-o", final,
            # No web lookup of the defect, the same rule as for Claude.
            "-c", 'web_search="disabled"',
            "-m", cell["model"]]
    if cell.get("effort"):
        argv += ["-c", f'model_reasoning_effort="{cell["effort"]}"']
    argv.append(prompt)
    env = {"HOME": run_dir / "home", "CODEX_HOME": home}
    return Invocation(
        argv=argv, env=env, read=[argv[0], package],
        auth=[(CODEX_FOLDER / "auth.json", home / "auth.json")],
        hosts=list(cell.get("hosts", [])),
        final_file=final,
    )


def parse_codex(stdout, final_file=None, model="unknown"):
    totals, error, completed = {}, None, 0
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type", "")
        if kind == "turn.completed":
            completed += 1
            for key, value in (event.get("usage") or {}).items():
                if isinstance(value, int):
                    totals[key] = totals.get(key, 0) + value
        elif kind in ("turn.failed", "error"):
            error = json.dumps(event)[:500]
    cached = totals.get("cached_input_tokens", 0)
    tokens = {
        # OpenAI counts cached tokens inside input_tokens.
        "input": totals.get("input_tokens", 0) - cached,
        "output": totals.get("output_tokens", 0),
        "cache_read": cached,
        "cache_write": 0,
    }
    final = Path(final_file).read_text() if final_file and Path(final_file).exists() else ""
    if not completed:
        # No finished turn means no usage record: the cost is unknown.
        return {"by_model": {}, "raw_usage": totals, "usd_reported": None,
                "turns": None, "error": error or "no turn.completed event",
                "final": final}
    return {"by_model": {model: tokens}, "raw_usage": totals,
            "usd_reported": None, "turns": None, "error": error, "final": final}


# --- Fake agent for the rig's own tests ---------------------------------------

FAKE = PACKAGE / "fake_agent.py"


def fake(cell, prompt, run_dir, budget_usd, scenario=None):
    argv = ["python3", FAKE, cell["model"]]
    read = [FAKE]
    if cell["model"] == "probe":
        # Paths the sandbox must hide: the rig repo with its hidden tests,
        # the sign-in folders, the fixture cache, and the sockets under /run
        # and /var. The rig folder itself shows, because this file is bound
        # inside it. A prepared environment must show, so it comes last.
        argv += [ROOT / ".git", ROOT / "scenarios", scenario.hidden,
                 scenario.solution("probe").parent,
                 CLAUDE_FOLDER, CODEX_FOLDER, STATE / "fixtures",
                 "/run/docker.sock", "/var/snap",
                 *([scenario.env] if scenario.env else [])]
    if cell["model"] == "netprobe":
        # The hosts it should reach; it also tries a direct connect and a
        # host that is not on the list.
        argv += cell.get("hosts", [])
    solution = scenario.solution(cell["model"]) if scenario else None
    if solution and solution.is_dir():
        argv.append(solution)
        read.append(solution)
    if cell.get("commit"):
        argv.append("--commit")
    return Invocation(argv=argv, env={"HOME": run_dir / "home"}, read=read,
                      hosts=list(cell.get("hosts", [])))


HARNESSES = {"claude": (claude, parse_claude), "codex": (codex, parse_codex),
             "fake": (fake, parse_claude)}
