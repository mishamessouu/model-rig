# Batch 20261019T065231Z-booking-ladder

2 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test.

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| claude-opus-medium | open | 1 | s1-sql-injection x1 | 1/1 | 21% to 100% | 0 | 0 | 10.239 | 10.239 | 0.144 | 28 | 16 | unknown |
| codex-luna-medium | open | 1 | s1-sql-injection x1 | 1/1 | 21% to 100% | 0 | 0 | 0.133 | 0.133 | n/a | 44 | 7 | unknown |

The network proxy refused a host in these runs: codex-luna-medium.open.r1 (ab.chatgpt.com, sdmntprcentralindia.oaiusercontent.com, sdmntprcentralus.oaiusercontent.com, sdmntprdenmarkeast.oaiusercontent.com, sdmntprnortheu.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-opus-medium | open | 6 | 1,433 | 22,824 | 13,828 |
| codex-luna-medium | open | 4,810 | 553 | 56,704 | 0 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-opus-medium.open.r1 | s1-sql-injection | True | Made the search query in `bookings/repository.py` use SQL parameters instead of pasting user input into the SQL, which closes an injection hole that let any use |
| codex-luna-medium.open.r1 | s1-sql-injection | True | Parameterized booking search because it prevents user input from changing the SQL query. |
