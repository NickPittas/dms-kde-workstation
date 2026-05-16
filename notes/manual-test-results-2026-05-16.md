# Manual test results

Date: 2026-05-16

## Portal experiment results

Active experiment: KDE/wlr-first portal config from `portal-experiment-2026-05-16.md`.

### Zen Browser

| Test                 | Result | Notes                                                        |
| -------------------- | ------ | ------------------------------------------------------------ |
| Download/save dialog | PASS   | Opens with correct Dolphin/KDE-style window. Theme is wrong. |
| Upload/open dialog   | PASS   | Works.                                                       |

Conclusion: KDE FileChooser works for Zen functionally. This is a major improvement over the previous uncertainty. Theme mismatch remains.

## Drag-and-drop results

Source: Dolphin
Test file: `~/dms-dnd-test.txt`

| Target             | Result | Notes                                                                                                        |
| ------------------ | ------ | ------------------------------------------------------------------------------------------------------------ |
| Dolphin → Dolphin  | PASS   | Works.                                                                                                       |
| Dolphin → Zed      | PASS   | Works.                                                                                                       |
| Dolphin → Obsidian | FAIL   | Does not work. Obsidian Flatpak currently has X11 permission but not Wayland; likely XWayland/Electron path. |
| Dolphin → Nuke     | FAIL   | Does not work. Likely Qt/proprietary/XWayland path, needs dedicated investigation.                           |

Conclusion:

Drag/drop is not completely broken in niri because Dolphin → Dolphin and Dolphin → Zed work. The failure appears app-stack-specific, likely XWayland/Electron/proprietary-app related. This is still serious for workstation use, especially Nuke.

## App theme results

| App / launch path                           | Result      | Notes                                                                                                                                                         |
| ------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Zed                                         | BAD         | Opens with completely wrong light theme.                                                                                                                      |
| Dolphin from DMS dock                       | GOOD        | Correct theme.                                                                                                                                                |
| Dolphin from niri `Super+E` / `Meta+E` bind | BAD/PARTIAL | Correct general theme, but detail/list rows alternate between correct color and white background, making text unreadable. Current bind is `spawn "dolphin";`. |

Conclusion:

Launch path affects theming. DMS dock likely launches via desktop entry / DMS launch prefix / different environment. niri direct spawn of `dolphin` appears to produce a subtly different KDE/Qt theme state.

## Follow-up investigations needed

1. Compare Dolphin process environment when launched from DMS dock vs niri shortcut.
2. Change niri `Super+E` bind to launch through the desktop file mechanism instead of raw `dolphin`.
3. Investigate current `QT_QPA_PLATFORMTHEME=gtk3` and whether it causes Zed/Dolphin theme issues.
4. Test Obsidian with Wayland socket / Electron Wayland mode.
5. Investigate Nuke display backend and whether it is XWayland-only.

## Follow-up after first DnD fixes

### Obsidian

Result: PASS.

After enabling Wayland mode for Obsidian Flatpak, Dolphin → Obsidian drag/drop works.

Keep:

```bash
flatpak override --user --socket=wayland --env=OBSIDIAN_USE_WAYLAND=1 md.obsidian.Obsidian
```

### Nuke

Result: FAIL.

Nuke still does not receive drag/drop from Dolphin.

Failed workarounds:

- Nuke direct launchers.
- Dolphin XWayland helper for Nuke DnD.

The XWayland Dolphin helper made things worse: it did not allow dragging anything outside the Dolphin window.

Action taken:

- Removed failed direct Nuke launchers.
- Removed failed Dolphin XWayland helper.

Current conclusion:

Nuke DnD remains unresolved and likely blocked by Nuke/X11/xwayland-satellite/proprietary Qt behavior.

### Dolphin Meta+E

Result: still FAIL after `gtk-launch org.kde.dolphin`.

Next experiment applied:

- Installed `qt5ct` and `qt6ct-kde` after dry-run showed install-only transaction.
- Enabled DMS `qtThemingEnabled=true`.
- Set qt5ct/qt6ct icon theme to `klassy-dark` instead of stale `Adwaita`.
- Changed Meta+E bind to launch Dolphin with explicit `QT_QPA_PLATFORMTHEME=qt6ct`.

New bind:

```kdl
Super+E { spawn "env" "QT_QPA_PLATFORMTHEME=qt6ct" "QT_QPA_PLATFORMTHEME_QT6=qt6ct" "dolphin"; }
```

Needs manual test.

## Dolphin Meta+E screenshot result

Screenshot reviewed:

`/home/npittas/Pictures/Screenshots/Screenshot from 2026-05-16 02-21-15.png`

