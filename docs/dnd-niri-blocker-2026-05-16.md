# DnD niri blocker

Date: 2026-05-16

## Status

Potential project blocker for DMS KDE Workstation.

## User-confirmed baseline

Under KDE, drag-and-drop works correctly for both Blender and Nuke.

Under niri, the same workflows fail.

Therefore this should no longer be treated primarily as a Blender/Nuke configuration problem. It is a niri/compositor/session workflow problem.

## Current niri DnD matrix

| Source  | Target   | Result         | Notes                                                   |
| ------- | -------- | -------------- | ------------------------------------------------------- |
| Dolphin | Dolphin  | PASS           | Same-app KDE/Wayland path works.                        |
| Dolphin | Zed      | PASS           | Works.                                                  |
| Dolphin | Obsidian | PASS after fix | Required Obsidian Flatpak Wayland override.             |
| Dolphin | Nuke     | FAIL           | Works under KDE, fails under niri.                      |
| Dolphin | Blender  | FAIL           | `.blend`, `.fbx`, `.obj`, images fail. Works under KDE. |

## Failed experiments removed

Removed:

```text
~/.local/bin/blender5-x11
~/.local/share/applications/Blender-5-X11.desktop
~/.local/share/kio/servicemenus/blender5-open.desktop
```

Reason:

The issue should not be solved by per-app hacks if the same apps work under KDE. The project needs to evaluate niri as the compositor base.

## Research summary

Online niri ecosystem search shows multiple drag/drop related issues:

- Drag and drop between windows discussion.
- Drag/drop from unfocused windows.
- Drag/drop focus shifting issues.
- Electron drag/drop bugs.
- Nautilus/Zen drag/drop bugs.
- XWayland-satellite drag/drop limitations.

This does not prove every failure is niri-only, but the user-confirmed KDE comparison strongly suggests niri is the variable that breaks these workflows.

## Why this matters

A creative workstation must support external file drag/drop into apps like:

- Blender
- Nuke
- compositing tools
- DCC tools
- image/video apps
- editors

If niri cannot reliably provide this, DMS KDE Workstation has a serious architecture problem.

## Decision point

Before building an installer, we must decide one of:

1. **Accept niri limitation** and document DnD as broken for some DCC apps.
2. **Find a compositor-level niri workaround**.
3. **Use DMS on a different compositor/session for workstation profile**.
4. **Use KDE Plasma as the primary workstation session and keep niri/DMS experimental**.

## Next recommended investigation

Do not continue app-specific Blender/Nuke tweaks.

Instead test compositor/session-level variables:

- Same apps under KDE Plasma Wayland: already reported working.
- Same apps under niri with focused source window vs unfocused source window.
- Same apps under niri with source/target on same column/workspace vs different columns.
- Same apps under niri with floating source and target windows.
- Same apps under niri after disabling any DnD edge-scroll/gesture behavior if configurable.
- Check niri version and upstream issues for fixes newer than current package.
- Test another non-Plasma compositor only if useful as control, e.g. Sway/Hyprland, but only if already available and safe.

## Current conclusion

The DMS KDE Workstation stack is promising for apps, theming, portals, screenshots, and default apps. But DnD failures into Blender/Nuke under niri may block using niri as the primary compositor for professional creative work.
