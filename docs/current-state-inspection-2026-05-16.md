# Current KDE/niri/DMS state inspection

Date: 2026-05-16
Inspection directory: `notes/inspection-20260516-014958/`

This inspection is read-only documentation of the current system state, except for the earlier package-install test batch that was already logged separately.

## Summary

The machine is already much closer to a KDE-powered DMS workstation than expected. KDE Plasma packages and KDE applications are largely installed. The main weakness is not missing KDE apps; it is that the active niri/DMS session is still wired through GNOME/GTK portal behavior and GTK-oriented Qt environment variables.

The biggest current mismatch:

```text
KDE/Qt apps are installed and should be the workstation base,
but the active niri session uses GTK/GNOME portals and QT platform theme = gtk3.
```

## Session state

From `session.txt`:

```text
Desktop=niri
Type=wayland
XDG_CURRENT_DESKTOP=niri
XDG_SESSION_DESKTOP=niri
WAYLAND_DISPLAY=wayland-1
niri 26.04
DMS v1.4.6
Quickshell 0.3.0
```

DMS is running under niri and the session is Wayland.

Important environment variables:

```text
QT_QPA_PLATFORM=wayland;xcb
QT_QPA_PLATFORMTHEME=gtk3
QT_QPA_PLATFORMTHEME_QT6=gtk3
```

This is not ideal for a KDE-first stack. Qt/KDE apps are being pushed through GTK platform theme integration instead of KDE/Qt integration.

## niri state

From `niri.txt`:

- Main config: `~/.config/niri/config.kdl`
- DMS-generated niri snippets exist in `~/.config/niri/dms/`
- `niri validate` reports config is valid.

Display state:

```text
Output: HDMI-A-1 / Samsung Q70A
Current mode: 3840x2160 @ 60 Hz
Scale: 2
Logical size: 1920x1080
VRR: supported, disabled
```

This is a safe display state compared with the earlier 4K@120/HDMI FRL problems.

## DMS state

From `dms.txt` and direct settings inspection:

```text
DMS version: v1.4.6
currentThemeName: dynamic
currentThemeCategory: dynamic
gtkThemingEnabled: true
qtThemingEnabled: false
syncModeWithPortal: true
matugenTemplateGtk: true
matugenTemplateQt5ct: true
matugenTemplateQt6ct: true
```

Interpretation:

- DMS is actively managing GTK theming.
- DMS is not applying Qt theming, even though Qt template generation options exist.
- For the KDE-first workstation goal, this is backwards: Qt/KDE should become the primary target, GTK should become fallback.

DMS has useful workstation-adjacent UI pieces already:

- Network icon toggle
- Bluetooth icon toggle
- Audio icon toggle
- VPN icon toggle
- Printer icon toggle
- Screen sharing icon toggle
- Privacy indicators
- Clipboard
- System tray
- Notepad/session state
- Plugin metadata

This suggests DMS can be extended into a workstation control surface without starting from zero.

## Portal state

From `portals.txt`:

Installed portal packages:

```text
xdg-desktop-portal
xdg-desktop-portal-gnome
xdg-desktop-portal-gtk
xdg-desktop-portal-kde
xdg-desktop-portal-wlr
```

Active portals:

```text
xdg-desktop-portal.service active
xdg-desktop-portal-gtk.service active
xdg-desktop-portal-gnome.service active
xdg-desktop-portal-wlr.service inactive
```

KDE portal package is installed, but there is no user service named `xdg-desktop-portal-kde.service` on this system. It may be D-Bus activatable rather than systemd-service visible.

Current user portal config:

```ini
~/.config/xdg-desktop-portal/niri-portals.conf

[preferred]
default=gnome;gtk;
org.freedesktop.impl.portal.FileChooser=gtk;
org.freedesktop.impl.portal.Access=gtk;
org.freedesktop.impl.portal.Notification=gtk;
org.freedesktop.impl.portal.Secret=gnome-keyring;
```

System KDE portal config exists:

```ini
/usr/share/xdg-desktop-portal/kde-portals.conf

[preferred]
default=kde
org.freedesktop.impl.portal.Settings=kde;gtk;
org.freedesktop.impl.portal.Secret=kwallet
```

System wlroots portal config exists:

```ini
/usr/share/xdg-desktop-portal/wlroots-portals.conf

[preferred]
default=gtk
org.freedesktop.impl.portal.ScreenCast=wlr
org.freedesktop.impl.portal.Screenshot=wlr
org.freedesktop.impl.portal.Settings=darkman
```

Interpretation:

The current active config is GNOME/GTK-first. For the KDE-first DMS workstation, the next major test should be a KDE/wlr portal profile:

```ini
[preferred]
default=kde;gtk;
org.freedesktop.impl.portal.FileChooser=kde;gtk;
org.freedesktop.impl.portal.OpenURI=kde;gtk;
org.freedesktop.impl.portal.Secret=kwallet;
org.freedesktop.impl.portal.ScreenCast=wlr;
org.freedesktop.impl.portal.Screenshot=wlr;
org.freedesktop.impl.portal.Access=gtk;
org.freedesktop.impl.portal.Notification=gtk;
```

This should be tested carefully, not blindly applied.

## KDE/Qt state

From `qt-kde.txt`:

KDE is already substantially installed. Important packages present include:

- `plasma-desktop`
- `plasma-systemsettings`
- `plasma-discover`
- `plasma-nm`
- `plasma-pa`
- `plasma-print-manager`
- `plasma-disks`
- `kde-partitionmanager`
- `kwalletmanager5`
- `spectacle`
- `filelight`
- `polkit-kde`
- `xdg-desktop-portal-kde`
- `kde-gtk-config`
- many KF6/KDE Frameworks packages

