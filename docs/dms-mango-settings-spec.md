# DMS Mango Workstation Settings spec

Date: 2026-05-16
Status: Draft after Mango baseline validation

## Purpose

Provide a real graphical settings surface for the DMS KDE Workstation Mango profile.

The temporary `mango-workstation-menu` proves the needed controls, but it is terminal/TUI-based and not suitable as the final UX. The final settings surface should be either:

1. a native DMS/Quickshell panel, or
2. a companion Qt/Kirigami application launched from DMS.

A native DMS panel is preferred for status, repair actions, and integration with existing DMS theming.

## Design goals

- KDE/Qt-first workstation defaults.
- No config-file editing required for normal changes.
- Every destructive or risky change must create a backup first.
- Settings must be reversible.
- Every section should expose health/status and repair actions.
- The UI should explain which component owns a setting: Mango, DMS, portal, KDE app, Flatpak, systemd user service, or external app.

## Non-goals

- Do not build a complete KDE System Settings clone.
- Do not hide the underlying component names from advanced users.
- Do not make niri the primary workflow again unless Blender/Nuke DnD is fixed there.

## Entry points

Recommended launch points:

- DMS Control Center tile: `Workstation Settings`
- DMS launcher result: `Workstation Settings`
- DMS tray/status item: `Workstation Services`
- Optional desktop entry: `DMS Mango Workstation Settings`

## Main sections

### 1. Overview

Show the current profile state:

- Session: Mango / Wayland
- DMS status
- Portal status
- Active layout
- Keyboard layout
- Important services: Dropbox, Sunshine, RustDesk, Vicinae, portals
- DnD baseline status: Blender/Nuke marked as user-confirmed working
- Health check button

Actions:

- Run health check
- Copy health report
- Open logs folder
- Restart DMS
- Reload Mango config

### 2. Layout and windows

Controls:

- Active layout:
  - Scroller
  - Monocle
  - Tile
  - Dwindle
- Default layout for new tags
- Focus navigation style
- Mouse wheel navigation behavior
- Gaps/borders if Mango supports runtime changes

Window actions:

- Close focused window
- Minimize focused window
- Restore minimized windows
- Toggle maximize
- Toggle floating
- Toggle fullscreen

Known validated bindings:

```text
Super+Q           close focused
Super+M           minimize focused
Super+Shift+M     restore minimized
Super+Shift+Enter toggle maximize
Super+Shift+Space toggle floating
Super+Shift+F     toggle fullscreen
```

Validated scroller navigation:

```text
Super+Wheel Down  focusstack next
Super+Wheel Up    focusstack prev
Super+Wheel Left  focusdir left
Super+Wheel Right focusdir right
```

### 3. Keyboard and input

Controls:

- Keyboard layouts
- Layout toggle binding
- Direct layout selection bindings
- Pointer/touchpad options if Mango exposes them

Approved baseline:

```text
xkb_rules_layout=us,gr
Alt+Shift -> toggle English/Greek
Super+Ctrl+1 -> English
Super+Ctrl+2 -> Greek
```

UI requirements:

- Must allow adding/removing layouts.
- Must preserve the approved Alt+Shift toggle.
- Must warn before replacing working keyboard config.

### 4. Screenshots and recording

Approved stack:

- `grim`
- `slurp`
- `swappy`
- `wf-recorder`

Controls:

- Region screenshot to Swappy
- Full screenshot to Swappy
- Region screenshot to clipboard
- Recording output folder
- Open screenshot folder

Rejected for this profile:

- Spectacle as default screenshot tool, because it expects Plasma in this non-Plasma session.

Validated theme condition:

```text
GTK_THEME=catppuccin-macchiato-blue-standard+default
```

or equivalent DMS-exported dark GTK theme when launching Swappy.

### 5. Portals

Show status for:

- `xdg-desktop-portal.service`
- `xdg-desktop-portal-wlr.service`
- `xdg-desktop-portal-gtk.service`
- optional `xdg-desktop-portal-kde.service`

