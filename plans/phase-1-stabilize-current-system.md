# Phase 1: Stabilize current system

Purpose: make this machine the reference implementation before writing an installer.

## Rule

No automation should be considered final until it has been tested manually here and documented.

## Checklist

### 1. Baseline inventory

- [ ] OS version and repos
- [ ] niri version
- [ ] DMS version/source/release
- [ ] Qt5/Qt6 packages installed
- [ ] KDE Frameworks apps installed
- [ ] Portal backends installed
- [ ] Flatpak apps installed
- [ ] NVIDIA driver/runtime versions
- [ ] XWayland / xwayland-satellite status

### 2. Portal strategy

Test and decide preferred backends for:

- [ ] FileChooser
- [ ] OpenURI
- [ ] Secret
- [ ] Screenshot
- [ ] ScreenCast
- [ ] Settings
- [ ] RemoteDesktop, if available

Candidate strategy:

```ini
[preferred]
default=kde;wlr;gtk;
org.freedesktop.impl.portal.FileChooser=kde;
org.freedesktop.impl.portal.OpenURI=kde;
org.freedesktop.impl.portal.Secret=kde;
org.freedesktop.impl.portal.ScreenCast=wlr;
org.freedesktop.impl.portal.Screenshot=wlr;
```

Fallback if KDE FileChooser fails:

```ini
org.freedesktop.impl.portal.FileChooser=gtk;
```

Test apps:

- [ ] Zen download dialog
- [ ] Dolphin open/save behavior
- [ ] Flatpak file picker
- [ ] screenshot tool
- [ ] OBS or screen recording
- [ ] Sunshine/Moonlight if relevant

### 3. KDE/Qt app baseline

Install/test:

- [ ] Dolphin
- [ ] Kate
- [ ] Okular
- [ ] Gwenview
- [ ] Ark
- [ ] KCalc or Qalculate
- [ ] Filelight
- [ ] KWalletManager or selected secrets UI
- [ ] Discover or Warehouse/GNOME Software

Validate:

- [ ] launch from menu
- [ ] theme consistency
- [ ] file associations
- [ ] thumbnails
- [ ] trash works
- [ ] removable drives appear
- [ ] network locations if needed

### 4. Admin utility baseline

Install/test:

- [ ] nm-connection-editor
- [ ] blueman
- [ ] pavucontrol
- [ ] qpwgraph or helvum
- [ ] gnome-disk-utility
- [ ] gparted
- [ ] firewall-config
- [ ] system-config-printer
- [ ] simple-scan
- [ ] Flatseal
- [ ] Gear Lever
- [ ] MenuLibre

### 5. Wayland essentials

Install/test:

- [ ] fuzzel
- [ ] swaync or DMS notifications
- [ ] wl-clipboard
- [ ] cliphist
- [ ] grim
- [ ] slurp
- [ ] swappy
- [ ] wf-recorder
- [ ] swayidle
- [ ] swaylock or gtklock
- [ ] polkit agent autostart
- [ ] secrets/keyring autostart

### 6. Remote desktop

Test and document:

- [ ] Sunshine host on niri
- [ ] capture backend: KMS vs wlr
- [ ] encoder: NVENC vs software
- [ ] Moonlight client settings
- [ ] RustDesk fallback behavior
- [ ] Remmina client availability

### 7. DMS integration opportunities

Document what should become UI later:

- [ ] portal selector
- [ ] menu editor
- [ ] default terminal picker
- [ ] default file manager picker
- [ ] app launch repair
- [ ] theme bridge
- [ ] service autostart manager
- [ ] remote desktop center

## Output of this phase

- `profiles/fedora/packages-approved.md`
- `profiles/fedora/mango-baseline.md`
- `configs/` candidate files
- `tests/phase-1-test-results.md`
- `notes/decisions.md`
- `scripts/dms-workstation-health`
- `scripts/apply-mango-baseline`
