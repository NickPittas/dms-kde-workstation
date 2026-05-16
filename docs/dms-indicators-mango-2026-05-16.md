# DMS indicators under Mango

Date: 2026-05-16

## User report

DMS under Mango shows Bluetooth, audio, network, notifications, clipboard, and language correctly.

Missing compared with niri/KDE expectation:

- Dropbox service/startup visibility
- Sunshine service/startup visibility

RustDesk appears because it registers a StatusNotifier item.

## Findings

Autostart is not the problem:

- Dropbox service is active.
- Sunshine service is active.
- Vicinae service is active.

Tray visibility is the problem:

- DMS system tray uses Quickshell `SystemTray.items` / StatusNotifier.
- RustDesk registers as StatusNotifier and appears.
- Dropbox/Sunshine do not appear as StatusNotifier items in the current Mango/DMS session.

DMS privacy indicators are separate and are based on PipeWire/niri checks. `PrivacyService.qml` has an explicit niri shortcut:

```qml
if (CompositorService.isNiri && NiriService.hasActiveCast) {
    return true
}
```

For Mango, generic PipeWire detection remains, but niri-specific active cast detection does not apply.

## Temporary fix/prototype

Created a synthetic StatusNotifier item:

```text
~/.local/bin/dms-workstation-service-indicator
```

It registers one tray item:

```text
Workstation Services
```

Tooltip shows:

```text
Dropbox:on/off  Sunshine:on/off  Vicinae:on/off  Portal:on/off
```

Click action opens Mango Workstation Menu.

Right-click action opens service status in Ghostty.

Autostart added to Mango config:

```text
exec-once=/home/npittas/.local/bin/dms-workstation-service-indicator
```

## Project implication

Long-term DMS should not rely only on third-party tray icons for workstation services.

DMS KDE Workstation should have a first-class Service Indicators widget/plugin showing:

- Dropbox running/sync state if available
- Sunshine running
- RustDesk running
- Vicinae running
- portals running
- KDE Connect running

The synthetic SNI script is only a prototype proving that DMS tray can display a generic service-status item under Mango.

## Manual visual result

User confirmed the `Workstation Services` indicator is visible in the DMS tray under Mango.

Result: **PASS**.