Result: FAIL.

The previous qt6ct experiment changed spacing/font size but did not fix the white alternating rows. This indicates qt6ct was active but did not load the generated DMS palette because `qt5ct.conf`/`qt6ct.conf` only had `icon_theme=klassy-dark` and no `color_scheme_path` or `custom_palette=true`.

Applied follow-up:

- Added `color_scheme_path=~/.config/qt5ct/colors/matugen.conf`
- Added `custom_palette=true`
- Added `style=Breeze`
- Same for qt6ct.

Revert:

- `scripts/restore-qtct-palette-fix-20260516-022140`

Needs manual retest with a fresh Dolphin instance from Meta+E.

## Dolphin Meta+E final result

Result: PASS.

The qtct palette follow-up fixed the Dolphin Meta+E alternating white row issue.

Working pieces:

- `qt5ct` installed.
- `qt6ct-kde` installed.
- DMS `qtThemingEnabled=true`.
- `~/.config/qt5ct/qt5ct.conf` uses generated `matugen.conf` with `custom_palette=true`.
- `~/.config/qt6ct/qt6ct.conf` uses generated `matugen.conf` with `custom_palette=true`.
- Meta+E launches Dolphin with explicit qt6ct env:

```kdl
Super+E { spawn "env" "QT_QPA_PLATFORMTHEME=qt6ct" "QT_QPA_PLATFORMTHEME_QT6=qt6ct" "dolphin"; }
```

This should be moved into approved DMS KDE Workstation baseline.

## KDE app validation pass

User reported:

- Spectacle does not work; it appears to require Plasma, not just KDE apps under niri.
- Other KDE apps open, but with white/light theme, not matching DMS/KDE Workstation target.

Action taken:

- Created global/current-session Qt environment fix:
  - `~/.config/environment.d/90-dms-kde-qt.conf`
  - `~/.config/systemd/user/dms.service.d/20-kde-qt-theme.conf`
- Imported env into user manager and D-Bus activation environment.
- Restarted DMS.

Environment now set for DMS-launched apps:

```text
QT_QPA_PLATFORMTHEME=qt6ct
QT_QPA_PLATFORMTHEME_QT6=qt6ct
```

Revert:

```bash
~/dms-kde-workstation/scripts/restore-global-qt-env-fix-20260516-022823
```

Needs manual retest: launch Kate/Okular/Gwenview/Ark/Filelight/KWalletManager/Discover from DMS/app launcher and verify theme.

Spectacle decision: do not include as default screenshot tool for niri profile unless later proven working. Prefer grim/slurp/swappy for the baseline.

## KDE app theme after global DMS env fix

Screenshot received: Okular still opens in a white/light theme.

Interpretation:

The DMS service environment alone was not sufficient. Apps may be launched from niri/fuzzel/vicinae or another launcher inheriting the niri process environment, not DMS. Therefore the Qt platform theme must also be set at the niri environment level.

Applied follow-up:

Added to `~/.config/niri/config.kdl`:

```kdl
environment {
    XDG_CURRENT_DESKTOP "niri"
    QT_QPA_PLATFORM "wayland;xcb"
    ELECTRON_OZONE_PLATFORM_HINT "auto"
    QT_QPA_PLATFORMTHEME "qt6ct"
    QT_QPA_PLATFORMTHEME_QT6 "qt6ct"
    TERMINAL "ghostty"
}
```

Validated config and loaded it with:

```bash
niri msg action load-config-file
```

Revert:

```bash
~/dms-kde-workstation/scripts/restore-niri-env-qtct-20260516-023029
```

Needs manual retest after closing and reopening KDE apps. If existing launchers still inherit old env, a logout/login may be needed.

## KDE app theme actual fix

User performed DMS UI action:

- Re-exported baseline GTK3/4 and QT5/6 configurations from DMS Theme and Colors menu.

Result:

- Okular theme now works correctly.

Important conclusion:

The missing step was not only environment variables. DMS must export baseline GTK/Qt configuration after the required qtct/GTK pieces exist. The previous export likely failed or produced incomplete configs because qt5ct/qt6ct-kde and/or GTK pieces were not installed at that time, or it was overwritten later.

Installer implication:

Order matters:

1. Install qt5ct and qt6ct-kde first.
2. Ensure GTK fallback packages/config dirs exist.
3. Enable DMS Qt/GTK theming settings.
4. Run/trigger DMS baseline export for GTK3/4 and QT5/6.
5. Then test KDE/Qt apps.

Do not assume existing DMS exports are valid if dependencies were installed afterward.

