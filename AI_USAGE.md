# AI usage disclosure

## Tools used
Claude (Anthropic AI assistant) was used throughout this assessment as a collaborative
assistant for investigation, scripting and documentation.

## Purpose and affected files
- **Investigation (Part 1):** Used AI to help form hypotheses from `docker compose logs`
  output and to structure `docs/troubleshooting.md` entries (symptom / evidence / root
  cause / status format).
- **Log analysis (log_analysis.md):** Used AI to write Python one-liners for parsing and
  correlating access.log/application.log/error.log by `request_id` (status counts, latency
  percentiles, malformed-line detection, duplicate-ID detection). All commands were run
  personally against the real log files; the numbers in log_analysis.md are actual command
  output, not AI-generated estimates.
- **Scripting (validate.py, failure_test.py, backup.sh, restore.sh):** AI drafted the initial
  version of each script based on the specific requirements (endpoints, ports, container
  names, network names) from this environment. Each script was then run personally against
  the live environment and iterated on until all checks passed genuinely (17/17 for
  validate.py, 7/7 for failure_test.py; backup/restore proven by an actual create -> backup ->
  delete -> restore -> verify cycle, and again across a full `docker compose down && up`).
- **CI workflow (.github/workflows/ci.yml):** AI drafted the workflow steps (checkout, config
  validation, build, start, bounded readiness wait, run validate.py, teardown). Verified by
  pushing and reviewing the actual GitHub Actions run.
- **Documentation (decisions.md, security_review.md, this file):** AI helped structure and
  word the write-ups, based on the actual fixes made and actual test results from this
  environment — not generic/hypothetical content.

## Verification
Every AI-assisted script or configuration change was executed against the real Docker
environment before being accepted: container health, curl responses, `docker compose ps`,
and script exit codes were checked personally, not assumed from the AI's explanation. No
AI-generated claim was treated as evidence on its own — see the actual terminal output
captured throughout this repository's commits and in troubleshooting.md/log_analysis.md.

## Not used for
Real secrets, credentials or production data were never shared with the AI. All values in
this repository (passwords, tokens) are synthetic lab-only values supplied by the assessment
starter pack.

## Note on duplicate commit message

Commit history contains two commits with an identical message:
"video: apply live challenge fix, change port to 8090, add app-03 instance"

- Commit 3d0b442 was an earlier attempt during the recording session.
- Commit 1e96591 reverted docker-compose.yml, nginx.conf and validate.py
  back to the pre-video state (2 instances, port 8080) to allow a clean
  restart of the live demonstration steps.
- Commit 0936534 is the final, correct commit that matches the actual
  submitted video. This is the commit referenced in the evidence index
  and in the final submission.

No commit dates were altered. Both commits were created in real time
during the same working session.
