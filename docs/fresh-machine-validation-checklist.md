# Fresh Machine Validation Checklist

Use this on a second machine or fresh Fedora install.

## Goal

Prove that a novice user can go from a working desktop session to a working first Mango login without guessing and without landing in an empty session.

## Rules

- Start from a currently working session such as KDE or niri.
- Do not switch to Mango until the checklist says to.
- Record every failure exactly as the user would see it.

## Preflight

- [ ] Fedora 44 is updated
- [ ] User has sudo access
- [ ] A working non-Mango session is available
- [ ] Internet access works

## Install DMS

- [ ] Run `sudo dnf copr enable avengemedia/dms`
- [ ] Run `sudo dnf install dms`
- [ ] Verify `command -v dms`
- [ ] Verify `command -v qs`

## Install Mango

- [ ] Run `sudo dnf install --nogpgcheck --repofrompath 'terra,https://repos.fyralabs.com/terra$releasever' terra-release`
- [ ] Run `sudo dnf install mangowm`
- [ ] Verify `command -v mango`
- [ ] Verify `/usr/share/wayland-sessions/mango.desktop` exists
- [ ] Do not log into Mango yet

## Clone and Apply

- [ ] Clone this repo
- [ ] Run `scripts/apply-mango-baseline --install-packages`
- [ ] Confirm dry-run output is understandable
- [ ] Run `scripts/apply-mango-baseline --apply --install-packages`
- [ ] Confirm failure messages are actionable if something is missing

## Verify Before Session Switch

- [ ] `~/.config/mango/config.conf` exists
- [ ] Mango config contains `exec-once=env QT_QPA_PLATFORMTHEME=qt6ct QT_QPA_PLATFORMTHEME_QT6=qt6ct dms run`
- [ ] `~/.config/systemd/user/xdg-desktop-portal.service` exists
- [ ] `~/.config/xdg-desktop-portal/mango-portals.conf` exists
- [ ] `~/.local/bin/dms-mango-settings` exists
- [ ] `systemctl --user is-enabled dms.service` is not `enabled`
- [ ] Run `scripts/test-first-mango-readiness`
- [ ] It ends with `READY`
- [ ] First Run Setup shows no hard blockers

## First Mango Login

- [ ] Log out
- [ ] Choose Mango in SDDM
- [ ] Log in successfully
- [ ] DMS shell appears
- [ ] Basic keybindings work
- [ ] A logout path is obvious and working
- [ ] DMS Mango Settings opens

## After First Mango Login

- [ ] Export DMS Theme/Colors once
- [ ] Reboot once
- [ ] Run `scripts/dms-workstation-health`
- [ ] Confirm portal/file chooser works
- [ ] Confirm screenshots work
- [ ] Confirm startup app flow works

## Pass Criteria

- No empty Mango session
- No silent failure in setup steps
- No duplicate/conflicting default Mango keybinds from this repo
- User can recover using README/app guidance alone

## Record Results

After running this checklist, copy the findings into:

```text
docs/fresh-machine-validation-results-template.md
```
