# Mango startup and settings hardening plan

Date: 2026-05-16
Status: Active

## Goal

Fix remaining Mango workstation reliability and UX issues without duplicating DMS startup responsibilities.

## Principles

- DMS remains the owner of its shell/bar/tray host/theme systems.
- Mango profile only fills gaps DMS does not cover under Mango.
- Every persistent change must be documented for future installer/profile work.
- GUI pages must be actual controls, not text-file editing inside a window.
- External KDE settings modules must be treated as helper tools with clear scope, not assumed to configure Mango.

## Task list

### Startup/tray reliability

- [x] Inspect DMS startup/systemd/deployer behavior and document ownership.
- [x] Create `docs/startup-ownership-mango-2026-05-16.md`.
- [x] Replace raw Mango tray-service restarts with an additive post-DMS helper that:
  - imports current Mango env,
  - waits for DMS/StatusNotifierWatcher,
  - starts `xembedsniproxy` if missing,
  - restarts only configured tray-sensitive user apps,
  - verifies real tray registration.
- [x] Store tray-sensitive apps in a user-editable config file for the GUI/installer.
- [x] Update health check to validate the helper and config.

### Settings GUI UX

- [x] Redesign Keybindings page as a real form-based editor.
- [x] Redesign Startup page around categories.
- [x] Redesign Default Apps page with per-category app dropdowns.
- [x] Redesign Login page with explicit autologin state and verification.
- [x] Add scope labels for external KDE tools.
- [x] Wrap external Qt/KDE tools in a themed launcher environment.

### Mango settings completeness

- [x] Inspect Mango docs/default config for animation options and supported layout values.
- [x] Add missing animation options (fade, none) and curve editor/presets.
- [x] Add font bridge page for DMS/KDE/GTK/Qt font sync.
- [ ] Add missing Overview/hot area/scratchpad/color settings where supported.

### Installer/profile documentation

- [x] Update `profiles/fedora/mango-baseline.md` with startup ownership and helper requirements.
- [x] Update `scripts/apply-mango-baseline` to deploy new helper/config when validated.
- [x] Add smoke test script `scripts/test-mango-settings-smoke`.
- [x] Add reboot verification script `scripts/test-reboot-verification`.
- [ ] Update manual test matrix with reboot tray tests, startup tests, default-app tests, autologin tests.

### Fixes discovered during implementation

- [x] Fix Kate hardcoding: config file buttons now use xdg-open to respect default editor.
- [x] Fix animation type options: added fade and none beyond slide/zoom.
- [x] Fix Mango layout reset on wallpaper change: disabled DMS Mango matugen template post-hook.
- [x] Fix qt5ct/qt6ct missing [Fonts] section: added font bridge.

## Verification checklist

- [ ] Reboot: Dropbox/Sunshine icons appear without manual restart.
- [ ] Adding a new tray-ready startup app works after reboot.
- [ ] Disabling a tray-ready startup app prevents it from starting after reboot.
- [ ] Keybinding editor can add/remove a harmless binding and detect duplicate conflicts.
- [ ] Default Apps page changes XDG defaults and verification reflects it.
- [ ] Login page clearly shows enabled/disabled state after changing autologin.
- [x] Health check reports startup helper/tray state correctly.
