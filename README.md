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

## Main install path

If **DMS is already installed**, the main path is:

```bash
git clone git@github.com:NickPittas/dms-kde-workstation.git
cd dms-kde-workstation
scripts/apply-mango-baseline --apply --install-packages
```

Then:

1. log into the **Mango** session
2. open **DMS → Settings → Theme/Colors**
3. export **GTK3 / GTK4 / QT5 / QT6** once
4. reboot once
5. run:

```bash
scripts/dms-workstation-health
```

---

## Fresh clone: what to do

### Before

Make sure you have:

- Fedora 44
- KDE Plasma installed
- a normal user with sudo
- DMS installed already

Verify DMS:

```bash
command -v dms
command -v quickshell
```

If those are missing, install DMS first using your normal DMS install method.

### Clone

```bash
git clone git@github.com:NickPittas/dms-kde-workstation.git
cd dms-kde-workstation
```

### Preview what will happen

```bash
scripts/apply-mango-baseline --install-packages
```

This is dry-run by default.

### Apply it for real

```bash
scripts/apply-mango-baseline --apply --install-packages
```

Optional Obsidian Wayland/DnD fix:

```bash
scripts/apply-mango-baseline --apply --install-packages --obsidian-override
```

### After

- choose the **Mango** session in SDDM
- log in
- run the one-time DMS theme export
- reboot once
- run the health check

---

## First Run Setup in the app

The settings app now includes a **First Run Setup** page.

Goal:

1. install Mango
2. install DMS
3. clone this repo
4. run **DMS Mango Settings**
5. open **First Run Setup**
6. click **Apply Setup**

That page checks and applies the user-level workstation baseline automatically.

### It handles things like

- Mango config deployment
- DMS startup line under Mango
- explicit `qt6ct` launch environment for DMS
- portal override + portal config
- screenshot toolchain install
- settings app install/autostart
- post-startup helper install
- startup app support after the UI appears
- DMS Dolphin launch override for proper dock launches

### Still manual

These are still intentionally manual:

- installing Mango itself
- installing DMS itself
- one-time DMS Theme/Colors export
- optional SDDM autologin setup

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
- **DMS dock** needed a DMS app override

So the baseline now applies a DMS `appOverrides` entry for Dolphin with:

```text
QT_QPA_PLATFORMTHEME=qt6ct
QT_QPA_PLATFORMTHEME_QT6=qt6ct
```

This prevents the checkerboard / wrong-row-color issue when Dolphin is launched from the DMS dock.

### DMS under Mango

DMS must be launched under Mango with explicit Qt theming env:

```ini
exec-once=env QT_QPA_PLATFORMTHEME=qt6ct QT_QPA_PLATFORMTHEME_QT6=qt6ct dms run
```

Without that, DMS-launched Qt/KDE apps can come up white or incorrectly themed.

---

## Scripts you will actually use

### Install / apply baseline

```bash
scripts/apply-mango-baseline --apply --install-packages
```

### Health check

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

The fix is a DMS app override for Dolphin with:

```text
QT_QPA_PLATFORMTHEME=qt6ct
QT_QPA_PLATFORMTHEME_QT6=qt6ct
```

This repo now applies that automatically in the baseline.

### Tray icons are missing after login

Check:

- `~/.local/bin/dms-mango-post-startup`
- `~/.config/dms-kde-workstation/startup.json`
- `~/.local/state/dms-kde-workstation/mango-post-startup.log`

The post-startup helper is responsible for delayed startup when DMS tray is ready.

### Startup apps do not appear on login

This project intentionally does **not** rely on plain KDE assumptions.

Startup apps are launched by the post-startup helper after the UI is ready.
Use the app’s **Startup** page.

### Ghostty transparency/blur under Mango behaves differently than under niri

This is still not fully normalized/documented as a clean baseline behavior.
Mango per-window opacity works, but Ghostty’s own transparency/blur path is not yet treated as fully solved in this repo.

### Screenshot selection UI behaves strangely

This repo uses `grim + slurp + swappy`, and the selection overlay was tuned to reduce blur/fill artifacts under Mango.
If screenshot output is correct but selection preview looks odd, check the installed region screenshot scripts in `~/.local/bin/`.

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
