#!/usr/bin/env bash
# Give the rig its own Claude Code and Codex sign-ins.
#
#     scripts/login.sh          sign in both
#     scripts/login.sh claude   sign in Claude Code only
#     scripts/login.sh codex    sign in Codex only
#
# The rig copies a sign-in into each run and copies a refreshed token back.
# A separate sign-in keeps those refreshes away from your own sessions.
set -euo pipefail
state="${MODEL_RIG_HOME:-$HOME/.model-rig}"
umask 077
which="${1:-both}"

if [[ "$which" == both || "$which" == claude ]]; then
  mkdir -p "$state/claude-config"
  export CLAUDE_CONFIG_DIR="$state/claude-config"
  echo "Claude Code: the folder is $CLAUDE_CONFIG_DIR."
  if claude auth status --json 2>/dev/null | grep -q '"loggedIn": *true'; then
    echo "Claude Code is signed in already."
  else
    echo "Claude Code prints a web address. Open it, sign in, and paste the code here."
    claude auth login --claudeai
  fi
  unset CLAUDE_CONFIG_DIR
fi

if [[ "$which" == both || "$which" == codex ]]; then
  mkdir -p "$state/codex-home"
  export CODEX_HOME="$state/codex-home"
  echo "Codex: the folder is $CODEX_HOME."
  if codex login status >/dev/null 2>&1; then
    echo "Codex is signed in already."
  else
    echo "Codex prints a web address and a code. Open the address and enter the code."
    codex login --device-auth
  fi
fi
