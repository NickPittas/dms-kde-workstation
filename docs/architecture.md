# Architecture: KDE-powered DMS Workstation

## Objective

Create a usable Fedora workstation environment using MangoWM and DankMaterialShell without forcing users to rediscover the missing pieces normally provided by KDE/GNOME.

MangoWM is the primary compositor candidate because it fixed the required Dolphin -> Nuke/Blender drag-and-drop workflow. niri remains secondary/experimental until that blocker is resolved.

## Target architecture

```text
Fedora base
  ├─ MangoWM
  │   └─ compositor, window management, scroller/tile/monocle layouts, reliable creative-app DnD
  ├─ DankMaterialShell
  │   └─ panel, launcher surface, dashboard, theme UX
  ├─ KDE/Qt workstation layer
  │   ├─ Dolphin, Kate, Okular, Gwenview, Ark, KCalc/Qalculate
  │   ├─ KWallet/KWalletManager or selected secrets backend
  │   └─ KDE/Qt file dialogs where they behave better
  ├─ Portal layer
  │   ├─ xdg-desktop-portal core
  │   ├─ wlr portal for screenshot/screencast
  │   ├─ gtk portal as compatibility fallback
  │   ├─ optional kde portal where it behaves well outside Plasma
  │   └─ Mango user-unit override where Fedora's graphical-session.target dependency blocks startup
  ├─ DE-independent admin tools
  │   ├─ nm-connection-editor
  │   ├─ blueman
  │   ├─ pavucontrol + qpwgraph/helvum
  │   ├─ gnome-disk-utility + gparted
  │   ├─ firewall-config
  │   ├─ Flatseal/Warehouse
  │   └─ system-config-printer/simple-scan
  └─ DMS Workstation tooling
      ├─ Health Check
      ├─ Portal Manager
      ├─ App/Menu Manager
      ├─ Theme Bridge
      ├─ Remote Desktop Center
      └─ Recovery Center
```

## Why KDE/Qt as the main app layer

For this workstation, KDE/Qt is the better primary app stack because:

- Dolphin is already preferred and is stronger than most lightweight file managers.
- Kate, Okular, Gwenview, Ark, Filelight, KCalc are mature workstation tools.
- Professional workflows benefit from feature-rich apps more than minimal purity.
- A KDE app base reduces the “missing everyday tool” problem.

GTK should remain available, but as fallback/compatibility rather than the identity of the system.

## What DMS should eventually own

DMS should not necessarily reimplement every settings panel. It should provide a portal/control surface that:

- opens the correct tool for a setting,
- shows whether the tool/backend is installed,
- explains what component owns the setting,
- backs up configs before changes,
- validates portal/theme/service health,
- provides repair actions.

## Non-goals

- Not a pure minimal setup.
- Not a full KDE Plasma replacement on day one.
- Not a GTK-only environment.
- Not a hidden pile of terminal commands.
- Not returning to niri as the primary profile while Blender/Nuke DnD is broken there.

## Success criteria

A normal user can do the following without searching man pages:

- change network settings,
- pair Bluetooth devices,
- set display scale/resolution safely,
- change default apps,
- add a custom launcher/menu entry,
- manage Flatpak permissions,
- manage secrets/keyring,
- configure remote desktop,
- diagnose portal/file picker/screenshot issues,
- reset broken theme/portal/display configuration.