## KDE baseline app validation after DMS export

User reported all tested KDE apps open and theme correctly after re-exporting baseline GTK3/4 and QT5/6 configurations from DMS.

Validated category: PASS

Apps covered by user report:

- Kate
- Okular
- Gwenview
- Ark
- Filelight
- KWalletManager
- Plasma Discover
- KDE Partition Manager
- Dolphin from Meta+E
- Dolphin from DMS dock

Conclusion:

The KDE/Qt app baseline is now viable once DMS baseline theme export is run after qt5ct/qt6ct-kde are installed.

## Screenshot launcher/shortcut setup

User reported grim/slurp/swappy had no usable launcher shortcuts.

Confirmed packages are installed:

- grim
- slurp
- swappy
- wf-recorder

Created helper scripts:

```text
~/.local/bin/dms-region-screenshot-edit
~/.local/bin/dms-full-screenshot-edit
~/.local/bin/dms-region-screenshot-copy
```

Created launcher entries:

```text
~/.local/share/applications/dms-region-screenshot-edit.desktop
~/.local/share/applications/dms-full-screenshot-edit.desktop
~/.local/share/applications/dms-region-screenshot-copy.desktop
```

Updated niri shortcuts:

```kdl
Print { spawn "/home/npittas/.local/bin/dms-region-screenshot-edit"; }
Ctrl+Print { spawn "/home/npittas/.local/bin/dms-full-screenshot-edit"; }
Shift+Print { spawn "/home/npittas/.local/bin/dms-region-screenshot-copy"; }
Alt+Print { screenshot-window; }
```

Config validated and loaded.

Needs manual test:

- Print: select region, opens Swappy.
- Ctrl+Print: full screenshot opens Swappy.
- Shift+Print: select region, copies to clipboard.

## Swappy theme issue

User confirmed swappy works but opens in a white theme.

Cause:

- Swappy is GTK3.
- GTK/gsettings had drifted back to `adw-gtk3-dark` or an ineffective GTK state after DMS exports.
- The screenshot helper scripts launched swappy without forcing a dark GTK theme.

Applied fix:

- Set gsettings GTK theme to installed dark Catppuccin theme:
  - `catppuccin-macchiato-blue-standard+default`
- Kept color scheme as `prefer-dark`.
- Patched screenshot edit scripts to launch swappy with:

```bash
env GTK_THEME=catppuccin-macchiato-blue-standard+default swappy -f -
```

Revert:

```bash
~/dms-kde-workstation/scripts/restore-swappy-theme-fix-latest
```

Needs retest:

- Print -> region -> swappy should now use dark GTK theme.
- Ctrl+Print -> full -> swappy should now use dark GTK theme.

## Swappy theme final result

Result: PASS.

User confirmed Swappy theme is fixed after forcing:

```bash
GTK_THEME=catppuccin-macchiato-blue-standard+default
```

inside the screenshot edit helper scripts.

Approved screenshot stack:

- grim
- slurp
- swappy
- wrapper scripts with explicit GTK_THEME
- niri Print/Ctrl+Print/Shift+Print bindings

## Default app cleanup

Applied KDE-first defaults:

- folders -> Dolphin
- PDFs -> Okular
- images -> Gwenview
- archives -> Ark
- text/code -> Zed
- http/https -> Zen Browser

Backup/revert:

- `notes/default-app-cleanup-20260516-024811/`
- `scripts/restore-default-app-cleanup-latest`

Needs manual spot tests from Dolphin:

- double-click PDF opens Okular
- double-click image opens Gwenview
- open archive opens Ark
- folder opens Dolphin

## Default app cleanup final result

Result: PASS / APPROVED.

User confirmed files opened from Dolphin launch the correct applications:

- PDFs -> Okular
- Images -> Gwenview
- Archives -> Ark
- Folders -> Dolphin
- Text/code -> Zed

Default-app baseline approved.

## Blender DnD issue

User reported Dolphin -> Blender drag/drop does not work for `.blend`, `.fbx`, `.obj`, or images.

Research found upstream Blender native Wayland DnD issues. Blender is installed as local bundle:

```text
/home/npittas/blender-5.0.1-linux-x64/
```

Added for testing:

- `Blender 5 (X11 / DnD Test)` launcher.
- `~/.local/bin/blender5-x11` wrapper.
- Dolphin service menu with Open with Blender actions.

Docs:

- `docs/blender-dnd-investigation-2026-05-16.md`

Needs manual testing.

## Blender default app correction

User reported the X11 test path caused an authorization issue and `.blend` files should open in normal Blender.

Action taken:

