# Decisions log

Record every decision here with date, reason, and rollback notes.

## 2026-05-16

- Created project folder: `/home/npittas/dms-kde-workstation`.
- Cloned upstream DMS into `upstream/DankMaterialShell`.
- Decided initial architecture: niri + DMS shell, KDE/Qt workstation layer, GTK fallback only.
- Decided to stabilize local reference system before writing installer automation.

## 2026-05-16 basic tools install

Safety process used:

1. Captured health baseline.
2. Captured RPM package baseline.
3. Ran `dnf install --assumeno` first.
4. Confirmed transaction only installed packages; no removals, no upgrades.
5. Installed first workstation-tools batch.
6. Ran health check after install.

Installed for testing, not yet approved:

- kate
- flatseal
- pavucontrol
- qpwgraph
- gnome-disk-utility
- gparted
- system-config-printer
- swappy
- wf-recorder
- blueman

Observation:

- Health check now sees most baseline tools.
- `flatseal` command name on Fedora is `com.github.tchx84.Flatseal`; health script was fixed.
- KDE polkit agent service exists, but starting it says an auth agent already exists. The current process/bus scan does not identify it clearly, so do not change polkit yet. Test with an admin GUI first.
- KDE and wlr portal services are still not active; portal strategy remains next major test area.

## 2026-05-16 direction correction: KDE-first, no GNOME duplicates

User clarified KDE is already installed and KDE applications are already available. The DMS Workstation stack should not install GNOME alternatives just to fill gaps.

Decision:

- Default stack is KDE/Qt-first.
- GNOME/GTK tools are fallback only when KDE/Qt has no good standalone tool or when a portal/app requires it.
- Updated package candidates to prefer KDE tools:
  - `kde-partitionmanager` instead of `gnome-disk-utility`/`gparted` as default disk UI.
  - `kwalletmanager5`/KWallet instead of Seahorse/gnome-keyring as default secrets UI.
  - `spectacle` where it works, with grim/slurp/swappy as wlroots fallback.
  - KCalc instead of GNOME Calculator/Qalculate by default.
- Health check now separates KDE/Qt workstation apps from helper/admin tools.

Note:

`gnome-disk-utility` was installed in the first test batch before this clarification. A dry-run removal shows it would remove only:

- `gnome-disk-utility`
- unused dependency `libhandy`

No removal has been performed yet. Decide later whether to remove it after KDE disk tools are validated.

## 2026-05-16 current state inspection

Read-only inspection saved to:

- `docs/current-state-inspection-2026-05-16.md`
- raw inspection files in `notes/inspection-20260516-014958/`

Main result:

- KDE app stack is already present and strong.
- niri/DMS are running correctly.
- Current weak point is configuration mismatch, not missing KDE apps.
- Active portal profile is GNOME/GTK-first.
- Qt env is GTK-themed despite KDE-first direction.
- DMS GTK theming is enabled while Qt theming is disabled.

Next recommended work is portal and Qt/KDE configuration testing, not more package installation.

## 2026-05-16 portal experiment and DnD issue

Portal experiment applied:

- Backed up old GTK/GNOME-first niri portal config.
- Applied KDE/wlr-first portal candidate.
- Restarted portals.
- Confirmed KDE, wlr, GTK, and GNOME portal backends are all running / D-Bus visible.

Docs:

- `docs/portal-experiment-2026-05-16.md`
- `docs/drag-and-drop-investigation-2026-05-16.md`

Revert script:

- `scripts/restore-portal-before-kde-wlr-experiment`

Drag-and-drop issue was reported by user and documented as project-critical. Initial research points to known niri/xwayland-satellite fragility, especially between Wayland and XWayland apps. Needs manual test matrix.

## 2026-05-16 DnD fixes applied

Applied changes documented in:

- `docs/dnd-fixes-2026-05-16.md`

Changes:

1. Obsidian Flatpak now has Wayland socket and `OBSIDIAN_USE_WAYLAND=1`.
2. niri/DMS `Super+E` Dolphin bind now uses `gtk-launch org.kde.dolphin` instead of raw `dolphin`.
3. Created direct Nuke launchers that do not wrap Nuke in Ghostty.
4. Created `Dolphin (XWayland for Nuke DnD)` helper launcher for testing same-X11 drag/drop into Nuke.

Revert:

- `scripts/restore-dnd-fixes-20260516-021137`

Important note:

Nuke ships Qt xcb platform plugin but no Qt Wayland platform plugin in `/opt/Nuke17.0v1/qtplugins/platforms`, so true native Wayland Nuke does not appear available from the installed bundle. Nuke DnD may require XWayland workaround or may remain limited by xwayland-satellite.

