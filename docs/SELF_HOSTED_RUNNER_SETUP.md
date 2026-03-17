# Self-Hosted Runner Setup

## Goal

Prepare a trusted Linux runner that can execute AgentSlam workflows requiring local ROS, Isaac-adjacent assets, and ChatGPT-managed Codex auth.

## Recommended Runner User On This Machine

For this specific machine, the fastest working path is to run the runner under `peng`, because:

- the repository already lives under `/home/peng/AgentSlam`
- the current Codex auth is already present under `/home/peng/.codex/auth.json`

If you later want stricter separation, create a dedicated runner user and complete a fresh `codex login` under that user before enabling codex-bearing workflows.

## Recommended Runner Root

Suggested install root on this machine:

- `/home/peng/actions-runner/agentslam`

Safe bootstrap-only scaffold:

- run `bash scripts/ops/bootstrap_self_hosted_runner.sh`

That script writes a non-sensitive local scaffold under `artifacts/ops/self_hosted_runner_bootstrap/` by default.

## Recommended Labels

Use these labels in GitHub Actions:

- `self-hosted`
- `linux`
- `x64`
- `agentslam`

GitHub documentation says self-hosted runners automatically receive default labels such as `self-hosted`, the operating system label, and the architecture label. Add `agentslam` as the custom routing label for this repo.

## Registration Flow

1. In GitHub, open the repository settings for Actions runners.
2. Add a new self-hosted runner for Linux x64.
3. Copy the install commands into the chosen runner root.
4. During initial `config.sh`, include labels such as:

```bash
./config.sh --url <REPOSITORY_URL> --token <REGISTRATION_TOKEN> --labels agentslam,linux,x64
```

You can include `self-hosted` implicitly because GitHub assigns it by default.

## Service Setup

GitHub documentation says you must add the runner first before configuring it as a service. On Linux systems with `systemd`, use the `svc.sh` helper created by the runner install:

```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

Use `sudo ./svc.sh status` to confirm the runner service state.

## Directory Layout Recommendation

- runner install: `/home/peng/actions-runner/agentslam`
- repository checkout: `/home/peng/AgentSlam`
- Codex auth home: `/home/peng/.codex`
- runner logs:
  - runner internal logs under the install directory, typically `_diag/`
  - repo-local Codex logs under `artifacts/ops/codex/`
  - nightly artifacts under `artifacts/nightly/`

## Dependency Checklist

Before enabling workflows on the runner, confirm:

- `git`
- `bash`
- `/usr/bin/python3`
- `/usr/bin/colcon`
- ROS Humble under `/opt/ros/humble`
- `flock`
- `codex`

## Runner-Side Sanity Check

After registration and before enabling schedule-heavy workflows:

```bash
cd /home/peng/AgentSlam
bash scripts/ops/check_codex_auth.sh
bash scripts/ops/phase1_ci_suite.sh --mode ci --artifact-dir /home/peng/AgentSlam/artifacts/nightly/manual-check --report-path /home/peng/AgentSlam/reports/nightly/manual-check.md
```

If both pass, the machine is ready for `robotics-ci.yml` and the nightly Prompt 5 workflows.
