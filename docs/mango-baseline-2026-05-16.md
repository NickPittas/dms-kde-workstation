# DMS KDE Workstation Mango baseline

Date: 2026-05-16

## Status

Mango is now the primary compositor candidate for the creative workstation profile.

Reason:

- Dolphin -> Nuke DnD works under Mango.
- Dolphin -> Blender DnD works under Mango.
- The same workflows failed under niri.

## Installed compositor

```text
mangowm 0.13.0
mmsg included
```

Session file:

```text
/usr/share/wayland-sessions/mango.desktop
```

Working config captured:

```text
configs/mango/config.conf.working-20260516
```

## Key working features

- DMS starts with `exec-once=env QT_QPA_PLATFORMTHEME=qt6ct QT_QPA_PLATFORMTHEME_QT6=qt6ct dms run`.
- Vicinae autostarts.
- portal overrides/config can be deployed before first Mango login.
- KDE/Qt apps theme correctly after DMS baseline export.
- Scroller layout is configured.
- Super+mouse wheel navigation works.
- Nuke DnD works.
- Blender DnD works.
- Default apps are KDE-first and approved.
- Screenshot stack uses grim/slurp/swappy.

## Known gaps

- DMS integration is weaker than niri.
- DMS service indicators/tray indicators are missing/incomplete under Mango.
- No polished Mango settings GUI exists online.
- Temporary fuzzel menu is not acceptable long term.
- Need native DMS Mango settings panel or companion Qt/Kirigami app.

## Current Mango controls

```text
Super+S       -> Scroller
Super+'       -> Monocle
Super+T       -> Tile
Super+D       -> Dwindle
Super+Shift+L -> Mango Workstation Menu
Super+J/K     -> focus next/previous
Super+H/L     -> focus left/right
Super+mouse wheel -> scroller previous/next
Super+left drag -> move
Super+right drag -> resize
```

## Architectural decision

Mango should become the primary candidate for the creative workstation installer. niri remains useful but should be marked secondary/experimental because of DnD failures in Blender/Nuke.

Safety note: users must not switch to Mango until preflight checks, baseline apply, and first-login readiness all pass from a currently working session.
