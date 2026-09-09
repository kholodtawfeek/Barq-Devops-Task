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
| Recorded challenge (video_challenge.sh) | .assessment/challenge.json | 0936534 | TBD |
| Live port change 8080 -> 8090 | docker-compose.yml / .env | 0936534 | TBD |
| Live third app instance (app-03) | docker-compose.yml | 0936534 | TBD |
| Final validate.py rerun on 3-instance/8090 setup | validate.py output | 0936534 | TBD |

## Video

Video URL: [https://drive.google.com/drive/folders/10yFfsHqWQb2pNyP2BHk9o1V4zrSPMDse?usp=sharing]
Final video commit: 0936534

## Note on video-related rows

Rows marked with commit 0936534 correspond to live changes made only during the recorded
video session (video_challenge.sh fix, port change, third instance, final validation).
These changes were not present before the video and exist only as part of the live
demonstration and its resulting commit.

An earlier attempt during the same recording session produced commit 3d0b442 with the
same message. That state was reverted in commit 1e96591 to restore the pre-video
baseline (2 instances, port 8080) before repeating the live steps cleanly. Commit
0936534 is the final, correct commit that matches the actual submitted video.

## Note on known limitation

STEP 11 (final validate.py rerun) shows one failed check: counter_increments. This was
caused by a timing race when app-03 was added live — NGINX began routing traffic to it
before its own healthcheck start_period completed. Full explanation in decisions.md.
