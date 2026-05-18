# DMS KDE Workstation

A reproducible **Fedora 44 KDE → MangoWM + DMS** workstation toolkit focused on **creative-app usability**, **KDE/Qt theming**, and **GUI-driven setup**.

This repo exists to turn a fragile hand-tuned setup into something you can actually install, verify, repair, and maintain.

## What this repo is for

This project is for people who want:

- **MangoWM** as the compositor
- **Dank Material Shell (DMS)** as the shell/bar/theme surface
- a **KDE/Qt-first** app stack
- working **Dolphin → Nuke / Blender drag-and-drop**
- working **tray icons**
- working **portal/file chooser behavior**
- working **Qt theming outside Plasma**
- a real **settings app** instead of remembering random commands

It is **not** trying to be a minimal rice.
It is trying to be a practical, reproducible workstation profile.

---

## What the repo provides

- a tested **Mango baseline config**
- a **baseline installer/deployer**
- a **health check** script
- restore/repair scripts
- a Qt companion app: **DMS Mango Settings**
- a **First Run Setup** page inside the app
- startup helpers for tray-sensitive and GUI startup apps
- documentation for the setup, decisions, and workarounds

---

## Safe install path for a new machine

**Do not switch to the Mango session yet.**

Run the setup from your current working desktop first (KDE, niri, or another session that already works).

If you switch to Mango too early, you can land in an empty session with no DMS shell, missing keybinds, and poor recovery options.

### 1) Install DMS first

Official Fedora DMS install path:

```bash
sudo dnf copr enable avengemedia/dms
sudo dnf install dms
```

Verify:

```bash
command -v dms
command -v qs
```

If `dms` or `qs` is missing, stop here and fix DMS first.

### 2) Install Mango

Official Fedora Mango install path:

```bash
sudo dnf install --nogpgcheck --repofrompath 'terra,https://repos.fyralabs.com/terra$releasever' terra-release
sudo dnf install mangowm
```

Do **not** log into Mango yet.

### 3) Clone this repo

```bash
git clone git@github.com:NickPittas/dms-kde-workstation.git
cd dms-kde-workstation
```

### 4) Preview the baseline changes

```bash
scripts/apply-mango-baseline --install-packages
```

Dry-run is the default.

### 5) Apply the baseline for real

**Do not run this inside Ghostty.** `dnf install` rebuilds the fontconfig cache, which crashes Ghostty (SEGV) and kills your terminal mid-install. Use SSH, Konsole, Kitty, or a TTY (Ctrl+Alt+F3) instead.

```bash
scripts/apply-mango-baseline --apply --install-packages
```

The script is idempotent — if it gets interrupted, just re-run it. It skips already-installed packages and already-deployed files.

If you previously enabled `dms.service`, disable it before first Mango login so Mango's explicit `dms run` startup line is the only DMS startup path:

```bash
systemctl --user disable dms.service
```

Optional Obsidian Wayland/DnD fix:

```bash
scripts/apply-mango-baseline --apply --install-packages --obsidian-override
```

### 6) Verify before session switch

Before you log out, run:

```bash
scripts/test-first-mango-readiness
```

Only continue if it ends with:

```text
READY: Safe to log out, choose the Mango session, and attempt first login.
```

If it says `NOT READY`, do **not** switch to Mango yet.

It also verifies that the Mango session entry exists at:

```text
/usr/share/wayland-sessions/mango.desktop
```

One common blocker is leaving `dms.service` enabled while Mango also starts `dms run`. Disable it from your current working session:

```bash
systemctl --user disable dms.service
```

### 7) First Mango login

Only now:

1. log out
2. choose the **Mango** session in SDDM
3. log into Mango
4. open **DMS → Settings → Theme/Colors**
5. export **GTK3 / GTK4 / QT5 / QT6** once
6. reboot once
7. run:

```bash
scripts/dms-workstation-health
```

---

## First Run Setup in the app

The settings app includes a **First Run Setup** page for this exact migration flow.

Use it like this:

1. stay in your current working KDE/niri session
2. install Mango
3. install DMS
4. clone this repo
5. run **DMS Mango Settings**
6. open **First Run Setup**
7. click **Refresh Status**
8. fix every blocker shown there
9. click **Apply Full Baseline**
10. click **Check Ready for First Mango Login**
11. only then log out and choose Mango

That page is supposed to be the safe gate before first Mango login.
It now also checks DMS startup ownership so you do not accidentally run both `dms.service` and Mango's `dms run` startup path at the same time.

### It handles

