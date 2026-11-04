# Local deployment and opt-in scheduling

## Local use

Run `python3 -m tennis.server`; open http://localhost:8765. Python's built-in HTTP
server is intended for local development, not a production internet deployment.
No secrets, raw datasets or project files are exposed through static routes. The
API is read-only. The server is not an update endpoint and cannot execute the agent.
Open pages check publication metadata once a minute while visible, refreshing
rankings after a newly validated snapshot is published. They do not fetch tennis
results or spend model calls themselves.

WSL processes depend on Windows/WSL staying awake. A Go subscription does not keep
this computer running. No scheduled task, public deployment or paid feed was
activated by installation.

## Deterministic refresh job

The command a scheduler should run, from the project directory, is:

```bash
python3 -m tennis.update --refresh
```

For the pinned archive, running frequently is pointless: it is immutable. Use an
offline replay when testing model changes. After a permitted updating feed exists,
set cadence according to its publishing latency/rate limits. Weekly official
ranking ingestion and finished-match polling are different jobs conceptually;
minute-by-minute page rendering is unnecessary when inputs have not changed.

Examples below are **not installed**. Review source terms and choose cadence first.

### Linux cron (always-on machine)

Example daily refresh after permission and source configuration:

```cron
15 6 * * * cd /absolute/path/Sports_Analysis && /usr/bin/python3 -m tennis.update --refresh >> /absolute/path/court-current-update.log 2>&1
```

Cron's working directory and Python path must be explicit. Monitor logs and the
`/api/meta` update status. Never clear a lock just to make a failed job go green.

### Windows Task Scheduler / WSL

Create a task manually only when wanted. Program: `wsl.exe`. Example arguments,
substituting your installed distribution name:

```text
-d Ubuntu --cd /mnt/c/Users/Carte/Sports_Analysis python3 -m tennis.update --refresh
```

Check `wsl --list --quiet` in Windows first; do not assume the distribution name.
Set “Do not start a new instance” and appropriate wake/start permissions. The
Python lock is a second layer against overlapping jobs. Test interactively before
enabling unattended runs. Keep logs and backups outside transient WSL sessions.

### OpenCode maintenance runs

Use `opencode run --agent tennis-updater "…"` for occasional diagnosis/maintenance.
CLI `--agent` is verified in the installed CLI. Do not use `--auto` as a substitute
for reviewing agent permissions. No model ID is hardcoded. Running this periodically
can consume subscription allowances and still does not obtain new data from a
frozen source. Use the deterministic updater for routine arithmetic.

## Public hosting checklist

Before deploying: resolve data redistribution/commercial rights, player photo
rights, permitted current feed coverage including ITF, and sourced health reports.
Use a production application server/reverse proxy with HTTPS, monitoring, request
limits, backups, independent health checks and protected update execution. Do not
expose the Python development server directly. Preserve publication atomicity and
keep public views read-only. Avoid exposing medical claims without provenance.

Back up `config.json`, optional metadata, cached raw checksums/files and the source
license documents. SQLite and API snapshots are rebuildable from those inputs.
Retain source/model revisions when comparing historical ranking changes.
