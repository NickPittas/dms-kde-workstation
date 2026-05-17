# Fresh Machine Validation Results

Date:
Tester:
Machine:
GPU:
Starting session (KDE/niri/etc):
Fedora version:

## Goal

Record a real end-to-end validation of the safe DMS + Mango first-login flow.

## Preflight

- DMS install result:
- Quickshell check result:
- Mango install result:
- Mango session entry result:

## Clone and Apply

- Dry-run command used:
- Dry-run result:
- Apply command used:
- Apply result:
- Any failure messages shown:

## Before Session Switch

- `scripts/test-first-mango-readiness` result:
- First Run Setup blocker state:
- `dms.service` enabled/disabled:
- Files confirmed present:
  - `~/.config/mango/config.conf`
  - `~/.config/systemd/user/xdg-desktop-portal.service`
  - `~/.config/xdg-desktop-portal/mango-portals.conf`
  - `~/.local/bin/dms-mango-settings`

## First Mango Login

- Was Mango visible in SDDM:
- Did login succeed:
- Did DMS appear automatically:
- Could the user open the settings app:
- Could the user log out safely:
- Any blank/empty-session symptoms:

## After First Mango Login

- DMS Theme/Colors export result:
- Reboot result:
- `scripts/dms-workstation-health` result:
- Portal/file chooser result:
- Screenshot workflow result:
- Startup app flow result:

## Problems Found

- Problem 1:
  - exact symptom:
  - reproduction:
  - recovery used:
- Problem 2:
  - exact symptom:
  - reproduction:
  - recovery used:

## Verdict

- [ ] PASS: safe for novice first-login flow
- [ ] FAIL: still unsafe / misleading

## Notes

- What was confusing?
- What recovered successfully?
- What still assumes too much Linux knowledge?
