# MangoWM evaluation

Date: 2026-05-16

## Why

niri is currently a blocker for professional creative DnD workflows:

- Dolphin -> Blender fails under niri, works under KDE.
- Dolphin -> Nuke fails under niri, works under KDE.

MangoWM is worth evaluating because:

- DMS supports MangoWC/MangoWM.
- Mango claims strong XWayland support.
- It does not use niri's scrollable-column model, which may be interacting badly with DnD.

## Installation

Installed for evaluation using Terra as a temporary repo source, not as a permanent repo package:

```bash
sudo dnf install -y --nogpgcheck --repofrompath 'terra,https://repos.fyralabs.com/terra$releasever' mangowm
```

Installed packages:

```text
mangowm-0.13.0-1.fc44.x86_64
scenefx-0.4.1-1.fc44.x86_64
wlroots0.19-0.19.3-1.fc44.x86_64
libliftoff
xcb-util-errors
```

Mango session file exists:

```text
/usr/share/wayland-sessions/mango.desktop
```

DMS doctor detects Mango:

```text
mangowc 0.13.0
```

## User config

Created:

```text
~/.config/mango/config.conf
```

Based on:

```text
/etc/mango/config.conf
```

Changes added:

```text
exec-once=systemctl --user import-environment WAYLAND_DISPLAY DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP QT_QPA_PLATFORM QT_QPA_PLATFORMTHEME QT_QPA_PLATFORMTHEME_QT6 ELECTRON_OZONE_PLATFORM_HINT
exec-once=dbus-update-activation-environment --systemd WAYLAND_DISPLAY DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP QT_QPA_PLATFORM QT_QPA_PLATFORMTHEME QT_QPA_PLATFORMTHEME_QT6 ELECTRON_OZONE_PLATFORM_HINT
exec-once=systemctl --user start dms.service
```

Changed default unavailable tools:

```text
Alt+space -> vicinae toggle
Alt+Return -> ghostty
```

Added DMS workstation app binds:

```text
Super+E -> Dolphin with qt6ct env
Super+B -> Zen Browser
Print -> region screenshot into Swappy
Ctrl+Print -> full screenshot into Swappy
Shift+Print -> region screenshot to clipboard
```

Changed risky default quit bind:

```text
Super+Shift+M -> quit Mango
```

instead of the original `Super+M`.

## Login test plan

At login screen:

1. Choose session: `Mango`.
2. Log in.
3. Confirm DMS appears.
4. If no DMS, press `Alt+Return` for Ghostty and run:

```bash
dms doctor
systemctl --user status dms.service
systemctl --user start dms.service
```

## Critical tests

### Must pass for project viability

- Dolphin -> Blender DnD works.
- Dolphin -> Nuke DnD works.

### Other checks

- DMS panel appears.
- Alt+Space opens vicinae.
- Alt+Return opens Ghostty.
- Super+E opens Dolphin themed correctly.
- Zen upload/download works.
- Obsidian DnD still works.
- Print screenshot workflow still works.
- Display remains stable at 4K60.

## Caveats

DMS supports Mango, but this may not be as polished as niri. Known online issues include:

- DMS doctor/name mismatch history between `mangowc` and `mango`.
- DMS output configuration issues on MangoWC reported upstream.
- DMS keybind issues reported by some users.

This is an evaluation track only. niri remains installed and available.