- Rewrote normal `Blender 5.desktop` to include `%F` and `MimeType=application/x-blender`.
- Made normal Blender desktop file executable/trusted.
- Set `application/x-blender` default back to normal `Blender 5.desktop`.
- Refreshed desktop database and KDE service cache.

Current default:

```text
application/x-blender -> Blender 5.desktop
```

Revert:

```bash
~/dms-kde-workstation/scripts/restore-blender-default-fix-latest
```

## DnD general niri blocker

User clarified that Blender and Nuke DnD both work perfectly under KDE. Therefore this should no longer be treated as a Blender/Nuke-specific configuration problem.

Additional failing case:

- Dolphin -> Blender: FAIL for `.blend`, `.fbx`, `.obj`, images.

Known passing cases under niri:

- Dolphin -> Dolphin: PASS
- Dolphin -> Zed: PASS
- Dolphin -> Obsidian after Wayland override: PASS

Known failing cases under niri:

- Dolphin -> Nuke: FAIL
- Dolphin -> Blender: FAIL

Conclusion:

DnD support under niri is inconsistent and is a potential project blocker for a creative workstation profile. Stop app-specific Blender/Nuke tweaks unless testing a compositor-level workaround.

Removed failed Blender X11 test launcher and Dolphin Blender service menu.

## Mango first login result

Initial Mango login showed only Ghostty and no DMS bar/dock.

Cause found:

- `dms.service` is tied to `graphical-session.target` via the packaged systemd user service.
- Mango session did not bring up `graphical-session.target` in the same way niri did.
- Starting `dms.service` from Mango therefore failed by dependency.

Manual fix applied in-session:

```bash
dms run
```

This started DMS (`dms run` + `qs -p /usr/share/quickshell/dms`).

Permanent Mango config fix:

Changed Mango startup from:

```text
exec-once=systemctl --user start dms.service
```

to:

```text
exec-once=dms run
```

So next Mango login should start DMS directly without relying on the systemd graphical-session target.

## Mango layout emergency fix

User reported Mango layout was unusable and blocked testing.

Applied emergency usability config:

- all tags default to `monocle`
- gaps set to 0
- border reduced to 2
- no border when single window enabled
- disabled sloppy focus and cursor warp
- added layout/floating/maximize binds:
  - Super+Enter -> toggle maximize screen
  - Super+Space -> toggle floating
  - Super+F -> fullscreen
  - Super+T -> tile layout
  - Super+C -> scroller layout
  - Super+D -> dwindle layout
  - Super+' -> monocle layout

Reloaded Mango with:

```bash
mmsg -s -d reload_config
```

Current layout reported: `M` / monocle.

## Mango DnD result

Result: PASS / major finding.

User confirmed:

- Dolphin -> Nuke DnD works in Mango.
- Dolphin -> Blender DnD works in Mango.

Conclusion:

The DnD blocker is niri-specific for this workflow. Mango is now a serious candidate compositor for DMS KDE Workstation.

## Mango scroller/layout controls

User asked how to get a niri-like scroller and how to scroll.

Applied:

- all tags default to `scroller`
- `scroller_focus_center=1`
- `scroller_prefer_center=1`
- current layout set to `S` / scroller via `mmsg -s -l S`

Added controls:

- Super+S -> scroller
- Super+' -> monocle
- Super+T -> tile
- Super+D -> dwindle
- Super+J/K -> focus next/prev client
- Super+H/L or Super+Left/Right -> focus left/right
- Super+mouse wheel up/down -> focus prev/next via axisbind

Mango layout codes from `mmsg -L` include:

- `S` = scroller
- `M` = monocle
- `T` = tile
- `DW` = dwindle

Note: Mango's IPC uses short layout codes; full names via `mmsg -s -l scroller` fall back to tile.

## Mango mouse/layout guidance and UI helper

Added a basic layout selector UI using fuzzel dmenu:

- launcher: `Mango Layout Selector`
- script: `~/.local/bin/mango-layout-menu`
- bind: `Super+Shift+L`

Layouts exposed:

- Scroller / S
- Monocle / M
- Tile / T
- Dwindle / DW
- Grid / G
- Vertical Scroller / VS

Mouse/window controls currently:

- Super + left drag: move floating/tiled window depending on Mango behavior
- Super + right drag: resize
- middle click: toggle maximize screen
- drag_tile_to_tile=1 allows tile rearrangement by mouse

Scroller movement:

- Super+J / Super+K: focus next/previous client
- Super+H / Super+L: focus left/right
- Super+Left / Super+Right: focus left/right
- Super + mouse wheel up/down: focus prev/next

