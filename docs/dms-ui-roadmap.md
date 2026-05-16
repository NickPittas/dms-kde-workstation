# DMS UI roadmap

Ideas for DMS changes after the external stack is proven.

## Stage 1: Settings portal, not full reimplementation

Add a DMS settings area called **Workstation** with tiles:

- Appearance
- Portals
- Apps & Menu
- Default Apps
- Startup
- Network
- Bluetooth
- Audio
- Displays
- Remote Desktop
- Flatpak Permissions
- Secrets
- System Health
- Recovery

Each tile can initially:

- show status,
- open an existing app,
- show install command if missing,
- link to docs,
- run safe repair scripts later.

## Stage 2: DMS Health Check UI

Expose results from `scripts/dms-workstation-health`.

Checks:

- required apps installed
- portal config valid
- portal services running
- polkit agent running
- keyring/secrets service running
- XWayland available
- D-Bus environment imported
- Qt theme configured
- GTK fallback configured
- fuzzel config exists
- Flatseal installed
- broken desktop entries

## Stage 3: Actual settings panels

Build native DMS panels for:

- portal selection
- theme bridge
- app/menu entries
- default terminal/file manager/browser
- startup services
- remote desktop presets
- recovery snapshots

## Stage 4: Installer integration

The installer should:

- install approved packages,
- copy config templates,
- enable user services,
- run health check,
- show remaining manual actions.