- Mango config deployment
- DMS startup line under Mango
- stable Qt/Electron toolkit environment
- portal package checks
- portal override + portal config deployment
- screenshot toolchain install
- settings app install/autostart
- post-startup helper install
- startup app support after the UI appears
- autologin helper deployment checks

It does **not** force personal MIME/default-app choices like browser/editor/file manager during baseline install. Use the app's **Default Apps** page for that.

### Still manual

These are still intentionally manual:

- installing Mango itself
- installing DMS itself
- one-time DMS Theme/Colors export after first working Mango login
- optional SDDM autologin setup

### Recovery if you switched too early

If you already logged into Mango and got a broken or empty session:

1. return to a working TTY or another desktop session
2. clone/fix the repo from there
3. re-run `scripts/apply-mango-baseline --apply --install-packages`
4. confirm the `dms run` exec-once line exists in `~/.config/mango/config.conf`
5. log back into Mango only after the baseline is in place

---

## Settings app

Main script:

```text
tools/dms-mango-settings.py
```

Installed launcher:

```text
~/.local/bin/dms-mango-settings
```

The app currently covers:

- first-run setup
- layouts / scroller
- animations / effects
- input
- keyboard
- keybindings
- window rules
- startup apps
- services
- portals
- theme bridge
- default apps
- screenshots
- remote desktop
- login/autologin
- backups / restore
- tools

### Settings app screenshots

#### Overview

![Overview](assets/screenshots/overview.png)

#### Layout & Scroller

![Layout & Scroller](assets/screenshots/layout-scroller.png)

#### Animations & Effects

![Animations & Effects](assets/screenshots/animations-effects.png)

#### Input

![Input](assets/screenshots/input.png)

#### Keyboard

![Keyboard](assets/screenshots/keyboard.png)

#### Keybindings

![Keybindings](assets/screenshots/keybindings.png)

#### Startup

![Startup](assets/screenshots/startup.png)

#### Services

![Services](assets/screenshots/services.png)

The Services page now reflects services that actually exist on the current machine instead of assuming every user has the same remote-desktop, sync, or tray tools installed.

#### Portals

![Portals](assets/screenshots/portals.png)

#### Theme Bridge

![Theme Bridge](assets/screenshots/theme-bridge.png)

#### Login

![Login](assets/screenshots/login.png)

#### Backup & Recovery

![Backup & Recovery](assets/screenshots/backup-recovery.png)

#### Tools

![Tools](assets/screenshots/tools.png)

---

## Important behavior decisions

### Startup apps

Under Mango, plain KDE-style autostart behavior is not enough for this setup.

So this project uses:

1. `.desktop` files in `~/.config/autostart/`
2. `dms-mango-post-startup`
3. delayed startup after DMS tray/UI is ready

That is intentional.

### Dolphin from the DMS dock

Dolphin launched from:

- **Meta+E** worked
- **Vicinae** worked
- **DMS dock** needed extra care on one machine

That behavior is **not** currently treated as a safe universal baseline fix.

If Dolphin launched specifically from the DMS dock still looks wrong on your machine, compare it against:

- Dolphin launched from a normal compositor bind
- Dolphin launched from Vicinae
- Dolphin launched from the DMS dock

If the problem is only the DMS dock path, a DMS `appOverrides` entry with:

```text
QT_QPA_PLATFORMTHEME=qt6ct
QT_QPA_PLATFORMTHEME_QT6=qt6ct
```

may help, but it should be treated as a targeted workaround, not a default assumption for all users.

### DMS under Mango

DMS must be launched under Mango with explicit Qt theming env:

```ini
exec-once=env QT_QPA_PLATFORMTHEME=qt6ct QT_QPA_PLATFORMTHEME_QT6=qt6ct dms run
```

Without that, DMS-launched Qt/KDE apps can come up white or incorrectly themed.

The shipped Mango baseline now keeps compositor binds generic. It does not assume your browser, terminal, editor, or file manager launch shortcuts.

---

## Scripts you will actually use

### Install / apply baseline

```bash
scripts/apply-mango-baseline --apply --install-packages
```

### Pre-switch readiness check

```bash
scripts/test-first-mango-readiness
```

### Health check (after first Mango login)

```bash
scripts/dms-workstation-health
```

### Restore baseline-managed files

```bash
scripts/restore-mango-baseline
```

### Smoke test the settings app

```bash
scripts/test-mango-settings-smoke
```

### Reboot verification

```bash
scripts/test-reboot-verification
```

### Fresh-machine validation docs

Checklist:

```text
docs/fresh-machine-validation-checklist.md
```

Results template:

```text
docs/fresh-machine-validation-results-template.md
```

---

## Troubleshooting

### KDE/Qt apps are white or wrongly themed

Check:

