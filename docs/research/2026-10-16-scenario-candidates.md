# Scenario candidates: real security fixes to revert

Date: 2026-10-16. Method: bug reinjection. Take a public app at a pinned
commit, revert one security fix, and use the fix's own test as the hidden
test. A research agent read the fix commits and file lists through the
GitHub API. It did not clone, build, or run any project.

## Recommended

1. **wger, workout log IDOR on a write path.** github.com/wger-project/wger,
   AGPL-3.0, Python 3.12, Django and DRF, about 36k lines of app code.
   GHSA-rjpf-7pf5-q54x / CVE-2026-46438. Fix commit b29cf178651bbcc243d21673932e32bd42017893.
   `WorkoutLogViewSet.get_owner_objects()` does not list `slot_entry`, so the
   shared owner check in `utils/viewsets.py` skips that foreign key. A test
   came with the fix (`test_api_ownership_checks.py`). 3 non-test files,
   +16/-3. Rung 3. SQLite in `settings/ci.py`. Check whether the hidden test
   needs the model changes too.
2. **wger, gym check passes when both gyms are None.** GHSA-c72h-82w6-rqfp /
   CVE-2026-43976. Fix commit b51f472ab2f790d8b4e67b4371bd6d1915af2930.
   `None != None` is False, so a trainer with no gym reads notes and
   contracts of any user with no gym. Test came with the fix. Rung 2 to 3.
   The commit does not name the advisory; confirm the match.
3. **Actual sync-server, cross-user budget file access.**
   github.com/actualbudget/actual, `packages/sync-server`, MIT, TypeScript,
   Express 5, better-sqlite3, about 13k lines. GHSA-qmjj-p7m9-wjrv /
   CVE-2026-27638. Fix commit 9966c024cb75f57943193cac8e42f401efed9d08.
   `/sync/*` checks that a file exists, not that the caller may use it.
   Test came with the fix. Revert `requireFileAccess` in one or two
   endpoints only. Rung 3. Setup risk medium: yarn 4 monorepo, native
   modules. More in the same project: path traversal GHSA-27vg-33gh-4hwg
   (18072e1d), secrets admin check (3494f78c94).

## Alternates

4. changedetection.io (Apache-2.0, Flask): decorator order auth bypass,
   GHSA-jmrh-xmgh-x9j4, 31a760c2. Static test only; famous. SSRF fix fe7aa38c65.
5. Unleash (Apache-2.0, TypeScript): missing `await` on a permission check,
   GHSA-72h8-wp98-7hch, 43e8db37b8 and 7bb2829fc4. Needs Postgres.
6. pyLoad (AGPL-3.0): SQL injection across three layers,
   GHSA-pwh4-6r3m-j2rf, 134edcdf. No test came with it. pycurl build risk.
7. Askbot (GPL-3.0, Django): avatar IDOR, GHSA-r2jv-fwfr-4j8c, 3da3d75f35.
   Mixed release commit; Postgres in CI.

## Excluded

- Bugsink: ideal fix (1a98424a87), but PolyForm Shield is not open source.
- OpenCVE: Business Source License.
- openwisp-ipam: a 1.4k-line plugin, not an app.
- EverShop, Aegra, alerta: need Postgres or MongoDB.

## Sources

GitHub advisory API (pip and npm, since 2023-06, CWEs 639, 862, 863, 285,
284, 287, 22, 89, 918, 915, 78, 943, 1336, about 2,800 advisories), the
advisory page and commit diff for each GHSA above, repository licence and
size data, wger `settings/ci.py`, Actual `sync-server/package.json`,
Askbot `tox.ini`.

## Open risk

Memorisation: a model may know a fix if the fix predates its training
cutoff. Check each fix date against each model's cutoff before a batch.

## Fixes after June 2026

Date: 2026-10-16. Method: all 20 wger advisories from the GitHub
advisory API, each mapped to its fix commit in a wger clone. Every
commit date below was checked with
`gh api repos/wger-project/wger/commits/<sha>`. Committer and author
dates agree for each commit.

**No published wger advisory has a fix commit after 2026-06-30.** The
five advisories published on 2026-10-04 (GHSA-v3x9, -rjpf, -x249, -c72h,
-xf64) name release 2.6 (2026-06-17). Their fixes date from April and May,
for example b51f472a (c72h, 04-26), 9be2d5f2 (x249, 05-08), 41500716
(xf64, 05-08), and b29cf178 (rjpf, 05-08).

The fixes below are security fixes with no published advisory. A fix
can still get an advisory later; check again before a build. All came
with a test. "Files" counts non-test files only.

| Commit | Date | Defect class | Files | Note |
|---|---|---|---|---|
| dd28603a | 2026-10-04 | IDOR across gyms (CWE-639) | `gym/views/config.py` +1/-1 | Compares the URL pk, not the object's gym. Smallest candidate. |
| d0ca31ca | 2026-10-04 | Missing authorization (CWE-862) | `gym/views/admin_config.py` +5/-2 | Edit view lacks `WgerPermissionMixin`. |
| 6a90e34f | 2026-10-04 | Privilege misuse in trainer-login session (CWE-269) | `core/views/user.py` +4, template | Impersonating trainer could get the member's API key. |
| 5c1817e9 | 2026-10-04 | Missing role hierarchy check (CWE-269) | `core/views/user.py`, `gym/helpers.py`, `gym/views/gym.py` | Same class as GHSA-x249, wider. |
| eaaf70d5 | 2026-10-08 | Role check skips deactivated accounts (CWE-863) | `core/views/user.py` +2/-3 | Follow-up to 5c1817e9. |
| 0c125dff | 2026-09-11 | Missing authorization on API create (CWE-862) | `exercises/api/permissions.py`, `exercises/api/views.py` | Any user could POST `/api/v2/exercise/`. |
| 0e0cc4e2 | 2026-09-15 | Markup injection in PDF, fetch of attacker URL (CWE-74, CWE-918) | `manager/views/pdf.py`, `nutrition/views/plan.py` | reportlab reads user text as markup. |
| 63520495 | 2026-09-27 | Same as 0e0cc4e2 | `manager/helpers.py` | Follow-up for the day table. |
| a76691e1 | 2026-08-10 | Deactivated user keeps API access (CWE-613) | `utils/headless_auth.py` +6 | JWT auth did not check `is_active`. |
| 3c6ce4b7 | 2026-07-09 | State change on GET, CSRF (CWE-352) | `core/views/user.py`, `gym/views/gym.py`, templates | Merge of ace2994d (2026-06-27). Public issue #2380. |

Best fits for a scenario: dd28603a (one-line IDOR, rung 2 or 3),
d0ca31ca (missing mixin), and 0c125dff (API permission). A later fix
date lowers the memorisation risk. Compare each date with each model's
training cutoff before a batch. None is built.
