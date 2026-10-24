# Anthropic eval practice, and the gaps in model-rig

Research review, 2026-10-18, by a Claude Opus 5.5 subagent. Kept verbatim,
except for one machine path, as the record behind the eval fixes in lab
commits 30ca2ca and 995e084.
What is fixed since: Wilson intervals in the report (gap "Statistics"),
repricing from stored tokens. The other gaps are open.

I read model-rig and all the primary sources it needed. I ran no model and made no API call. Each finding is marked:

- **[V]**: I fetched the source and read the passage.
- **[S]**: I saw it only in a search-result snippet.
- **[I]**: my own inference.

## 1. What Anthropic recommends

| Practice | Source |
|---|---|
| **Three kinds of grader.** Code graders are "fast, cheap, objective, reproducible" but "brittle". Model graders are flexible but non-deterministic. Human graders are the "gold standard" and are used to calibrate model graders. [V] | [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), 2026-01-09 |
| **pass@k and pass^k.** pass@k is the chance of at least one success in k trials. pass^k is the chance that all k succeed, which measures consistency. [V] | same |
| **Read the transcripts.** "Failures should seem fair." What an agent leaves out can matter more than what it includes. [V] | same; [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents), 2025-09-11 |
| **Capability evals and regression evals.** Capability evals start with a low pass rate. Regression evals stay near 100%, and capability evals "graduate" into them. [V] | Demystifying |
| **Saturation.** "0% pass@100 is most often a signal of a broken task." The best model at the highest effort should be "well below 100%". The tooling warns at 95% or more. [V] | Demystifying; [Automating eval design and hillclimbing with Claude](https://claude.dev/blog/automating-eval-design-and-hillclimbing/), Lance Martin, 2026-09-28 |
| **Balanced problem sets.** Test cases where the agent should act and cases where it should not. Start with 20 to 50 tasks taken from real failures. [V] | Demystifying |
| **Task quality.** Each task has a reference solution. "Two domain experts would independently reach the same pass/fail verdict." [V] | same |
| **Isolated environments.** Each trial starts clean. In one internal eval, Claude gained "an unfair advantage... by examining the git history from previous trials." [V] | same |
| **Grade the outcome, not the path.** Checking for an exact sequence of tool calls is "too rigid". Give partial credit on tasks with several parts. [V] | same |
| **Statistics.** Report the standard error. Cluster it when tasks are related. Resample each question several times. Compare models with paired differences on the same tasks. Do a power analysis to choose the number of tasks. [V] | [A statistical approach to model evaluations](https://www.anthropic.com/research/statistical-approach-to-model-evals), 2024-11-19 |
| **Infrastructure noise.** Resource settings alone moved Terminal-Bench 2.0 by 6 points. Publish the resource configuration. Doubt gaps under 3 points. [V] | [Quantifying infrastructure noise in agentic coding evals](https://www.anthropic.com/engineering/infrastructure-noise), 2026-02-05 |
| **Hill-climbing.** Split the cases at random into train and test. Check that the noise is smaller than the smallest gain you would act on. Make one change per round, keep it only if train and test both improve, and revert it otherwise. Read scored transcripts before you trust a grader. Run the grader twice on the same output. [V] | Automating eval design (above); Writing tools (held-out sets) |
| **Model graders checked against human labels.** Bloom's judge reached a Spearman correlation of 0.86 against 40 hand-labelled transcripts. Petri is the companion auditing tool. [V] | [Bloom](https://www.anthropic.com/research/bloom), 2025-12-19; [Petri](https://www.anthropic.com/research/petri-open-source-auditing) |
| **How SWE-bench is reported.** Opus 4.6 scores are "averaged over 25 trials", with max effort and default sampling. Sonnet 4.6 uses 10 trials. Older cards use a scaffold with bash and string-replace editing only. [S]: the PDF was over the fetch size limit. | [Opus 4.6 system card](https://www.anthropic.com/claude-opus-4-6-system-card) |
| **Success criteria.** Criteria must be specific, measurable, achievable, and relevant, across several dimensions such as accuracy, latency, and price. A different model should do the grading. [V] | [Define success criteria and build evaluations](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests) |

Other benchmarks, only where they show a practice that model-rig lacks:

- SWE-bench Verified removed 61.1% of screened samples because their tests could reject a valid fix. [S, [OpenAI](https://openai.com/index/introducing-swe-bench-verified/)]
- Terminal-Bench 2.0 had three reviewers check each task, at about 3 hours per task. It puts a canary string in every task file. [S, [paper](https://arxiv.org/abs/2601.11868)]
- The METR Task Standard declares network permissions for each task. [S, [STANDARD.md](https://github.com/METR/task-standard/blob/main/STANDARD.md)]

I could not find these, so I do not cite them:

- A Console evaluation-tool page. The develop-tests page does not mention one.
- Agent SDK guidance on evals.
- A separate post about Claude Code's internal evals. Demystifying has one sentence on it: "first for narrow areas like concision and file edits, and then... over-engineering."

The installed `claude-api` skill is an older copy. It does not have the `build-eval` or `hillclimb` commands, so a fresh sparse clone would add them [V].

## 2. Gap table

Facts about model-rig come from its code and from batch `20261016T205957Z` [V].

| Practice | What model-rig does now | Concrete change | Effort |
|---|---|---|---|
| Statistics | `rig/report.py` prints only "3/3", with no interval. A 3/3 has a 95% Wilson interval of about 0.44 to 1. Sonnet has n=1. | Add Wilson intervals and paired differences per scenario to `report.py`. Say in the report that n=3 cannot rank two cells that are close. | S |
| pass@k and pass^k | Only a success count. | Add per-cell columns for mean pass@1, pass@3, and pass^3. | S |
| Contamination and isolation | The agent sandbox shares the host network (`network=True`, `rig/sandbox.py`). The advisory GHSA-rjpf-7pf5-q54x is public. My grep of all 56 run logs found no `curl`, `wget`, or `git fetch` [V]. Fresh copy per run, `.git` stripped [V]. | Send agent traffic through an allowlist proxy that reaches provider hosts only. Add `fix_date` and per-model `cutoff` fields, and make `rig run` refuse a cell whose cutoff is after the fix date. Opus 5.5 states a June 2026 cutoff, and the wger fix is dated 2026-05-08 [I: possible leak]. | M |
| Grade the outcome; human graders | 27 of 56 runs scored "other change", which counts as failure. Some of these could be real, valid security fixes [I]. | Add a `rig review <batch>` command. A person reads each "other change" diff without seeing the cell name and records real or not, plus severity, as `review` in `result.json`. Add a model grader later, checked against those labels as Bloom did. | M |
| Read transcripts | `agent-log.jsonl.gz` is saved, but nothing renders it. | Add `rig transcripts <batch>` to print the tool calls and the last 15 lines of failure output. Read a sample from each cell. Tag each failure as agent, task, or infra. | S |
| Balanced set | No case where nothing needs a fix. This is README "Next" item 2. | Add a scenario `wger-fixed` pinned to fix commit `b29cf17` with the `security` prompt. Score it as no invented vulnerability and no regression. | M |
| Saturation and problem-set size | One real fix, which gives three sibling defects, plus one toy scenario. Opus scored 6/6. | Add 10 to 20 reinjected CVEs across vulnerability classes (IDOR, SQLi, XSS, SSRF, path traversal), starting from `docs/research/2026-10-16-scenario-candidates.md`. Warn in the report when the best cell is at 95% or more. | L |
| Task quality and valid alternative fixes | `rig check` proves that each defect test fails before the fix and passes after it [V]. The test was loosened once already, in commit `aac1c4d` (refusal status). | Add 1 or 2 `solutions/alt-*` fixes per defect, and make `rig check` require that they pass too. Add a reviewer checklist in `docs/`. | S |
| Infrastructure noise | No CPU or memory limits. A timeout of 1800 s. CLI versions are recorded [V]. | Run each cell under `systemd-run --scope -p MemoryMax= -p CPUQuota=`. Record host load. Rerun infra failures and do not count them. | S |
| Canary | Hidden tests and fixes are published in the public `model-rig` repo. | Put a canary GUID in `hidden/` and `solutions/`. | S |
| Complete cost data | `config/prices.toml` has no Sonnet or Astra prices, so those cells show "n/a" for cost. | Add the missing price rows, then run `rig report` again. | S |
| Hill-climb with held-out tasks | Not needed for model comparison. | If you later tune prompts or harness settings, split the scenarios into train and test first. | M |

## 3. Top five changes for security colleagues

1. **Close the network and record training cutoffs.** A security reader's first question will be "could it look up the CVE?". Today the honest answer is "yes, but the logs show no fetch". The proxy plus the cutoff check turn that into "no".
2. **Review the "other change" diffs.** Half the runs were scored as failures without anyone reading them. A real vulnerability found off the planted list is a success to a security reader. Calling it a failure undermines the ranking.
3. **Error bars, pass^3, and paired comparisons.** "Opus 6/6, Astra 5/6" is not a statistically separable result. Show the intervals, or run more trials before you claim a ranking.
4. **More CVEs, plus the clean control.** One fix family cannot support claims about security work in general. The clean control shows which models invent vulnerabilities.
5. **Valid alternative fixes and transcript sampling.** This answers "does your test reject correct fixes?". It is the same failure that led to 61.1% of screened samples being removed for SWE-bench Verified.

Two things I did not verify:

- I did not see the Opus 4.6 system-card SWE-bench details in the PDF itself, only in a search snippet.
- The possible Opus 5.5 contamination is an inference from the cutoff and fix dates. It is not shown by any run.

The repo I read is the lab copy of model-rig. The files the changes touch are `rig/report.py`, `rig/sandbox.py`, `rig/check.py`, `rig/run.py`, `config/prices.toml`, and `scenarios/wger-log-idor/scenario.toml`.
