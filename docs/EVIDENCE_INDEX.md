# Evidence index

Maps each requirement to where it is proven in this repository, which commit introduced it,
and the video timestamp where it is demonstrated live. Video timestamps are filled in after
the recording (see note at the bottom).

| Requirement | File / output | Commit | Video timestamp |
|---|---|---|---|
| Investigation journal (10 findings) | troubleshooting.md | 631e2e4 | TBD |
| Dockerfile fix (drop root, remove baked secret) | Dockerfile | 7ae4902 | TBD |
| Port/credential/healthcheck fixes | config/app.env, docker-compose.yml, nginx/nginx.conf | 0666548 | TBD |
| Log analysis (10 template questions) | log_analysis.md | 66432db | TBD |
| validate.py (17 bounded checks) | validate.py | 63b8713 | TBD |
| failure_test.py (stop/recover backend) | failure_test.py | a698aa6 | TBD |
| backup.sh / restore.sh + persistence proof | backup.sh, restore.sh | 3b568f5 | TBD |
| CI workflow (build, start, validate) | .github/workflows/ci.yml | f7f667d | TBD |
| Decisions log (7 decisions) | decisions.md | 0113b35 | TBD |
| Security review (10 risks) | security_review.md | 59e38d2 | TBD |
| AI usage disclosure | AI_USAGE.md | e7f76b1 | TBD |
| Architecture diagram | architecture.png | 05cfeac | TBD |
| README (setup/build/test/backup/cleanup) | README.md | 281cc9a | TBD |
| Recorded challenge (video_challenge.sh) | .assessment/challenge.json | TBD (video commit) | TBD |
| Live port change 8080 -> 8090 | docker-compose.yml / .env | TBD (video commit) | TBD |
| Live third app instance (app-03) | docker-compose.yml | TBD (video commit) | TBD |
| Final validate.py rerun on 3-instance/8090 setup | validate.py output | TBD (video commit) | TBD |

## Note on video-related rows

Rows marked "TBD (video commit)" correspond to live changes made only during the recorded
video demonstration (port change, third instance, video_challenge.sh fix) and are committed
during/after that recording, not before. Their commit hashes and video timestamps are added
in a documentation-only follow-up commit after the video is recorded and uploaded, as
permitted by the assessment rules ("Explain any later documentation-only commits").