## Mango mouse scroll/tray follow-up

User reported:

- Super+mouse scroll did not work for scroller navigation.
- DMS tray/bar only showed RustDesk, not Dropbox/Sunshine.

Investigation:

- Mango config had duplicate `axisbind=SUPER,UP/DOWN` entries.
- Earlier default axis binds used `viewtoleft_have_client` / `viewtoright_have_client`, which did not visibly move scroller focus in the current test.
- DMS StatusNotifierWatcher is running.
- RustDesk registers on the user bus and appears in tray.
- Dropbox and Sunshine processes are running, but they do not appear to register StatusNotifier items on the current user bus. Sunshine likely has no tray; Dropbox may use legacy tray/appindicator behavior not exposed to DMS.

Action:

- Removed duplicate/old Super axisbinds.
- Left only clean scroller navigation axisbinds:

```text
axisbind=SUPER,UP,focusstack,prev
axisbind=SUPER,DOWN,focusstack,next
axisbind=SUPER,LEFT,focusdir,left
axisbind=SUPER,RIGHT,focusdir,right
```

Needs manual retest: Super+mouse wheel up/down in scroller.

Tray conclusion:

Autostart is working for Dropbox/Sunshine. The missing icons are likely not an autostart failure but a tray/protocol support difference. DMS sees StatusNotifier items; RustDesk provides one. Dropbox/Sunshine do not currently expose visible StatusNotifier items under Mango/DMS.

## Mango Super+mouse wheel scroller navigation

Result: PASS.

After removing duplicate old axisbinds, Super+mouse wheel now works for scroller navigation.

Working axisbinds:

```text
axisbind=SUPER,UP,focusstack,prev
axisbind=SUPER,DOWN,focusstack,next
axisbind=SUPER,LEFT,focusdir,left
axisbind=SUPER,RIGHT,focusdir,right
```

## DMS indicators regression in Mango

User noted DMS had indicators under niri for services like Dropbox/Sunshine, but under Mango only RustDesk appears.

Interpretation:

This is likely a DMS compositor-specific data path/regression under Mango, not simply missing autostart. Services are running, but DMS is not surfacing the same indicators it showed in niri.

Needs investigation in DMS source/UI service model:

- Which DMS widgets/indicators are compositor-independent?
- Which depend on niri-specific services/session state?
- How DMS decides to show screen sharing / service / tray indicators.
- Whether Mango/DWL backend exposes fewer status hooks.

## Mango portal health fix

Problem:

- `xdg-desktop-portal.service` was inactive/dead under Mango.
- D-Bus activation failed because Fedora's stock user unit has `Requisite=graphical-session.target`.
- Mango session did not activate `graphical-session.target` the same way niri/KDE did.

Fix:

- Added user override unit:
  - `~/.config/systemd/user/xdg-desktop-portal.service`
- The override removes dependency on `graphical-session.target` for this user.
- Added user Mango portal config:
  - `~/.config/xdg-desktop-portal/mango-portals.conf`

Result:

- `xdg-desktop-portal.service` active.
- `org.freedesktop.portal.Desktop` present on user bus.
- Health check now passes portal core service.

Revert:

```bash
~/dms-kde-workstation/scripts/restore-mango-portal-unit-override-latest
```

## Mango keyboard layout controls

User needs English/Greek keyboard swap and Alt+Shift is not accessible enough.

Configured:

```text
xkb_rules_layout=us,gr
```

Added Mango binds:

```text
Super+Space       -> switch keyboard layout
Super+Shift+Space -> switch keyboard layout
Super+Ctrl+1      -> English / layout index 0
Super+Ctrl+2      -> Greek / layout index 1
```

Added `Keyboard` section to Mango Workstation Menu:

- Switch layout
- Set English (US)
- Set Greek (GR)
- Current layout
- Open Mango config

Current reported layout at time of setup:

```text
HDMI-A-1 kb_layout us
```

## Mango keyboard layout correction

User reported Super+Space was toggling floating and should not be keyboard layout switching. User needs Alt+Shift like niri/KDE.

Cause:

- Conflicting binds existed:
  - `Super+Space` was both floating and layout switch.
  - Emergency config had floating on Super+Space.

Fix:

- Removed `Super+Space` keyboard switching.
- Removed `Super+Space` floating toggle.
- Kept floating toggle on:
  - `Alt+Backslash`
  - `Super+Shift+Space`
- Added Mango documented modifier-key layout switch:

```text
bind=ALT,shift_l,switch_keyboard_layout
bind=ALT,shift_r,switch_keyboard_layout
```