Current Mango requirement:

- Fedora's stock portal unit depends on `graphical-session.target`.
- Mango did not activate that target in testing.
- A user override is currently required.

Files:

```text
~/.config/systemd/user/xdg-desktop-portal.service
~/.config/xdg-desktop-portal/mango-portals.conf
```

Actions:

- Test file picker
- Restart portals
- Apply Mango portal override
- Restore previous portal config
- Show active backend preference

### 6. Theme bridge

Controls/status:

- DMS theme export status
- GTK3 config present
- GTK4 config present
- Qt5ct config present
- Qt6ct config present
- `custom_palette=true` for Qt5/Qt6

Important workflow:

1. Install `qt5ct` and `qt6ct-kde`.
2. Enable DMS Qt theming.
3. Re-export DMS baseline GTK3/4 and QT5/6 configs from DMS Theme/Colors.

This fixed KDE app theming and Dolphin alternating-row colors.

Actions:

- Open DMS theme settings
- Validate theme files
- Backup theme files
- Restore last known good theme snapshot

### 7. Default apps

Approved defaults:

```text
Folders -> Dolphin
PDFs -> Okular
Images -> Gwenview
Archives -> Ark
Text/code -> Zed
HTTP/HTTPS -> Zen Browser
```

Controls:

- Show current xdg-mime associations.
- Apply approved workstation defaults.
- Backup/restore `mimeapps.list`.

### 8. Services and autostart

Show service status for:

- Dropbox
- Sunshine
- RustDesk
- Vicinae
- DMS
- portals
- PipeWire
- WirePlumber
- KWallet/keyring
- KDE Connect if installed

Actions:

- Start/stop/restart each user service
- Enable/disable autostart for profile-managed services
- Open logs
- Open service status

Current validated prototype:

```text
~/.local/bin/dms-workstation-service-indicator
```

This synthetic StatusNotifier item is visible in the DMS tray under Mango and reports Dropbox/Sunshine/Vicinae/Portal state.

Long-term this should become a native DMS widget/plugin.

### 9. Creative app compatibility

Required tests:

- Dolphin -> Nuke drag-and-drop
- Dolphin -> Blender drag-and-drop
- Dolphin -> Obsidian drag-and-drop
- Dolphin -> Zed drag-and-drop

Current result:

- Mango: Blender/Nuke DnD user-confirmed working.
- niri: Blender/Nuke DnD failed and remains a blocker.

Actions:

- Open DnD test checklist
- Record pass/fail result
- Show known app-specific fixes

Obsidian Flatpak fix:

```text
flatpak override --user --socket=wayland --env=OBSIDIAN_USE_WAYLAND=1 md.obsidian.Obsidian
```

### 10. External tools launcher

Expose approved GUI tools:

- Dolphin
- Kate
- Okular
- Gwenview
- Ark
- Filelight
- KWalletManager
- Plasma Discover
- KDE Partition Manager
- Flatseal
- Blueman
- pavucontrol
- qpwgraph
- system-config-printer
- GParted

Each tool row should show:

- installed/missing
- launch button
- package name
- why it exists in this profile

## Implementation options

### Option A: DMS/Quickshell-native panel

Pros:

- Best visual integration.
- Reuses DMS theme and control-center patterns.
- Can integrate directly with DMS services and notifications.

Cons:

- More DMS/QML-specific implementation work.
- External command execution and file editing must be carefully wrapped.

### Option B: Qt/Kirigami companion app

Pros:

- KDE/Qt-native.
- Easier to build forms, lists, backups, logs, and dialogs.
- Better long-term for complex settings.

Cons:

- Separate app visual identity unless themed carefully.
- Needs packaging and desktop integration.

### Recommended path

Start with a DMS/Quickshell-native status/settings panel for:

- Overview
- Services
- Portals
- Theme bridge
- Shortcuts to external GUI tools

