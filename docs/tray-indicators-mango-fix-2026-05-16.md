# Mango real tray/status indicator fix

Date: 2026-05-16

## Problem

Dropbox and Sunshine were running under Mango but did not show real tray/status icons in DMS.

RustDesk did show, proving DMS/Quickshell StatusNotifier support was working.

## Root cause found

The apps were not failing because DMS needed a replacement app. They were failing because tray-sensitive services inherited stale/incorrect session environment.

Evidence:

- `org.kde.StatusNotifierWatcher` initially listed only RustDesk and the synthetic Workstation Services item.
- Dropbox process environment showed stale niri values and no usable display variables:

```text
XDG_SESSION_DESKTOP=niri
(no DISPLAY)
(no WAYLAND_DISPLAY)
```

- Sunshine log showed:

```text
Environment variable WAYLAND_DISPLAY has not been defined
Failed to create system tray
System tray is not initialized
```

- `/etc/xdg/autostart/xembedsniproxy.desktop` exists but has:

```text
OnlyShowIn=KDE;
```

So the KDE XEmbed-to-SNI bridge does not automatically start in Mango.

## Runtime fix tested

Ran:

```bash
systemctl --user import-environment DISPLAY WAYLAND_DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE DBUS_SESSION_BUS_ADDRESS XDG_DATA_DIRS

dbus-update-activation-environment --systemd DISPLAY WAYLAND_DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE DBUS_SESSION_BUS_ADDRESS XDG_DATA_DIRS

pgrep -x xembedsniproxy >/dev/null || xembedsniproxy &

systemctl --user restart dropbox.service app-dev.lizardbyte.app.Sunshine.service
```

After restart, real StatusNotifier items appeared:

```text
:.../org/ayatana/NotificationItem/dropbox_client_...
:.../org/ayatana/NotificationItem/trayid...
```

Sunshine log changed to:

```text
Starting system tray
System tray created
```

## Persistent Mango config fix

Updated `~/.config/mango/config.conf`:

```text
exec-once=systemctl --user import-environment WAYLAND_DISPLAY DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE DBUS_SESSION_BUS_ADDRESS XDG_DATA_DIRS QT_QPA_PLATFORM QT_QPA_PLATFORMTHEME QT_QPA_PLATFORMTHEME_QT6 ELECTRON_OZONE_PLATFORM_HINT
exec-once=dbus-update-activation-environment --systemd WAYLAND_DISPLAY DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE DBUS_SESSION_BUS_ADDRESS XDG_DATA_DIRS QT_QPA_PLATFORM QT_QPA_PLATFORMTHEME QT_QPA_PLATFORMTHEME_QT6 ELECTRON_OZONE_PLATFORM_HINT
exec-once=pgrep -x xembedsniproxy >/dev/null || xembedsniproxy

# Restart tray-sensitive services so they inherit the current Mango DISPLAY/WAYLAND environment.
exec-once=systemctl --user restart dropbox.service
exec-once=systemctl --user restart app-dev.lizardbyte.app.Sunshine.service
```

Also copied to project baseline:

```text
configs/mango/config.conf.working-20260516
```

## Conclusion

The missing app icons were caused by environment/session startup ordering and the KDE-only XEmbed bridge autostart rule, not by DMS needing fake replacement indicators.

The synthetic Workstation Services indicator remains useful for service health, but Dropbox/Sunshine can expose real tray icons when started with the correct Mango environment.

## Follow-up environment audit

After fixing Dropbox/Sunshine, audited likely GUI/tray processes.

OK with current Mango env:

- DMS / Quickshell
- Vicinae
- portals
- xembedsniproxy
- Dropbox
- Workstation service indicator

Suspicious/wrong env:

- RustDesk server/tray launched by the root RustDesk service:

```text
DISPLAY=:0
XDG_SESSION_CLASS=background
XDG_SESSION_TYPE=unspecified
missing WAYLAND_DISPLAY
missing XDG_CURRENT_DESKTOP
```

RustDesk still registered a tray item, but it is not running under the current Mango session env. This likely comes from RustDesk's privileged/background service rather than Mango autostart.

Also updated current user-manager env to match the active Mango session:

```text
XDG_SESSION_ID=53
XDG_SESSION_PATH=/org/freedesktop/DisplayManager/Session4
XDG_SESSION_CLASS=user
XDG_SESSION_TYPE=wayland
XDG_CURRENT_DESKTOP=mango
XDG_SESSION_DESKTOP=mango:wlroots
DISPLAY=:1
WAYLAND_DISPLAY=wayland-0
```
