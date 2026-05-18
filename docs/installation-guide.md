# DMS KDE Workstation — Fedora 44 KDE → Mango + DMS + Settings App

## Goal

Start from **Fedora 44 KDE Plasma** and end with:

- **MangoWM** session
- **DMS** shell
- **DMS Mango Settings** app
- working **KDE/Qt theming**
- working **tray icons**
- working **startup apps launched after the UI appears**
- working **Dolphin → Nuke/Blender DnD**

The installer path is now **automation-first**.

---

## What is automatic now

`scripts/apply-mango-baseline` now installs/deploys:

- Mango config
- portal override + portal config
- mime defaults baseline
- qt6ct environment file
- screenshot scripts + desktop files
- workstation menu
- service indicator
- `dms-mango-post-startup`
- startup config JSON
- current `dms-mango-settings` app
- settings app desktop file
- settings app autostart entry
- optional targeted workarounds can still be applied later if a specific launch path misbehaves on your machine

It also uses direct file writes via `tee`, not `cp`, for deployed files.

---

## What is still manual

Only these parts remain manual:

1. **Install DMS** if it is not already installed
2. **Run DMS Theme/Colors export once** after install
3. **Log into Mango** from SDDM
4. Optional: **enable SDDM autologin**

Everything else should be handled by the baseline deployer and the settings app.

---

## 1. Prerequisites

### Fedora base

Start from:

- Fedora 44
- KDE Plasma installed
- normal user with sudo

### DMS

This profile assumes `dms` and `quickshell` already exist.

Verify:

```bash
command -v dms
command -v quickshell
```

If either is missing, install DMS first using your normal DMS install path.

### Project checkout

```bash
git clone <repo-url> ~/dms-kde-workstation
cd ~/dms-kde-workstation
```

---

## 2. Preferred install path

### Dry-run first

```bash
scripts/apply-mango-baseline --install-packages
```

### Real apply

Do **not** run package installation inside Ghostty. Use SSH, Konsole, Kitty, or a TTY because Ghostty can crash while `dnf` rebuilds fontconfig caches.

```bash
scripts/apply-mango-baseline --apply --install-packages
```

If `dms-mango-settings` later fails with `No module named 'PySide6'`, install the missing dependency and re-run the baseline:

```bash
sudo dnf install -y python3-pyside6
scripts/apply-mango-baseline --apply --install-packages
```

Optional Obsidian Wayland/DnD fix:

```bash
scripts/apply-mango-baseline --apply --install-packages --obsidian-override
```

This will:

- install Mango and approved Fedora packages, including `python3-pyside6` for the settings app
- deploy the working Mango baseline
- make DMS start with explicit `qt6ct` env
- install the settings app
- make the settings app autostart
- install the post-startup helper that launches startup apps after the tray is ready

---

## 3. First login into Mango

At SDDM, choose the **Mango** session and log in.

Expected result:

- DMS bar appears
- settings app autostarts
- one settings tray icon appears
- Dropbox/Sunshine/KRFB tray icons appear if installed

---

## 4. One-time DMS theme export

This is still required once after install.

Open:

- **DMS → Settings → Theme/Colors**

Then export:

- GTK3
- GTK4
- QT5
- QT6

Why this is still manual:

- DMS owns the Matugen/theme export flow
- the exported files depend on your active DMS theme state

After this, KDE/Qt apps like Ark, Okular, Dolphin, Gwenview should use the dark theme.

---

## 5. Reboot once

```bash
systemctl reboot
```

This verifies the real startup path.

---

## 6. Verify

Run:

```bash
scripts/dms-workstation-health
```

Then manually verify:

- DMS bar is visible
- settings app autostarted
- launching settings again does **not** create a second tray icon
- Alt+Shift toggles `us` / `gr`
- Ark/Okular/Dolphin are dark themed
- Dolphin launched from the DMS dock is also dark themed (no checkerboard rows)
- Dolphin → Nuke DnD works
- Dolphin → Blender DnD works
- screenshot actions open Swappy / copy image
- file chooser portals work

---

## Startup apps: how they work now

Under Mango, relying on KDE autostart behavior is not enough.

So our design is:

1. User adds apps from **Settings → Startup**
2. App stores `.desktop` entries in `~/.config/autostart/`
3. `dms-mango-post-startup` waits for DMS tray/UI
4. Then it launches those startup apps

This is intentional.

It gives us Windows-like behavior:

- log in
- UI appears
- selected apps launch after the desktop is ready

That is the supported startup model for this workstation.

---

## Important implementation details

### DMS must start with explicit qt6ct env

The working Mango config uses:

```ini
exec-once=env QT_QPA_PLATFORMTHEME=qt6ct QT_QPA_PLATFORMTHEME_QT6=qt6ct dms run
```

This is required because otherwise DMS-launched KDE/Qt apps can inherit `gtk3` and appear white.

### Dolphin from the DMS dock may need a targeted DMS app override

The DMS dock can launch apps through its own launcher pipeline. On one machine, Dolphin needed:

```text
QT_QPA_PLATFORMTHEME=qt6ct
QT_QPA_PLATFORMTHEME_QT6=qt6ct
```

That is now treated as a targeted workaround, not a universal baseline action. The baseline installer does **not** auto-apply that override anymore.

### Post-startup helper owns startup app launch timing

The helper:

- waits for `StatusNotifierWatcher`
- waits for tray settle
- launches autostart apps
- restarts tray-sensitive services

This is why tray icons and startup apps work more reliably here than with plain Mango/KDE assumptions.

---

## Optional: SDDM autologin

Autologin is supported but not required for the baseline install.

The settings app Login page can manage it, with:

- PolicyKit prompt
- config consolidation
- rollback/backup support

This is intentionally separate from the base installer.

---

## Recovery

Restore script:

```bash
scripts/restore-mango-baseline
```

Health check:

```bash
scripts/dms-workstation-health
```

---

## Short version

Safe order:

1. stay in your current working KDE/niri session
2. install DMS
3. install Mango
4. run:

```bash
cd ~/dms-kde-workstation
scripts/apply-mango-baseline --apply --install-packages
scripts/test-first-mango-readiness
```

5. only if readiness says `READY`, log into Mango
6. run DMS Theme/Colors export once
7. reboot once
8. verify

That is now the intended install path.