## 2026-05-16 DnD follow-up and Dolphin theme experiment

- Obsidian Wayland override fixed Dolphin → Obsidian DnD. Keep it.
- Nuke DnD workarounds failed. Removed failed Nuke direct launchers and XWayland Dolphin helper.
- Meta+E Dolphin still failed with `gtk-launch org.kde.dolphin`.
- Installed `qt5ct` and `qt6ct-kde` after dry-run showed only 2 new packages, no removals/upgrades.
- Enabled DMS `qtThemingEnabled=true`.
- Set qt5ct/qt6ct icon theme to `klassy-dark`.
- Changed Meta+E Dolphin bind to explicit qt6ct env.

Revert for Dolphin theme experiment:

- `scripts/restore-dolphin-theme-fix-20260516-021940`

## 2026-05-16 Dolphin Meta+E fixed

Confirmed fixed by user.

Approved baseline components:

- `qt5ct`
- `qt6ct-kde`
- DMS `qtThemingEnabled=true`
- qt5ct/qt6ct configs using DMS-generated `matugen.conf` with `custom_palette=true`
- Meta+E Dolphin launched with explicit `QT_QPA_PLATFORMTHEME=qt6ct` and `QT_QPA_PLATFORMTHEME_QT6=qt6ct`

Working configs copied to `configs/qt/`, `configs/niri/`, and `configs/dms/`.

## 2026-05-16 global Qt env fix for KDE apps

Problem:

- KDE apps opened but were white/light themed outside Plasma.
- Dolphin Meta+E was fixed only because it had explicit qt6ct env.

Decision/action:

- Apply qt6ct environment globally for DMS KDE Workstation:
  - `~/.config/environment.d/90-dms-kde-qt.conf`
  - DMS service drop-in `~/.config/systemd/user/dms.service.d/20-kde-qt-theme.conf`
- Restarted DMS so DMS-launched apps inherit qt6ct.

Revert:

- `scripts/restore-global-qt-env-fix-20260516-022823`

Spectacle:

- User reports Spectacle does not work under niri and needs Plasma.
- Mark Spectacle as not approved for niri baseline; use grim/slurp/swappy instead.

## 2026-05-16 niri environment qtct fix

Okular still opened light after DMS service env fix. Added qt6ct environment block to niri config so apps launched by niri/fuzzel/vicinae/direct compositor spawns get the correct Qt platform theme.

Revert:

- `scripts/restore-niri-env-qtct-20260516-023029`

## 2026-05-16 DMS baseline export is required

User confirmed that Okular theming was fixed only after manually using DMS Theme and Colors menu to re-export baseline GTK3/4 and QT5/6 configurations.

Decision:

- The installer must install qt5ct/qt6ct-kde before triggering DMS theme export.
- DMS Workstation health check must detect whether qtct configs include the generated matugen palette and whether the export needs rerun.
- DMS UI/installer should expose a clear "Export/Rebuild GTK + Qt theme configs" action, not bury it.

## 2026-05-16 KDE app baseline approved

User confirmed all tested KDE apps open and theme correctly after DMS baseline export.

This validates the KDE-first architecture for DMS Workstation.

## 2026-05-16 screenshot integration

Spectacle rejected for niri baseline. Created launcher scripts and .desktop entries for grim/slurp/swappy and bound Print/Ctrl+Print/Shift+Print in niri.

Working config copied to:

- `configs/niri/config.kdl.working-screenshot-binds-20260516`
- `configs/scripts/`
- `configs/applications/`

## 2026-05-16 swappy theme fix

Swappy is GTK3 and opened with a white theme. Patched screenshot edit scripts to force `GTK_THEME=catppuccin-macchiato-blue-standard+default` for swappy and aligned GNOME gtk-theme gsetting to the same installed dark theme.

Installer implication:

- GTK helper apps may need explicit GTK_THEME wrappers even in KDE-first stack.
- DMS Workstation should avoid relying on global GTK state for small helper apps.

## 2026-05-16 swappy approved

User confirmed Swappy dark theme fix works. Approved screenshot stack for DMS KDE Workstation:

- grim
- slurp
- swappy
- explicit GTK_THEME wrappers
- niri screenshot keybinds

## 2026-05-16 default app cleanup

Applied KDE-first default application baseline:

- PDF: Okular
- Images: Gwenview
- Archives: Ark
- Folders: Dolphin
- Browser: Zen
- Text/code: Zed

Working `mimeapps.list` copied to `configs/mime/mimeapps.list.working-20260516`.

## 2026-05-16 default app baseline approved

