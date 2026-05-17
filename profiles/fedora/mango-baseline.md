# Fedora Mango baseline profile

Date: 2026-05-16
Status: Automated installer/profile from validated reference machine

## Purpose

Reproduce the current working DMS KDE Workstation Mango baseline on Fedora with one primary installer path:

```text
scripts/apply-mango-baseline --apply --install-packages
```

This profile is based on the reference machine where the following were manually tested:

- Mango session starts.
- DMS starts with `dms run` from Mango config.
- Dolphin -> Nuke drag-and-drop works.
- Dolphin -> Blender drag-and-drop works.
- KDE/Qt apps theme correctly after DMS theme export.
- Alt+Shift toggles English/Greek keyboard layouts.
- grim/slurp/swappy screenshot workflow works.
- Portals are active under Mango with the user-unit override.
- The synthetic `Workstation Services` DMS tray indicator is visible.

## Package groups

### Core compositor/session

```text
mangowm
```

Evaluation install source used on Fedora 44:

```text
sudo dnf install -y --nogpgcheck --repofrompath 'terra,https://repos.fyralabs.com/terra$releasever' mangowm
```

The profile should not permanently enable Terra unless that becomes a deliberate packaging decision.

### DMS/runtime helpers

DMS itself is managed separately. The profile assumes `dms` and `quickshell` are already installed.

Required/expected commands:

```text
dms
quickshell
mango
mmsg
fuzzel
wl-copy
```

### Portals

```text
xdg-desktop-portal
xdg-desktop-portal-wlr
xdg-desktop-portal-gtk
xdg-desktop-portal-kde   # optional/experimental outside Plasma
```

Current working Mango baseline uses wlr + gtk portal services and a user override for the core portal service.

### KDE/Qt workstation apps

```text
dolphin
kate
okular
gwenview
ark
kcalc
filelight
kwalletmanager5
plasma-discover
kde-partitionmanager
```

### Qt/GTK theme bridge

```text
qt5ct
qt6ct-kde
```

The profile also deploys:

```text
~/.config/environment.d/90-dms-kde-qt.conf
```

and Mango starts DMS with explicit:

```text
QT_QPA_PLATFORMTHEME=qt6ct
QT_QPA_PLATFORMTHEME_QT6=qt6ct
```

After installing, use DMS Theme/Colors to re-export baseline GTK3/4 and QT5/6 configs once.

### Admin/helper tools

```text
nm-connection-editor
blueman
pavucontrol
qpwgraph
firewall-config
system-config-printer
gparted
flatseal
```

### Screenshots/recording

```text
grim
slurp
swappy
wf-recorder
wl-clipboard
```

Spectacle is not the default in this non-Plasma session.

## Config files deployed by profile

```text
~/.config/mango/config.conf
~/.config/systemd/user/xdg-desktop-portal.service
~/.config/xdg-desktop-portal/mango-portals.conf
~/.config/mimeapps.list
~/.config/environment.d/90-dms-kde-qt.conf
~/.local/bin/dms-region-screenshot-edit
~/.local/bin/dms-full-screenshot-edit
~/.local/bin/dms-region-screenshot-copy
~/.local/bin/mango-workstation-menu
~/.local/bin/dms-workstation-service-indicator
~/.local/share/applications/dms-region-screenshot-edit.desktop
~/.local/share/applications/dms-full-screenshot-edit.desktop
~/.local/share/applications/dms-region-screenshot-copy.desktop
~/.local/share/applications/dms-mango-settings.desktop
~/.config/autostart/dms-mango-settings.desktop
```

## Flatpak overrides

Obsidian DnD fix:

```text
flatpak override --user --socket=wayland --env=OBSIDIAN_USE_WAYLAND=1 md.obsidian.Obsidian
```

Only apply if Obsidian is installed.

## Post-apply actions

```text
systemctl --user daemon-reload
systemctl --user restart xdg-desktop-portal.service xdg-desktop-portal-wlr.service xdg-desktop-portal-gtk.service
```

Then log out/in or start a Mango session.

## Verification

Run:

```text
scripts/dms-workstation-health
```

Manual checks:

- DMS bar appears.
- Workstation Services indicator appears.
- Alt+Shift toggles US/Greek.
- Dolphin -> Nuke DnD works.
- Dolphin -> Blender DnD works.
- Region screenshot opens Swappy with dark theme.
- Zen upload/download uses a working file chooser.
- KDE apps open with the DMS-exported theme.

## Safety

The installer/profile script must:

- default to dry-run,
- require `--apply` before writing files,
- create timestamped backups before overwriting user configs,
- avoid permanent repo changes unless explicitly requested,
- print verification steps after applying.

## 2026-05-16 hardening additions

The Mango baseline now includes the additive post-startup helper, DMS launch overrides, and category-backed startup config:

- `~/.local/bin/dms-mango-post-startup`
- `~/.local/bin/apply-dms-launch-overrides`
- `~/.config/dms-kde-workstation/startup.json`

Purpose:

- wait for DMS/Quickshell StatusNotifierWatcher
- wait for tray settle
- launch startup apps from `~/.config/autostart/*.desktop` after the UI is ready
- ensure `xembedsniproxy`
- restart only configured tray-ready services after tray infrastructure is ready
- merge DMS Dolphin launch override so dock launches use qt6ct env correctly

This avoids putting Dropbox/Sunshine restart logic directly in Mango config and avoids taking over DMS startup ownership.

Restore support:

- `scripts/restore-mango-baseline` now includes the helper and startup JSON in managed files.

Verification:

- `scripts/test-mango-settings-smoke` compiles and offscreen-launches the settings app.
- `scripts/dms-workstation-health` checks that the helper and startup JSON are present.