If settings become too complex, move editing-heavy pages to a Qt/Kirigami companion app and keep DMS as the launcher/status surface.

## Minimal viable version

MVP should include:

1. Overview health page.
2. Service indicators and controls.
3. Portal status and repair.
4. Theme bridge validation.
5. Default apps validation/apply.
6. Links to Mango layout/keyboard controls.
7. Links to approved external tools.

## Safety requirements

Before modifying any file, create timestamped backups for:

```text
~/.config/mango/config.conf
~/.config/xdg-desktop-portal/mango-portals.conf
~/.config/systemd/user/xdg-desktop-portal.service
~/.config/mimeapps.list
~/.config/qt5ct/qt5ct.conf
~/.config/qt6ct/qt6ct.conf
~/.config/gtk-3.0/settings.ini
~/.config/gtk-4.0/settings.ini
```

All repair actions must show:

- what file/service will change,
- backup location,
- command to undo if available,
- verification result after applying.

## Open questions

- Should the final editor write Mango config directly or use `mmsg` where possible?
- Can DMS expose a safe generic config-backup/patch helper?
- Should the service indicator remain StatusNotifier-based or become a dedicated DMS bar widget?
- How much of this belongs upstream in DMS vs this workstation profile?

## Prototype 1 implementation

Created first Qt/PySide6 GUI prototype:

```text
~/.local/bin/dms-mango-settings
~/.local/share/applications/dms-mango-settings.desktop
```

Project copies:

```text
tools/dms-mango-settings.py
configs/scripts/dms-mango-settings
configs/applications/dms-mango-settings.desktop
```

Current prototype pages:

- Overview/status
- Layout and appearance
- Keyboard layouts
- User service controls
- External tool launchers

Current safe-write behavior:

- backs up `~/.config/mango/config.conf` before writes
- edits only known key/value and known keyboard/tagrule lines
- requests Mango reload after saving via `mmsg -s -d reload_config`

Temporary menu integration:

- `mango-workstation-menu` now includes `Open GUI Settings` as the first item.

## Prototype 2 implementation

User feedback: Prototype 1 exposed too few Mango settings and hard-coded reference-machine startup apps. That violated the KDE-like settings goal.

Added Prototype 2 pages/capabilities:

- `Input` page:
  - focus follows mouse
  - cursor warp
  - focus across monitors/tags
  - tile dragging options
  - tap-to-click
  - tap-and-drag
  - drag lock
  - trackpad/mouse natural scrolling
  - disable while typing
  - left-handed mode
  - middle-button emulation
- `Startup` page:
  - list Mango `exec-once` startup commands
  - add arbitrary startup commands
  - remove selected startup commands
  - presets for Dropbox, Sunshine, KDE Connect, and Workstation indicator
  - link to KDE Autostart settings / autostart folder for normal `.desktop` app startup
- `Login` page:
  - display manager detection
  - SDDM autologin status
  - enable/disable DMS-managed SDDM Mango autologin file with admin permission

Important policy correction:

- The baseline may ship with recommended startup entries, but the settings UI must let the user remove or add them.
- Startup apps/services are user preference, not immutable profile law.

## Prototype 3 implementation

User feedback: more Mango-specific settings are required, especially scroller centering.

Added Mango-specific layout controls:

- Scroller structures
- Scroller default proportion
- Scroller single-window proportion
- Center focused window (`scroller_focus_center`)
- Prefer center position (`scroller_prefer_center`)
- Pointer focus at scroller edge (`edge_scroller_pointer_focus`)
- Scroller proportion presets
- Tile/master controls: new window is master, master factor, master count, smart gaps
- Dwindle controls: smart split, drop simple split, manual split, horizontal/vertical split, preserve split

Fixed shortcut issue:

- Removed stale duplicate `Super+Shift+L` bind to `mango-layout-menu`.
- `Super+Shift+L` should now open the general `mango-workstation-menu`, whose first item is `Open GUI Settings`.