Kept explicit layout binds:

```text
Super+Ctrl+1 -> English
Super+Ctrl+2 -> Greek
```

Needs manual test: Alt+Shift should toggle us/gr.

## Mango Alt+Shift keyboard toggle final result

Result: PASS.

User confirmed Alt+Shift toggles English/Greek correctly under Mango.

Approved baseline:

```text
xkb_rules_layout=us,gr
bind=ALT,shift_l,switch_keyboard_layout
bind=ALT,shift_r,switch_keyboard_layout
bind=SUPER+CTRL,1,switch_keyboard_layout,0
bind=SUPER+CTRL,2,switch_keyboard_layout,1
```

## DMS indicators under Mango investigation

User clarified DMS core indicators work under Mango:

- Bluetooth
- Audio
- Network
- Notifications
- Clipboard
- Language

Missing are startup/service app indicators like Dropbox/Sunshine.

Investigation showed:

- Dropbox and Sunshine are running.
- RustDesk appears because it registers a StatusNotifier item.
- Dropbox/Sunshine do not appear as StatusNotifier items in current Mango/DMS session.

Prototype fix added:

- `~/.local/bin/dms-workstation-service-indicator`
- synthetic StatusNotifier item: `Workstation Services`
- tooltip shows Dropbox/Sunshine/Vicinae/Portal state
- added to Mango autostart

Needs manual visual test: check whether a Workstation Services tray icon appears in DMS.

### Workstation Services indicator visual test

Confirmed by user: the synthetic `Workstation Services` DMS tray indicator is visible under Mango.

Result: PASS.

## DMS Mango Workstation Settings GUI prototype

Created first Qt/PySide6 GUI prototype:

- `~/.local/bin/dms-mango-settings`
- desktop launcher: `DMS Mango Workstation Settings`
- project source: `tools/dms-mango-settings.py`

Smoke tests:

- Python compile: PASS
- Qt offscreen startup smoke test: PASS by timeout/no immediate crash
- Deployer dry-run includes GUI files: PASS

Needs manual visual test by user.

## DMS Mango Settings GUI Prototype 2

Added after user feedback that Prototype 1 had too few settings and hard-coded startup assumptions.

New pages:

- Input
- Startup
- Login

Smoke tests:

- Python compile: PASS
- Qt offscreen startup smoke test: PASS by timeout/no immediate crash
- Installed updated script to `~/.local/bin/dms-mango-settings`: PASS

Needs manual visual/use test.

## DMS Mango Settings GUI Prototype 3

Added scroller-specific and Mango-specific layout controls, including focused-window centering.

Fixed duplicate `Super+Shift+L` binding: stale `mango-layout-menu` binding removed, general `mango-workstation-menu` binding remains.

Smoke tests:

- Python compile: PASS
- Qt offscreen startup smoke test: PASS by timeout/no immediate crash
- Mango config reload after keybind cleanup: attempted/no blocking error

Needs manual test: press `Super+Shift+L` and confirm general menu opens, then launch GUI settings.

## DMS Mango Settings GUI Prototype 4

Full UI refactor after user feedback:

- DMS-like left sidebar
- dark/accent styling
- scrollable pages
- cards
- sliders/dropdowns/toggles instead of plain forms

Smoke tests:

- Python compile: PASS
- Qt offscreen startup smoke test: PASS by timeout/no immediate crash
- Installed updated script to `~/.local/bin/dms-mango-settings`: PASS

Needs manual visual test.

## DMS Mango Settings GUI Prototype 5

Added Backup & Recovery page.

Smoke tests:

- Python compile: PASS
- Qt offscreen startup smoke test: PASS by timeout/no immediate crash
- Installed updated script to `~/.local/bin/dms-mango-settings`: PASS

Needs manual visual/restore test.

## DMS Mango Settings GUI Prototype 6

Startup Manager v2 added.

Features:

- Mango `exec-once` command manager
- XDG/KDE application autostart manager
- systemd user service autostart manager

Smoke tests:

- Python compile: PASS
- Qt offscreen startup smoke test: PASS by timeout/no immediate crash
- Installed updated script to `~/.local/bin/dms-mango-settings`: PASS

Needs manual test:

- add/remove harmless desktop autostart entry
- enable/disable a non-critical user service if available
- save Mango startup command after creating checkpoint

## DMS Mango Settings GUI Prototype 7

Matugen palette integration added.

Smoke test palette values loaded from current DMS/KDE export:

- accent: `#1042ff`
- accent text: `#e2e1ef`
- background: `#11131c`
- surface: `#1a1b25`

Compile/install: PASS.