User confirmed file opening from Dolphin works with the intended KDE-first defaults. Baseline approved.

## 2026-05-16 Blender DnD investigation

Blender drag/drop fails from Dolphin. Upstream Blender has known Wayland DnD issues. Created X11 test launcher and Dolphin service menu workaround. This is not approved yet.

## 2026-05-16 Blender default corrected

X11 Blender test should not be default. Normal Blender desktop file now has `%F`, MIME type, executable bit, and is the default for `application/x-blender`.

## 2026-05-16 DnD marked as niri-level project blocker

User confirmed Blender and Nuke drag/drop work in KDE, but not niri. Stop treating this as Blender/Nuke-specific. Removed failed Blender X11 launcher/service-menu experiments. DnD is now tracked as a compositor/workflow blocker for DMS KDE Workstation.

## 2026-05-16 Mango evaluation setup

Installed MangoWM 0.13.0 from Terra temporary repo source for evaluation only. Did not add Terra release repo permanently.

Created `~/.config/mango/config.conf` from `/etc/mango/config.conf` and added DMS startup, Ghostty/Vicinae binds, Dolphin/Zen/screenshot binds, and safer quit bind.

Doc: `docs/mango-evaluation-2026-05-16.md`

Next step: logout, choose Mango session, test DnD into Blender/Nuke.

## 2026-05-16 Mango DMS startup fix

DMS service failed in Mango because the packaged `dms.service` depends on `graphical-session.target`, which Mango did not activate. Fixed Mango evaluation config to start DMS directly with `exec-once=dms run` instead of `systemctl --user start dms.service`.

This means the Mango profile needs its own DMS startup path, not a reinstall.

## 2026-05-16 Mango layout emergency fix

Mango default tile layout was unusable for testing. Switched all tags to monocle and added basic layout/floating/maximize binds. This is evaluation-only.

## 2026-05-16 Mango DnD passes and scroller enabled

Mango fixes the project-critical DnD blocker for Nuke and Blender. This strongly suggests the DMS KDE Workstation should pivot from niri to Mango for creative workstation use.

Configured Mango with scroller layout by default and added layout/focus controls. Future DMS UI should expose `mmsg -L` layouts as a dropdown and switch with `mmsg -s -l <code>`.

## 2026-05-16 Mango workflow/UI prototype

Added autostart parity, scroller mouse controls, and a fuzzel-based Mango Workstation Menu. This is the first working prototype of a DMS Mango settings dropdown/control surface.

Doc: `docs/mango-workflow-guide-2026-05-16.md`

## 2026-05-16 Mango tray/autostart clarification

Dropbox and Sunshine services are running in Mango. Their icons are absent from DMS tray because they do not appear to register StatusNotifier items on the user bus, unlike RustDesk. Treat this as tray protocol/visibility issue, not autostart failure.

Cleaned duplicate Mango axisbinds for Super+wheel scroller navigation.

## 2026-05-16 Mango mouse navigation approved

Super+mouse wheel works after cleaning duplicate axisbinds. Approved for Mango scroller workflow.

DMS indicators under Mango need source-level investigation because niri had service indicators that Mango currently lacks despite services running.

## 2026-05-16 expanded Mango Workstation Menu

Expanded `~/.local/bin/mango-workstation-menu` into submenu-based temporary settings UI for layout, mouse/navigation, appearance, autostart, status, and config actions. Copied to `configs/scripts/mango-workstation-menu`.

## 2026-05-16 Mango baseline frozen and health check updated

Captured working Mango config to `configs/mango/config.conf.working-20260516`.

Created `docs/mango-baseline-2026-05-16.md` documenting Mango as primary creative workstation candidate because Blender/Nuke DnD works.

Updated `scripts/dms-workstation-health` to verify Mango baseline, theme baseline, default apps, Obsidian override, autostarts, and known blockers.

Current health check confirms Mango active and core baseline OK. Remaining warnings:

- xdg-desktop-portal.service not active, while wlr/gtk backends are active.
- no user mango portal config yet.
- Spectacle rejected intentionally.
- DMS indicators/tray incomplete under Mango.
- no native Mango settings GUI found.

## 2026-05-16 Mango window controls

Mango lacks KDE-style global titlebar buttons. Added Window submenu to Mango Workstation Menu and direct keybinds for close/minimize/restore/maximize/floating/fullscreen. Updated working Mango config and menu script copies.

## 2026-05-16 Mango portal health fixed

Created user override for xdg-desktop-portal.service because Mango does not activate graphical-session.target, causing Fedora's stock portal unit to fail Requisite dependency. Core portal service now active under Mango.

