# Startup ownership under Mango

Date: 2026-05-16
Status: Active design/implementation note

## Why this document exists

After reboot, Dropbox/Sunshine tray icons did not appear until services were restarted manually. The fix must not duplicate or fight DMS startup. This document records ownership so the future installer can reproduce the correct sequence safely.

## DMS-owned responsibilities

DMS should continue to own:

- DMS shell process (`dms run`).
- Quickshell/DMS bar and control center.
- StatusNotifierWatcher/Host via Quickshell `SystemTray` service.
- DMS tray rendering (`SystemTrayBar.qml`).
- DMS theme/Matugen export.
- DMS widgets/notifications/clipboard where applicable.

Important: Fedora's packaged `dms.service` depends on `graphical-session.target`:

```ini
PartOf=graphical-session.target
After=graphical-session.target
Requisite=graphical-session.target
WantedBy=graphical-session.target
```

Mango did not activate that target in testing, so the profile starts DMS directly:

```text
exec-once=dms run
```

Do not create another service that also starts DMS unless Mango begins activating `graphical-session.target` correctly.

## Mango-profile-owned responsibilities

The Mango workstation profile owns only gaps around Mango session setup:

- Import current Mango display/session environment into systemd and D-Bus activation.
- Start portal services/overrides needed because Fedora's stock portal unit also expects `graphical-session.target`.
- Start `xembedsniproxy` because its desktop autostart file has `OnlyShowIn=KDE;`, so it does not start automatically in Mango.
- Start/restart user-selected tray-sensitive services only after DMS/StatusNotifierWatcher is ready.
- Verify real tray registration for those services.

## User-owned responsibilities

The user/profile settings own the list of apps/services to start:

- normal startup apps,
- tray-ready startup services,
- systemd user services,
- advanced Mango `exec-once` commands.

The baseline may ship recommended entries, but they must be removable in the GUI.

## Problem found

Dropbox/Sunshine were running but missing real tray icons because they were started before inheriting the current Mango display/session environment or before tray infrastructure was ready.

Evidence:

- Dropbox previously had stale `XDG_SESSION_DESKTOP=niri` and missing display variables.
- Sunshine logged:

```text
WAYLAND_DISPLAY has not been defined
Failed to create system tray
System tray is not initialized
```

- After importing Mango env, starting `xembedsniproxy`, and restarting the services, real StatusNotifier items appeared.

## Correct additive startup model

Mango config should do:

```text
exec-once=env QT_QPA_PLATFORMTHEME=qt6ct QT_QPA_PLATFORMTHEME_QT6=qt6ct dms run
exec-once=systemctl --user start vicinae.service
exec-once=systemctl --user start xdg-desktop-portal-wlr.service xdg-desktop-portal-gtk.service plasma-xdg-desktop-portal-kde.service
exec-once=/home/npittas/.local/bin/dms-mango-post-startup
```

Notes:

- newer Mango guidance warns against keeping redundant `dbus-update-activation-environment` startup lines when Mango already handles runtime session propagation for portals
- `dms.service` must **not** also be enabled for Mango if this `dms run` exec-once path is present

`dms-mango-post-startup` does **not** start DMS. It only waits for DMS/StatusNotifierWatcher and fills Mango-specific gaps.

## Helper responsibilities

`dms-mango-post-startup`:

1. import current session env into systemd and D-Bus activation,
2. wait for `org.kde.StatusNotifierWatcher`,
3. start `xembedsniproxy` if missing,
4. restart configured tray-sensitive user services,
5. start optional helper processes when explicitly configured by the user,
6. log verification output.

## Config file

User-editable config:

```text
~/.config/dms-kde-workstation/startup.json
```

Project baseline:

```text
configs/dms-kde-workstation/startup.json
```

Initial baseline:

```json
{
  "tray_ready_services": [],
  "post_start_commands": [],
  "wait_timeout_seconds": 30
}
```

## Installer implications

The installer/profile should:

- install/copy `dms-mango-post-startup`,
- install default `startup.json` only if absent or after backup,
- update Mango config to call the helper after `dms run`,
- avoid enabling `dms.service` under Mango unless Mango activates `graphical-session.target`,
- keep tray-sensitive apps in config rather than hardcoding them into Mango config.

## Do not duplicate

Do not duplicate these in a helper:

- launching `dms run`,
- creating the StatusNotifierWatcher,
- rendering tray icons,
- DMS theme export.

Those are DMS responsibilities.