## Real tray indicator fix under Mango

Found root cause for missing Dropbox/Sunshine icons:

- services were running with stale niri/no-display environment
- Sunshine explicitly logged `WAYLAND_DISPLAY has not been defined` and `Failed to create system tray`
- KDE `xembedsniproxy` existed but only autostarts in KDE

Runtime fix:

- imported current Mango display/session env into systemd/dbus activation
- started `xembedsniproxy`
- restarted Dropbox and Sunshine

Result:

- Dropbox registered real StatusNotifier item
- Sunshine registered real StatusNotifier item
- Sunshine log: `System tray created`

Persistent Mango config updated and copied to project baseline.

## Follow-up environment audit after tray fix

Checked likely GUI/tray processes.

Correct Mango environment:

- DMS / Quickshell
- Vicinae
- portals
- xembedsniproxy
- Dropbox
- Workstation service indicator

Wrong/stale environment:

- RustDesk server/tray is launched by RustDesk root/background service with `DISPLAY=:0`, background session class, and no `WAYLAND_DISPLAY`.

User systemd environment was refreshed to active Mango `XDG_SESSION_ID=53` and current session path.

## Mango workstation completion task stack

Completed 10-task stack:

1. Keybindings editor page
2. Portal settings page
3. Theme Bridge page
4. Default Apps page
5. Screenshots & Recording page
6. Remote Desktop page
7. Matugen/theme polish note/status
8. Health check reboot regression checks
9. Restore Mango baseline script
10. Docs/spec/manual results and smoke tests

Smoke tests:

- `python3 -m py_compile tools/dms-mango-settings.py`: PASS
- Qt offscreen settings launch: PASS by timeout/no crash
- `scripts/restore-mango-baseline` dry-run: PASS
- `scripts/dms-workstation-health`: PASS for active Mango core, tray icons, portals, HDMI; warns only enp6s0 no carrier

## Additive Mango post-startup helper

Implemented first version of additive helper:

- imports current Mango environment into systemd and D-Bus activation
- waits for DMS/Quickshell StatusNotifierWatcher
- starts `xembedsniproxy` if missing
- restarts tray-ready services from `~/.config/dms-kde-workstation/startup.json`
- starts optional post-start commands

Manual run result: PASS.

Log:

```text
~/.local/state/dms-kde-workstation/mango-post-startup.log
```

Mango config now calls helper instead of hardcoding xembedsniproxy and Dropbox/Sunshine restarts directly.

## Startup Manager category redesign

Implemented category-based Startup page:

- Normal application autostart
- Tray-ready startup backed by `~/.config/dms-kde-workstation/startup.json`
- User service autostart
- Advanced Mango exec-once commands

Smoke tests:

- Python compile: PASS
- Qt offscreen startup smoke test: PASS by timeout/no immediate crash
- Installed updated script: PASS

Needs manual UI test: add/remove a harmless service in Tray-ready list and confirm `startup.json` updates.

## Keybindings real-control editor

Implemented new Keybindings page with modifier checkboxes, key field, type dropdown, action dropdown, duplicate detection, and advanced raw binding escape hatch.

Smoke tests:

- Python compile: PASS
- Qt offscreen startup smoke test: PASS by timeout/no immediate crash
- Installed updated script: PASS

Needs manual UI test:

- Add a harmless shortcut from controls.
- Confirm duplicate warning appears if reusing an existing shortcut.
- Save and confirm Mango reloads.

## Default Apps category UI

Implemented category rows/dropdowns for default apps:

- Folders
- PDFs
- Images
- Archives
- Text/code
- Browser

Smoke tests:

- Python compile: PASS
- Qt offscreen startup smoke test: PASS by timeout/no immediate crash
- Installed updated script: PASS

Needs manual UI test:

- Open Default Apps page.
- Confirm current choices preselect Dolphin/Okular/Gwenview/Ark/Zed/Zen.
- Apply selected defaults and verify no unwanted change.

## Login/autologin page UX cleanup

Implemented clearer SDDM autologin page:

- separate verified status card
- explicit Enabled/Disabled/Configured-but-not-SDDM state
- visible User/Session/Config file fields
- Enable/Disable actions explain exactly which file they write/remove
- admin commands open in a terminal for visible password/error handling

Smoke tests:

- Python compile: PASS
- Qt offscreen startup smoke test: PASS by timeout/no immediate crash
- Installed updated script: PASS

Needs manual UI test before enabling autologin on a real reboot.

## Animation curve coverage

Implemented Animation curve fields and presets:

- open/move/tag/close/focus/fade-out/fade-in curves
- preset dropdown for Balanced, Snappy, Soft, Linear, Slow ease
- validation for four comma-separated values between 0 and 1

Smoke tests:

- Python compile: PASS
- Qt offscreen startup smoke test: PASS by timeout/no immediate crash
- Installed updated script: PASS

Needs manual UI test:

- Open Animations & Effects.
- Apply a preset.
- Save/reload Mango.
- Confirm motion feels correct and no config reload errors appear.

## KDE/System settings scope labels and theming wrapper

Implemented scope-labeled tool/settings launchers:

- KDE Default Applications labeled global XDG
- SDDM Login Screen labeled system/admin
- Autostart labeled mixed scope
- Colors/Appearance labeled mostly KDE/Plasma/KDE-app scope

KDE modules now launch with qtct environment variables. Config-file buttons use `xdg-open` to honor Zed/default editor rather than hardcoding Kate.

Smoke tests:

- Python compile: PASS
- Qt offscreen startup smoke test: PASS by timeout/no immediate crash
- Installed updated script: PASS

Needs manual UI test:

- Click Open mimeapps.list and confirm Zed opens.
- Open KDE Default Apps/Login Screen from Tools and confirm theme is acceptable.

## Restore/smoke-test hardening

Added `scripts/test-mango-settings-smoke` for repeatable compile/offscreen-launch validation.

Updated `scripts/restore-mango-baseline` to include:

- `~/.local/bin/dms-mango-post-startup`
- `~/.config/dms-kde-workstation/startup.json`

Verification:

- smoke test: PASS
- restore dry-run: PASS, no backups yet for newly managed files is expected until the deployer backs them up

## Animation type correction

User correctly pointed out Mango supports more animation types than slide/zoom.

Updated open/close dropdowns to include:

- slide
- zoom
- fade
- none

Added fade/zoom parameter sliders for begin opacity and zoom scale ratios.

Smoke test: PASS.

## Graphical animation curve editor

Implemented graphical curve editor for Mango animation curves:

- curve preview canvas
- control point/tangent visualization
- x1/y1/x2/y2 sliders
- generated numeric value shown as secondary information

Smoke test: PASS.

Needs manual UX test: confirm the preview updates and feels more user-friendly than raw curve numbers.

## Font bridge investigation

User changed DMS font to JetBrains Mono. Inspection showed:

- DMS settings changed: `~/.config/DankMaterialShell/settings.json` has `fontFamily=JetBrains Mono`
- KDE globals changed: `~/.config/kdeglobals` has `font=JetBrains Mono NL,12,...`
- GTK3/GTK4 changed: `gtk-font-name=JetBrains Mono NL, 12`
- qt5ct/qt6ct configs did not have a `[Fonts]` section

Conclusion: DMS font setting is not enough for all Qt apps under Mango when Qt apps are launched through qtct platform theme. Qt apps such as Dolphin may need qt5ct/qt6ct `[Fonts]` entries and an app restart.

Applied qtct font bridge:

```ini
[Fonts]
fixed="JetBrains Mono NL,12,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
general="JetBrains Mono NL,12,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
```

Files updated:

- `~/.config/qt5ct/qt5ct.conf`
- `~/.config/qt6ct/qt6ct.conf`
- project qt snapshots

Backup created under `~/.local/state/dms-kde-workstation/backups/20260516-134052`.

Manual test needed: fully close Dolphin and reopen it; if it still ignores the font, inspect Dolphin environment and Qt platform theme usage.

## Wallpaper change resets Mango layout investigation

Found cause:

- DMS setting `matugenTemplateMangowc=true` enabled the Mango/mangowc matugen template.
- `/usr/share/quickshell/dms/matugen/configs/mangowc.toml` has:

```text
post_hook = 'sh -c "mmsg -d reload_config 2>&1 || true"'
```

- Every wallpaper/theme generation therefore reloads Mango config.
- Mango reload re-applies `tagrule=id:N,layout_name:scroller`, resetting current layout back to default scroller/sliding.

Applied fix:

```json
"matugenTemplateMangowc": false
```

Backup:

```text
~/.local/state/dms-kde-workstation/backups/20260516-134536/.config/DankMaterialShell/settings.json
```

Manual test needed: switch current layout to tile/monocle, trigger wallpaper change, confirm Mango no longer resets to scroller.

## Font bridge page

Implemented Theme Bridge font section:

- fc-list populated font family dropdown
- size dropdown
- current font status per source (DMS, kdeglobals, GTK3/4, qt5ct/qt6ct)
- apply-everywhere action with backup
- refresh status

Smoke test: PASS.