Copied working unit/config to:

- `configs/systemd-user/xdg-desktop-portal.service.mango-override-20260516`
- `configs/xdg-desktop-portal/mango-portals.conf.working-20260516`

## 2026-05-16 Mango keyboard layout controls

Configured us,gr and added accessible switch/set binds plus Keyboard submenu in Mango Workstation Menu. Avoided variants because online Mango issue reports crashes with variants during layout switching.

## 2026-05-16 Alt+Shift keyboard toggle for Mango

Fixed conflict around Super+Space. Added Alt+Shift left/right as Mango keyboard layout toggle using `bind=ALT,shift_l,switch_keyboard_layout` and `bind=ALT,shift_r,switch_keyboard_layout`.

## 2026-05-16 Mango keyboard toggle approved

User confirmed Alt+Shift toggles English/Greek correctly under Mango. Baseline approved.

## 2026-05-16 DMS service indicator prototype

Created synthetic StatusNotifier item for Workstation Services to show Dropbox/Sunshine/Vicinae/Portal state in DMS tray under Mango. This is a prototype; long-term should be native DMS widget/plugin.

Doc: `docs/dms-indicators-mango-2026-05-16.md`

## 2026-05-16 Mango Settings UI direction

Drafted `docs/dms-mango-settings-spec.md`.

Decision: the current terminal/TUI `mango-workstation-menu` is only a stopgap. Final UX should be either:

1. DMS/Quickshell-native Workstation Settings panel, preferred for overview/status/repair integration, or
2. Qt/Kirigami companion app for heavier editing workflows.

Recommended path: start with a DMS-native MVP for Overview, Services, Portals, Theme Bridge, Default Apps validation, and external tool launchers. Move complex config editing to a Qt/Kirigami app later if needed.

## 2026-05-16 First profile deployer

Created draft Fedora Mango baseline profile and safe deployer:

- `profiles/fedora/mango-baseline.md`
- `scripts/apply-mango-baseline`

The deployer defaults to dry-run and requires `--apply` before writing files. Package installation is separately gated behind `--install-packages` and uses the temporary Terra repo only for `mangowm`.

## 2026-05-16 Start building GUI settings

Started with a Qt/PySide6 companion GUI rather than waiting for full DMS/Quickshell integration. Reason: user needs practical customization now.

Created `dms-mango-settings` prototype with Overview, Layout, Keyboard, Services, and Tools pages. DMS-native integration can come later after the control model stabilizes.

## 2026-05-16 Mango startup ownership and additive post-startup helper

Created `docs/startup-ownership-mango-2026-05-16.md` to avoid duplicating DMS startup behavior.

Decision:

- DMS owns `dms run`, Quickshell, StatusNotifierWatcher/Host, tray rendering, theme export.
- Mango profile owns only Mango-specific gaps: env import, portal workaround, `xembedsniproxy`, and tray-sensitive service restart after DMS tray watcher is ready.
- Added `dms-mango-post-startup` helper. It does not start DMS; it waits for the watcher and only then starts compatibility pieces and configured tray-ready services.

Files:

- `scripts/dms-mango-post-startup`
- `configs/dms-kde-workstation/startup.json`
- `~/.local/bin/dms-mango-post-startup`
- `~/.config/dms-kde-workstation/startup.json`

## 2026-05-16 Disable DMS Mango matugen template to stop layout resets

DMS's `mangowc` matugen template writes `~/.config/mango/dms/colors.conf` and runs this post-hook on every wallpaper/theme generation:

```text
mmsg -d reload_config
```

Mango `reload_config` rereads tag rules such as `tagrule=id:1,layout_name:scroller`, which resets the current layout back to the configured default. This is bad for the user's expected behavior: runtime layout choice should survive wallpaper changes.

Current Mango config does not source `~/.config/mango/dms/colors.conf`, so reloading Mango for that generated color file is unnecessary in this profile.

Decision: set DMS setting `matugenTemplateMangowc=false` to stop DMS from running the Mango matugen template and post-hook during wallpaper changes. DMS still owns shell colors, and GTK/Qt/KDE/Zed/etc templates remain enabled.

## 2026-05-16 Lesson: never ship untested admin scripts

I wrote scripts that modify /etc/sddm.conf.d/ with elevated privileges without dry-running them first. The standalone consolidate-sddm-autologin script had EOF/quoting errors and was given to the user to run with pkexec. This was reckless.

Rule from now on:
- Any script or action that modifies system files must be dry-run first.
- The in-app GUI action must generate a command string that can be inspected before execution.
- Never tell the user to run an admin script that hasn't been tested.