Plan reminder:

- The GUI should keep expanding toward the Mango config surface, not stop at a small curated subset.
- Use the markdown spec/startup plan as the source of truth.

## Prototype 4 UI refactor

User feedback: Prototype 1-3 looked like a failed basic forms app and became the limiting factor. The target is visually closer to DMS Settings: left sidebar, dark/accent theme, rounded cards, overflow scrolling, and controls that match the setting type.

Replaced the PySide UI shell with a DMS-inspired layout:

- left navigation sidebar
- scrollable content pages
- rounded settings cards
- accent-green selected navigation
- styled toggle switches
- sliders for numeric ranges
- dropdowns for layout/animation choices
- buttons grouped as action rows

Current left-nav pages:

- Overview
- Layout & Scroller
- Animations & Effects
- Input
- Keyboard
- Startup
- Services
- Login
- Tools

Added/kept Mango-specific controls:

- scroller centering
- scroller proportions
- scroller structures
- default layouts
- tile/master controls
- dwindle controls
- blur/shadow/opacity controls
- animation type dropdowns
- animation duration sliders
- pointer/trackpad controls
- startup add/remove UI
- SDDM autologin helper

This is still a Qt companion app, but the interaction model is now intended to match the DMS settings style rather than a generic form dialog.

## Prototype 5 Backup & Recovery

Added a `Backup & Recovery` page to support safe customization before adding more risky settings.

Capabilities:

- list existing Mango config backups from `~/.local/state/dms-kde-workstation/backups/*/.config/mango/config.conf`
- create a manual checkpoint of the current Mango config
- restore selected backup
- open backups folder in Dolphin
- reset Mango config to project known-working baseline
- export current Mango config as the new project baseline

Safety behavior:

- restore/reset creates a fresh backup of the current config before overwriting it
- Mango reload is requested after restore/reset

This should be expanded later with diff/preview support.

## Prototype 6 Startup Manager v2

Expanded Startup page from a simple Mango `exec-once` list into a KDE-like startup manager with three startup models:

1. **Mango session startup**
   - view `exec-once=` commands
   - add arbitrary command
   - remove selected command
   - presets for Dropbox, Sunshine, KDE Connect, Workstation indicator
   - save/reload Mango config

2. **Application autostart**
   - list `~/.config/autostart/*.desktop`
   - add GUI app from installed `.desktop` launchers
   - enable selected app by setting `Hidden=false`
   - disable selected app by setting `Hidden=true`
   - remove selected autostart entry
   - open autostart folder

3. **User service autostart**
   - list `systemctl --user list-unit-files --type=service`
   - show enablement state and active/stopped status
   - filter services
   - enable/disable selected service
   - start/stop selected service

This matches the startup plan better: recommended profile startup entries are defaults, not hardcoded requirements, and users can add/remove apps/services through the GUI.

## Prototype 7 Matugen palette integration

Fixed companion app theming gap: the PySide settings app no longer uses a fully hardcoded green/dark palette.

The app now reads DMS-exported KDE/Qt palette files in priority order:

1. `~/.local/share/color-schemes/DankMatugen.colors`
2. `~/.config/qt6ct/colors/matugen.conf`
3. `~/.config/qt5ct/colors/matugen.conf`

Mapped palette roles:

- accent: `[Colors:Selection] BackgroundNormal`
- accent text: `[Colors:Selection] ForegroundNormal`
- background: `[Colors:Window] BackgroundNormal`
- surface/card: `[Colors:View] BackgroundAlternate`
- secondary surface: `[Colors:Button] BackgroundNormal`
- text: `[Colors:Window] ForegroundNormal`
- muted text: `[Colors:Window] ForegroundInactive`
- border: `[Colors:Button] BackgroundAlternate`

This keeps the companion app aligned with the DMS Matugen export. It will update on next launch after DMS exports a new palette.

