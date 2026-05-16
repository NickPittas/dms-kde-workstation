# Approved Fedora packages

Nothing approved yet.

Use this file only for packages that were tested on the reference machine and accepted as part of the DMS KDE Workstation baseline.

Format:

```text
package-name  # why it is included / tested behavior
```

## Approved compositor baseline

```text
mangowm  # Primary creative-workstation compositor candidate; fixed Dolphin -> Nuke and Dolphin -> Blender drag-and-drop where niri failed.
```

Install note:

```text
sudo dnf install -y --nogpgcheck --repofrompath 'terra,https://repos.fyralabs.com/terra$releasever' mangowm
```

The Terra repo was used as a temporary package source during evaluation, not added permanently.

## Approved after testing: Qt/KDE theming bridge

```text
qt5ct       # Needed for DMS-generated Qt5 theme config/palette support outside Plasma.
qt6ct-kde   # Needed for DMS-generated Qt6 theme config/palette support outside Plasma; fixed Dolphin Meta+E row colors with qt6ct palette config.
```

## Approved screenshot baseline for Mango/niri

```text
grim    # niri/wlroots screenshot backend tool
slurp   # region selection for grim
swappy  # screenshot annotation/editor; installed and available
```

Rejected for current niri baseline:

```text
spectacle  # Opens only with Plasma requirements / not working correctly under current niri session.
```

## Approved KDE/Qt workstation app baseline

User confirmed these open and theme correctly after DMS baseline export:

```text
kate
okular
gwenview
ark
filelight
kwalletmanager5
plasma-discover
kde-partitionmanager
dolphin
kcalc
```

Required theming condition:

- Install `qt5ct` and `qt6ct-kde` first.
- Enable DMS Qt theming.
- Re-export DMS baseline GTK3/4 and QT5/6 configs after dependencies exist.

## Approved screenshot integration commands

Installed tools:

```text
grim
slurp
swappy
wf-recorder
```

Approved launcher/shortcut approach:

```text
Print       -> region screenshot into Swappy
Ctrl+Print  -> full screenshot into Swappy
Shift+Print -> region screenshot to clipboard
Alt+Print   -> niri built-in focused-window screenshot
```

Screenshot theme condition:

```text
Swappy must be launched with GTK_THEME=catppuccin-macchiato-blue-standard+default or equivalent DMS-exported GTK dark theme.
```

## Approved default application baseline

```text
inode/directory                    -> org.kde.dolphin.desktop
application/pdf                    -> okularApplication_pdf.desktop
image/png/jpeg/gif/webp/tiff/svg   -> org.kde.gwenview.desktop
archives                           -> org.kde.ark.desktop
text/plain/markdown/code-ish       -> dev.zed.Zed.desktop
http/https                         -> app.zen_browser.zen.desktop
```

User confirmed opening files from Dolphin launches correct applications.

## Approved Mango keyboard layout baseline

```text
xkb_rules_layout=us,gr
Alt+Shift -> switch keyboard layout
Super+Ctrl+1 -> English
Super+Ctrl+2 -> Greek
```