KDE globals show:

```ini
[General]
ColorScheme=MaterialYouDark
TerminalApplication=/usr/bin/ghostty --gtk-single-instance=true
TerminalService=com.mitchellh.ghostty.desktop

[Icons]
Theme=klassy-dark

[KDE]
LookAndFeelPackage=Catppucine Nick
```

Interpretation:

- KDE apps already have a MaterialYouDark/Catppuccin-ish configuration.
- Ghostty is already the KDE default terminal.
- KDE app base is strong enough to be the primary workstation base.
- The environment variable `QT_QPA_PLATFORMTHEME=gtk3` conflicts with this direction and should be investigated.

## GTK state

From `gtk.txt`:

GTK settings:

```ini
gtk-application-prefer-dark-theme=true
gtk-theme-name=catppuccin-macchiato-blue-standard+default
gtk-icon-theme-name=klassy-dark
gtk-cursor-theme-name=breeze_cursors
```

Custom GTK3/GTK4 CSS overrides are present and were created during the earlier Zen portal fix.

But GNOME settings still show:

```text
gtk-theme = 'adw-gtk3-dark'
color-scheme = 'prefer-dark'
icon-theme = 'klassy-dark'
cursor-theme = 'breeze_cursors'
```

Interpretation:

GTK state is still mixed:

- GTK settings.ini says Catppuccin.
- gsettings says `adw-gtk3-dark`.
- DMS has GTK theming enabled.
- GTK CSS portal overrides exist.

For KDE-first, this should not be the core theme path. Keep GTK usable, but do not make it the main identity.

## Apps, MIME, defaults

From `apps-mime.txt`:

Desktop entries:

```text
~/.local/share/applications: 17
/usr/share/applications: 381
/var/lib/flatpak/exports/share/applications: 26
~/.local/share/flatpak/exports/share/applications: 1
```

Important defaults:

```text
inode/directory: org.kde.dolphin.desktop
text/plain: dev.zed.Zed.desktop
application/pdf: app.zen_browser.zen.desktop
http/https: app.zen_browser.zen.desktop
```

Custom protocol handlers exist:

```text
x-scheme-handler/cavalry=cavalry-protocol.desktop
x-scheme-handler/opencode=OpenCode-handler.desktop
```

Interpretation:

- Dolphin is correctly default for folders.
- Zen is default browser.
- PDF default is currently Zen, not Okular. For a KDE workstation, this should probably become Okular after user approval.
- Custom protocol handler work confirms why a DMS App/Menu Manager is needed.

## Services/autostart state

From `services.txt`:

Running important user services include:

```text
dms.service
niri.service
dropbox.service
app-dev.lizardbyte.app.Sunshine.service
pipewire.service
pipewire-pulse.service
wireplumber.service
xdg-desktop-portal.service
xdg-desktop-portal-gtk.service
xdg-desktop-portal-gnome.service
kwalletd6 / secretservicecompat via dbus
kded6 via dbus
kdeconnectd via dbus
```

niri wants:

```text
niri.service.wants/dms.service
niri.service.wants/dropbox.service
niri.service.wants/app-dev.lizardbyte.app.Sunshine.service
```

Interpretation:

- DMS, Dropbox, and Sunshine are now correctly tied to niri startup.
- KWallet/secret service compatibility is active.
- KDE services like kded6/kdeconnect are active through D-Bus.
- GNOME/GTK portals remain active and are part of the current mismatch.

## Main findings

### Good state

- KDE app stack is already present.
- niri config is valid.
- DMS is running.
- Display is in safe 4K@60/scale 2 state.
- KWallet/secretservicecompat is running.
- Dolphin is default file manager.
- Ghostty is default terminal in KDE globals.
- Dropbox/Sunshine/DMS autostart with niri.

### Mismatches / problems

1. **Portal stack is GNOME/GTK-first, not KDE/wlr-first.**
2. **Qt platform theme is set to GTK3 despite KDE-first goal.**
3. **DMS Qt theming is disabled.**
4. **GTK settings are internally inconsistent between settings.ini and gsettings.**
5. **PDF default is Zen instead of Okular.**
6. **wlr portal is installed but inactive.**
7. **KDE portal is installed but not active as the selected niri backend.**
8. **Polkit agent detection is unclear: KDE agent claims an agent already exists, but process scan does not identify it. Do not change yet; test with an admin GUI first.**

## Recommended next steps

Do not install more apps yet. The app base is mostly there.

Next work should be configuration/testing:

1. **Portal experiment, with backup**
   - Create a candidate KDE/wlr niri portal config.
   - Restart portals.
   - Test Zen download dialog, Dolphin, Flatpak picker, Spectacle/screenshot, screen recording.
   - Revert if Zen/file picker breaks.

2. **Qt/KDE platform theme experiment**
   - Investigate whether `QT_QPA_PLATFORMTHEME=gtk3` is coming from DMS, niri env, or user environment.
   - Test KDE apps with KDE/Qt platform theme behavior.
   - Do not blindly change until we know why it was set.

3. **DMS Qt theming**
   - Test enabling `qtThemingEnabled` only after backing up DMS settings.
   - Verify Dolphin/Kate/Okular appearance.

4. **Default app cleanup**
   - Consider setting PDF default to Okular.
   - Keep Zen as browser.
   - Preserve Zed as text editor unless user wants Kate.

5. **Polkit validation**
   - Open a known admin GUI such as KDE Partition Manager.
   - Confirm whether authentication prompt appears.
   - Only fix polkit if the prompt fails.

6. **Document accepted state**
   - Once tested, move approved packages/configs into `profiles/fedora/packages-approved.md` and `configs/`.