## Prototype 8 Keybindings and Portals pages

Added:

- `Keybindings` page:
  - lists Mango `bind=` and `axisbind=` lines
  - marks duplicate shortcut keys
  - adds raw `bind=`/`axisbind=` lines
  - removes selected binding lines
  - saves with backup and reload

- `Portals` page:
  - shows core/wlr/gtk/kde portal service status
  - shows expected Mango portal files
  - restarts portal services
  - opens portal config/unit files
  - launches a browser target for manual file chooser testing

## Prototype 9 Theme Bridge and Default Apps pages

Added:

- `Theme Bridge` page:
  - validates DMS settings, DankMatugen KDE colors, qt5ct/qt6ct configs and palettes, GTK3/GTK4 files
  - shows loaded app palette colors
  - opens qt5ct/qt6ct and theme notes

- `Default Apps` page:
  - shows current vs approved MIME defaults
  - applies approved KDE/Qt workstation defaults with backup of `~/.config/mimeapps.list`
  - opens `mimeapps.list` and KDE default apps settings

## Prototype 10 Screenshots and Remote Desktop pages

Added:

- `Screenshots` page:
  - validates grim/slurp/swappy/wf-recorder/wl-copy
  - validates screenshot helper scripts
  - launches region/full/copy screenshot helpers
  - opens screenshot folder
  - provides wf-recorder terminal command launcher

- `Remote Desktop` page:
  - shows Sunshine service status
  - opens Sunshine web UI
  - restarts Sunshine
  - opens RustDesk
  - shows NVIDIA status via `nvidia-smi`
  - documents accepted RustDesk weird-env state

## Prototype 11 Health/reboot regression checks

Updated `scripts/dms-workstation-health` for reboot regressions:

- Mango config checks for display environment import
- Mango config/running check for `xembedsniproxy`
- real StatusNotifierWatcher checks for Dropbox and Sunshine tray items
- HDMI audio sink visibility through PipeWire/wpctl
- Ethernet carrier warnings for known NICs

Theme Bridge now notes that the companion app must be restarted after a DMS Matugen export to reload palette values.

## Prototype 12 Restore script and final smoke pass

Added:

```text
scripts/restore-mango-baseline
```

Behavior:

- dry-run by default
- `--apply` restores newest available backups for files managed by `apply-mango-baseline`
- runs `systemctl --user daemon-reload` after restore

Final smoke checks for this task stack:

- settings app Python compile: PASS
- settings app offscreen launch: PASS by timeout/no crash
- restore script dry-run: PASS
- health check updated and run: PASS for Mango core/portals/tray/HDMI, warns only unused Ethernet port with no carrier

## Prototype 13 Startup Manager category redesign

Redesigned Startup page around ownership/categories instead of raw commands first:

1. **Normal application autostart**
   - manages `~/.config/autostart/*.desktop`
   - add/enable/disable/remove GUI apps
   - intended for apps that do not require a tray icon during session startup

2. **Tray-ready startup**
   - manages `~/.config/dms-kde-workstation/startup.json`
   - services in this list are restarted by `dms-mango-post-startup` only after DMS StatusNotifierWatcher is ready and `xembedsniproxy` is running
   - intended for Dropbox, Sunshine, and similar tray-sensitive services

3. **User service autostart**
   - uses `systemctl --user enable/disable/start/stop`
   - intended for normal background services

4. **Advanced Mango exec-once commands**
   - raw Mango startup commands remain available but are no longer the primary interface

This addresses the question: adding another tray app should work if it is added to the Tray-ready startup section, not normal app autostart.

## Prototype 14 Keybindings real-control editor

Redesigned Keybindings page so raw Mango lines are no longer the primary interface.

Primary UI now has:

- existing shortcut list with human-readable labels
- duplicate shortcut warning
- modifier checkboxes: Super, Ctrl, Alt, Shift
- key field
- shortcut type dropdown:
  - Mango action
  - Run command
  - Wheel/axis action