- `qt5ct` and `qt6ct-kde` are installed
- `QT_QPA_PLATFORMTHEME=qt6ct`
- `QT_QPA_PLATFORMTHEME_QT6=qt6ct`
- DMS theme export was run once

Then log out/in or restart DMS.

### Dolphin launched from DMS dock has checkerboard rows

This is specifically the DMS dock launch path.

Try the global baseline first:

- confirm `qt5ct` and `qt6ct-kde` are installed
- confirm DMS is started under Mango with the explicit `qt6ct` env line
- export DMS Theme/Colors once after first working Mango login

If the problem still happens only from the DMS dock, a DMS app override for Dolphin with:

```text
QT_QPA_PLATFORMTHEME=qt6ct
QT_QPA_PLATFORMTHEME_QT6=qt6ct
```

may help as a targeted workaround. This repo no longer auto-applies that override during baseline setup.

### Tray icons are missing after login

Check:

- `~/.local/bin/dms-mango-post-startup`
- `~/.config/dms-kde-workstation/startup.json`
- `~/.local/state/dms-kde-workstation/mango-post-startup.log`
- `~/.config/systemd/user/xdg-desktop-portal.service`
- `~/.config/xdg-desktop-portal/mango-portals.conf`

The post-startup helper is responsible for delayed startup when DMS tray is ready.
If the session is still incomplete, return to a working session or TTY and re-run:

```bash
scripts/apply-mango-baseline --apply --install-packages
```

### Startup apps do not appear on login

This project intentionally does **not** rely on plain KDE assumptions.

Startup apps are launched by the post-startup helper after the UI is ready.
Use the app’s **Startup** page.

The shipped `startup.json` baseline is intentionally neutral. It does not assume Dropbox, Sunshine, or other personal services are installed. Add tray-sensitive services only if you actually use them.

### Ghostty transparency/blur under Mango behaves differently than under niri

This is still not fully normalized/documented as a clean baseline behavior.
Mango per-window opacity works, but Ghostty’s own transparency/blur path is not yet treated as fully solved in this repo.

### Screenshot selection UI behaves strangely

This repo uses `grim + slurp + swappy`, and the selection overlay was tuned to reduce blur/fill artifacts under Mango.
If screenshot output is correct but selection preview looks odd, check the installed region screenshot scripts in `~/.local/bin/`.

### Window Rules cannot list/select open windows

The Window Rules page uses `lswt` to list open Wayland windows and get app IDs across monitors.
The baseline installer builds and installs it automatically when run with `--install-packages`.

Manual install:

```bash
sudo dnf install -y git gcc make wayland-devel wayland-protocols-devel scdoc
git clone https://git.sr.ht/~leon_plickat/lswt ~/.local/src/lswt
make -C ~/.local/src/lswt
sudo make -C ~/.local/src/lswt install
```

Test:

```bash
lswt
lswt --custom 'a,t,A'
```

### `dms-mango-settings` says `No module named 'PySide6'`

Install the settings app dependency:

```bash
sudo dnf install -y python3-pyside6
```

Then re-run:

```bash
scripts/apply-mango-baseline --apply --install-packages
```

The installer now includes `python3-pyside6`; older checkouts did not.

### Install crashed / was interrupted / machine in unknown state

The baseline script is idempotent. If it was interrupted (power loss, terminal crash, etc.), just re-run:

```bash
scripts/apply-mango-baseline --apply --install-packages
```

It skips already-installed packages and already-deployed files, so it is safe to run multiple times.

### Ghostty crashes during `dnf install`

This is a known Ghostty + fontconfig bug: when `dnf` installs packages that rebuild the fontconfig cache, Ghostty (a GTK4 app) crashes with a SEGV in `FcConfigDestroy`.

**Do not run `dnf install` or the baseline script with `--install-packages` inside Ghostty.**

Use one of these instead:
- SSH into the machine
- Konsole, Kitty, or any non-GTK4 terminal
- A TTY (Ctrl+Alt+F3)

The baseline script now detects Ghostty and refuses to install packages if it is the parent terminal.

---

## Repo layout

```text
configs/     Files deployed by the workstation baseline
scripts/     Install, health, restore, and test scripts
tools/       The DMS Mango Settings app source
docs/        Installation notes, architecture, investigations, workarounds
profiles/    Fedora profile notes and package decisions
plans/       Project plans
notes/       Field notes from testing and debugging
tests/       Manual verification matrix
```

---

## Current state

This repo is already useful and installable, but still evolving.

The core workflow is now real:

- install Mango
- install DMS
- clone repo
- apply baseline / run first-run setup
- export DMS theme once
- verify

That is the main purpose of this project.
