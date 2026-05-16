# Blender drag-and-drop investigation

Date: 2026-05-16

## User report

Dolphin -> Blender drag/drop does not work for:

- `.blend`
- `.fbx`
- `.obj`
- image files

## Why this matters

This extends the DnD concern beyond Nuke. DnD is a workstation-critical workflow for creative apps.

## Initial inspection

Blender is not installed from Fedora RPM or Flatpak. It is a local Blender 5.0.1 bundle:

```text
/home/npittas/blender-5.0.1-linux-x64/
```

Current launcher:

```text
~/.local/share/applications/Blender 5.desktop
Exec=/home/npittas/blender-5.0.1-linux-x64/blender-launcher
```

## Research summary

Upstream Blender has known Wayland drag/drop issues:

- Blender issue #99737: drag-and-drop does not work with the Wayland backend.
- Blender Wayland limitations around finding windows under cursor / window position.
- Some formats have had separate Blender drag/drop limitations, especially asset/import formats.

This means Blender DnD failure may be an application/backend issue, not solely niri.

## Test workaround added

Created X11/XWayland launcher:

```text
~/.local/bin/blender5-x11
~/.local/share/applications/Blender-5-X11.desktop
```

Wrapper contents:

```bash
exec env WAYLAND_DISPLAY= GDK_BACKEND=x11 SDL_VIDEODRIVER=x11 /home/npittas/blender-5.0.1-linux-x64/blender-launcher "$@"
```

Purpose:

- Force Blender away from native Wayland.
- Test whether DnD works better through XWayland.

## Dolphin service menu workaround

Created:

```text
~/.local/share/kio/servicemenus/blender5-open.desktop
```

Actions:

- Open with Blender 5
- Open with Blender 5 (X11 / DnD Test)

Purpose:

If DnD remains unreliable, Dolphin right-click/open-with integration may be the practical replacement for `.blend` files and possibly some import workflows.

## Manual tests needed

### Native Blender

- Launch `Blender 5`.
- Drag `.blend` from Dolphin.
- Drag image from Dolphin.
- Drag `.obj` from Dolphin.
- Drag `.fbx` from Dolphin.

### X11 test Blender

- Launch `Blender 5 (X11 / DnD Test)`.
- Repeat the same drag/drop tests.

### Dolphin service menu

- Right-click `.blend` in Dolphin -> Open with Blender 5.
- Right-click `.blend` -> Open with Blender 5 (X11 / DnD Test).

## Current status

Open. Needs manual testing.

If Blender X11 also fails, DMS Workstation should document Blender drag/drop as unreliable under niri and provide service menu/open-with workflows instead.
