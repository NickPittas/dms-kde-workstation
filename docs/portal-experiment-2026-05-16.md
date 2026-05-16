# Portal experiment: KDE/wlr-first niri profile

Date: 2026-05-16
Experiment stamp: `20260516-015511`

## Goal

Test whether a KDE/Qt-first portal profile works better for DMS KDE Workstation than the previous GNOME/GTK-first profile.

## Previous active config

Backed up to:

```text
configs/xdg-desktop-portal/niri-portals.conf.backup-20260516-015511
```

Previous config:

```ini
[preferred]
default=gnome;gtk;
org.freedesktop.impl.portal.FileChooser=gtk;
org.freedesktop.impl.portal.Access=gtk;
org.freedesktop.impl.portal.Notification=gtk;
org.freedesktop.impl.portal.Secret=gnome-keyring;
```

## New experimental active config

Active file:

```text
~/.config/xdg-desktop-portal/niri-portals.conf
```

Candidate stored at:

```text
configs/xdg-desktop-portal/niri-portals.kde-wlr-experiment-20260516-015511.conf
```

Config:

```ini
[preferred]
# DMS KDE Workstation experiment: prefer KDE/Qt for desktop UX,
# wlroots for niri-native capture, GTK/GNOME only as fallback.
default=kde;gtk;
org.freedesktop.impl.portal.FileChooser=kde;gtk;
org.freedesktop.impl.portal.OpenURI=kde;gtk;
org.freedesktop.impl.portal.Secret=kwallet;
org.freedesktop.impl.portal.ScreenCast=wlr;
org.freedesktop.impl.portal.Screenshot=wlr;
org.freedesktop.impl.portal.Access=gtk;
org.freedesktop.impl.portal.Notification=gtk;
org.freedesktop.impl.portal.Settings=kde;gtk;
```

## Result after restart

Portal services and backends started successfully.

Confirmed on D-Bus:

```text
org.freedesktop.impl.portal.desktop.gnome
org.freedesktop.impl.portal.desktop.gtk
org.freedesktop.impl.portal.desktop.kde
org.freedesktop.impl.portal.desktop.wlr
```

Confirmed processes:

```text
/usr/libexec/xdg-desktop-portal
/usr/libexec/xdg-desktop-portal-gnome
/usr/libexec/xdg-desktop-portal-gtk
/usr/libexec/xdg-desktop-portal-kde
/usr/libexec/xdg-desktop-portal-wlr
```

Important: KDE portal is D-Bus activated, not shown as a normal `xdg-desktop-portal-kde.service` systemd unit.

## Revert command

If file pickers, portals, or app behavior break:

```bash
~/dms-kde-workstation/scripts/restore-portal-before-kde-wlr-experiment
```

## Manual tests needed

Please test these and record pass/fail in `tests/phase-1-test-matrix.md`.

### File picker tests

- [ ] Zen Browser download/save dialog opens.
- [ ] Zen Browser upload/open-file dialog opens.
- [ ] Dialog is KDE-style or at least usable.
- [ ] Dolphin still opens folders normally.
- [ ] Flatpak app file picker opens.
- [ ] No stale Zen lock / duplicate launch behavior.

### Screenshot/screencast tests

- [ ] Spectacle launches under niri.
- [ ] Spectacle can take a screenshot.
- [ ] `grim` still works.
- [ ] `swappy` can edit a screenshot.
- [ ] OBS or another screencast app can see a screen source, if installed.
- [ ] Sunshine/Moonlight still works or fails in the same known way.

### Secrets tests

- [ ] KWalletManager opens.
- [ ] Apps can access secrets through KWallet / secretservicecompat.
- [ ] No unexpected GNOME keyring prompt appears.

## Known risk

Zen previously needed GTK FileChooser to work. If KDE FileChooser breaks Zen again, possible fallback is:

```ini
org.freedesktop.impl.portal.FileChooser=gtk;
```

while keeping:

```ini
org.freedesktop.impl.portal.Secret=kwallet;
org.freedesktop.impl.portal.ScreenCast=wlr;
org.freedesktop.impl.portal.Screenshot=wlr;
```

## Manual test results: 2026-05-16

Zen results:

- Download/save dialog works.
- Upload/open dialog works.
- Dialog uses the correct Dolphin/KDE-style window, but theme is wrong.

Conclusion:

KDE FileChooser is functionally viable for Zen. Keep the KDE/wlr portal experiment active for now. Theme mismatch remains a separate Qt/KDE/DMS theme-bridge problem.
