# Mango workflow guide

Date: 2026-05-16

## Current status

Mango fixed the project-critical DnD issue:

- Dolphin -> Nuke works.
- Dolphin -> Blender works.

Now the goal is to make Mango usable enough to replace niri for the DMS KDE Workstation profile.

## Autostart parity

Historical note: this file originally captured a machine-local startup experiment.

The safer current model is:

```text
exec-once=env QT_QPA_PLATFORMTHEME=qt6ct QT_QPA_PLATFORMTHEME_QT6=qt6ct dms run
exec-once=systemctl --user start vicinae.service
exec-once=systemctl --user start xdg-desktop-portal-wlr.service xdg-desktop-portal-gtk.service plasma-xdg-desktop-portal-kde.service
exec-once=/home/npittas/.local/bin/dms-mango-post-startup
```

Do not treat direct Dropbox/Sunshine exec-once startup as the baseline model. Tray-sensitive services should be handled by the post-startup helper after DMS tray infrastructure is ready.

## Mango Workstation Menu

Created:

```text
~/.local/bin/mango-workstation-menu
~/.local/share/applications/mango-workstation-menu.desktop
```

Launcher name:

```text
Mango Workstation Menu
```

Shortcut:

```text
Super+Shift+L
```

Menu actions:

- Layout: Scroller
- Layout: Monocle
- Layout: Tile
- Layout: Dwindle
- Layout: Grid
- Toggle: Floating
- Toggle: Maximize
- Toggle: Fullscreen
- Action: Reload Mango Config
- Action: Open Mango Config
- Action: Start DMS
- Action: Start Workstation Autostart
- Status: Current Layout
- Status: Windows

This is a first prototype for the DMS UI dropdown/settings surface.

## Mouse/scroller controls

Use Super as the modifier so normal app scrolling is not broken.

```text
Super + mouse wheel up/down     -> previous/next scroller client
Super + horizontal wheel        -> left/right focus, if hardware sends LEFT/RIGHT axis
Super + side mouse button       -> previous client
Super + extra mouse button      -> next client
Super + left drag               -> move window
Super + right drag              -> resize window
Middle click                    -> toggle maximize screen
```

Keyboard equivalents:

```text
Super+S       -> scroller
Super+'       -> monocle
Super+T       -> tile
Super+D       -> dwindle
Super+J/K     -> next/previous client
Super+H/L     -> left/right client
Super+Left/Right -> left/right client
Super+Shift+L -> Mango Workstation Menu
```

## Known issue

Mango is less discoverable than niri and KDE. DMS should eventually expose a Mango settings panel/dropdown instead of requiring config edits.

Minimum DMS UI needed:

- layout selector
- current layout indicator
- toggle floating/maximize/fullscreen
- reload config
- open Mango config
- autostart status
- DnD status/test helper

## Expanded Mango Workstation Menu

The temporary fuzzel-based menu now has submenus:

```text
Layout
Mouse / Navigation
Appearance
Autostart
Status
Config
```

Launch:

```text
Super+Shift+L
```

or app launcher:

```text
Mango Workstation Menu
```

This is still a prototype, but it now covers the minimum settings UI we need until DMS gets native Mango settings panels.

## Window controls

Mango does not provide KDE-style titlebar buttons globally. Added replacement actions in Mango Workstation Menu and keybinds.

### Menu

`Super+Shift+L` -> `Window`

Actions:

- Close focused window
- Minimize focused window
- Restore minimized windows
- Toggle maximize
- Toggle fullscreen
- Toggle floating
- Toggle scratchpad
- Current window

### Keybinds

```text
Super+Q            -> close focused window
Super+M            -> minimize focused window
Super+Shift+M      -> restore minimized windows
Super+Shift+Enter  -> toggle maximize
Super+Shift+Space  -> toggle floating
Super+Shift+F      -> toggle fullscreen
```

Long-term DMS UI idea: add a Mango window-controls widget with close/minimize/maximize/floating buttons.
