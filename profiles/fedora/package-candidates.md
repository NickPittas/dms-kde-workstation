# Fedora package candidates

These are candidates, not yet approved. Move packages to `packages-approved.md` only after testing.

## Shell / session

```text
niri
xwayland-satellite
xdg-desktop-portal
xdg-desktop-portal-kde
xdg-desktop-portal-wlr
xdg-desktop-portal-gtk  # fallback only if KDE/wlr cannot cover a feature
```

DMS source/release is tracked separately under `upstream/DankMaterialShell`.

## KDE/Qt workstation apps

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
spectacle
filelight
kde-partitionmanager
plasma-disks
```

Possible extras:

```text
kdegraphics-thumbnailers
ffmpegthumbs
kio-extras
```

## Admin tools

Prefer KDE/Qt tools where they already exist. Use DE-independent tools only where KDE does not provide a good standalone option.

```text
# KDE/Qt first
kde-partitionmanager
plasma-disks
kwalletmanager5
plasma-discover
spectacle
filelight

# DE-independent essentials
nm-connection-editor
blueman
pavucontrol
qpwgraph
helvum
firewall-config
system-config-printer
```

Do not add GNOME alternatives to the default profile unless KDE/Qt tooling fails a test.

## Flatpak/app management

```text
flatseal
```

Also evaluate Flatpak apps:

```text
io.github.flattool.Warehouse
it.mijorus.gearlever
```

## Wayland utilities

```text
fuzzel
wl-clipboard
cliphist
grim
slurp
swappy
wf-recorder
swayidle
swaylock
```

## Remote desktop

```text
sunshine
remmina
rustdesk
moonlight-qt
```

Fedora package names may differ or some may come from Flatpak/COPR/RPM Fusion.

## Everyday apps

```text
kcalc
kate
okular
gwenview
ark
filelight
```

Optional user apps, not default stack:

```text
obsidian
logseq
qalculate-qt or qalculate-gtk only if KCalc is insufficient
```

## Validation before approval

For each package/app, record:

- source: Fedora, RPM Fusion, COPR, Flatpak, AppImage
- theme behavior
- Wayland behavior
- XWayland requirement
- portal behavior
- launcher/menu behavior
- known overrides