- Mango action dropdown with common window, focus, layout, and keyboard-layout actions
- command/argument field
- Add shortcut / Clear editor buttons

Raw `bind=` / `axisbind=` input remains only as an advanced escape hatch.

Current supported action presets include:

- close/minimize/restore/maximize/floating/fullscreen
- focus next/previous/left/right/up/down
- keyboard layout toggle and direct English/Greek selection
- layout switching through `mmsg -s -l S/M/T/DW`

Implementation note: the UI still writes normal Mango config lines. It is a safer front-end, not a separate keybinding system.

## Prototype 15 Default Apps real category UI

Redesigned Default Apps page from status text to category rows with dropdown controls.

Categories:

- Folders → `inode/directory`
- PDFs → `application/pdf`
- Images → `image/png`, `image/jpeg`, `image/webp`
- Archives → `application/zip`, `application/x-tar`
- Text/code → `text/plain`, `text/markdown`
- Browser → `x-scheme-handler/http`, `x-scheme-handler/https`

Each row now shows:

- category name and scope
- current status (`OK`, `WARN`, or `MIXED`)
- dropdown populated from installed `.desktop` files

Actions:

- Apply selected defaults
- Refresh
- Apply approved baseline
- Open `mimeapps.list`
- Open KDE Default Apps module

Implementation still uses `xdg-mime default ...` and backs up `~/.config/mimeapps.list` before applying changes.

## Prototype 16 Login/autologin UX cleanup

Redesigned Login page into a clear verified-status plus managed-action layout.

Status card now shows:

- detected display manager
- autologin enabled/disabled/unknown state
- autologin user
- autologin session
- config file that provided the active Autologin section
- other Autologin sections if multiple files exist

Management card now makes scope explicit:

- Enable Mango autologin writes only `/etc/sddm.conf.d/dms-mango-autologin.conf`
- Disable managed autologin removes only that DMS-managed file
- other SDDM autologin files are left untouched and will still show in status

Admin actions now open in a terminal using `pkexec` with `sudo` fallback, so the user can see password prompts and errors instead of a silent detached command.

## Prototype 17 Animation curve coverage

Expanded Animations & Effects page to include Mango's cubic-bezier animation curve settings.

New curve fields:

- `animation_curve_open`
- `animation_curve_move`
- `animation_curve_tag`
- `animation_curve_close`
- `animation_curve_focus`
- `animation_curve_opafadeout`
- `animation_curve_opafadein`

Each curve is edited as `x1,y1,x2,y2` with values between `0` and `1`.

Added curve presets:

- Balanced / Mango default
- Snappy
- Soft / DMS-like
- Linear / minimal
- Slow ease

Save validates curve syntax before writing Mango config. Presets only populate the fields; user must still save animation/effects to write them.

## Prototype 18 KDE/System settings scope labels and theming wrapper

Updated external tool/settings launchers so KDE modules are clearly labeled by scope and no longer presented as Mango-native controls.

Tools page now separates:

- application launchers
- external KDE/System settings

External settings rows include scope notes:

- Default Applications: global XDG MIME defaults, affects Mango apps/portals
- SDDM Login Screen: system SDDM config, global/admin scope
- Autostart: mixed scope; some entries affect Mango, Plasma-only entries may not
- Colors/Appearance: mostly KDE/Plasma/KDE-app settings; Mango/DMS theming still comes from DMS Matugen export and qtct configs

KDE modules now launch through `launch_kde_module()`, which wraps them with:

```text
QT_QPA_PLATFORMTHEME=qt6ct
QT_QPA_PLATFORMTHEME_QT6=qt6ct
```

This is intended to reduce white/unthemed KDE settings windows under Mango.

Also changed internal config-file open buttons to `xdg-open`, so `mimeapps.list` and similar text files respect the user's default editor instead of hardcoding Kate.

## Prototype 19 smoke-test and restore coverage

Added a project smoke test for the companion app:

```text
scripts/test-mango-settings-smoke
```

It performs:

- Python compile check
- Qt offscreen launch check with timeout

Restore coverage updated:

- `scripts/restore-mango-baseline` now includes `~/.local/bin/dms-mango-post-startup`
- `scripts/restore-mango-baseline` now includes `~/.config/dms-kde-workstation/startup.json`

This keeps the new Startup Manager/tray-ready startup work reversible through the same baseline restore workflow.

## Prototype 17b Animation type correction

Corrected animation type dropdowns after checking Mango documentation/wiki.

Open/close animation types now include:

- `slide`
- `zoom`
- `fade`
- `none`

Added exposed tuning values:

- `fadein_begin_opacity`
- `fadeout_begin_opacity`
- `zoom_initial_ratio`
- `zoom_end_ratio`

Note: older/local examples only showed `slide`/`zoom`, but current Mango docs and rule docs list `slide`, `zoom`, `fade`, and `none`.

## Prototype 17c Graphical curve editor

Replaced raw text-only animation curve controls with a graphical cubic-bezier editor.

Each curve row now shows:

- a preview canvas with grid
- bezier curve line
- visible control handles and tangents
- sliders for x1, y1, x2, y2
- generated curve value for transparency

The app still writes Mango-compatible values such as `0.46,1,0.29,1`, but users no longer need to type those numbers directly.

Preset behavior remains the same: presets update the graphical editors, then Save writes to Mango config.

## Font bridge requirement

DMS font settings affect DMS UI directly. For a KDE/Qt-first Mango workstation, font changes must also be bridged to app/toolkit configuration:

- `~/.config/kdeglobals` `[General] font/fixed/menuFont/toolBarFont/smallestReadableFont`
- `~/.config/gtk-3.0/settings.ini` `gtk-font-name`
- `~/.config/gtk-4.0/settings.ini` `gtk-font-name`
- `~/.config/qt5ct/qt5ct.conf` `[Fonts] general/fixed`
- `~/.config/qt6ct/qt6ct.conf` `[Fonts] general/fixed`

Under Mango with qtct platform theme, Qt apps may ignore DMS-only font changes until qtct font entries exist and the app is restarted. A future Theme Bridge/Fonts page should expose font family/size and write all of the above with backups.

## Mango matugen reload hazard

DMS's upstream Mango/mangowc matugen template includes a post-hook that runs `mmsg -d reload_config` after generating `~/.config/mango/dms/colors.conf`.

In this workstation profile, Mango config does not source that generated colors file, and runtime layout should not reset on wallpaper changes. Therefore the recommended profile setting is:

```json
"matugenTemplateMangowc": false
```

The companion app should expose this as a warning/toggle under Theme Bridge or Layout:

- **Mango color template**: off by default
- Warning: enabling it can reload Mango on wallpaper/theme changes and reset runtime layout to tag defaults

GTK/Qt/KDE app color templates can remain enabled; they do not require Mango compositor reload.

## Prototype 20 Font bridge page

Added a font bridge to the Theme Bridge page so one action can set the workstation font across all toolkit configs.

Font bridge writes:

- DMS `settings.json` `fontFamily`
- `~/.config/kdeglobals` `[General] font/fixed/menuFont/toolBarFont/smallestReadableFont`
- `~/.config/gtk-3.0/settings.ini` `gtk-font-name`
- `~/.config/gtk-4.0/settings.ini` `gtk-font-name`
- `~/.config/qt5ct/qt5ct.conf` `[Fonts] general/fixed`
- `~/.config/qt6ct/qt6ct.conf` `[Fonts] general/fixed`

UI:

- font family combo populated from `fc-list`
- size dropdown 8-24pt
- current font status per source shown
- apply button with backup confirmation
- refresh button

All affected files are backed up before writing.

Note: running apps need restart to pick up the new font. This is a toolkit limitation, not a DMS/Mango issue.
