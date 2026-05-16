# Drag-and-drop investigation

Date: 2026-05-16

## User report

Drag and drop does not work between applications:

- Dolphin → Zed
- Dolphin → Obsidian
- Dolphin → Nuke

This may be a serious blocker for the DMS KDE Workstation project if it is a niri/compositor-level limitation.

## Initial findings

### Relevant app display stacks

Current Flatpak permissions:

#### Zed

```text
sockets=fallback-x11;gpg-agent;pulseaudio;ssh-auth;wayland;x11;
filesystems=home;
```

Zed has both Wayland and X11 access and home filesystem access.

#### Obsidian

```text
sockets=pulseaudio;ssh-auth;x11;
filesystems=home;/media;/mnt;/run/media;...
```

Obsidian currently has X11 but **not Wayland** permission. Under niri, this likely means Obsidian is running through XWayland / xwayland-satellite.

#### Zen

```text
sockets=cups;fallback-x11;pcsc;pulseaudio;wayland;x11;
```

Zen has both Wayland and X11 access.

#### Nuke

Not yet inspected in this project, but Nuke commonly uses Qt/X11/XWayland behavior. It may be affected by the same XWayland drag-and-drop path.

### xwayland-satellite

Installed version:

```text
xwayland-satellite-0.8.1-1.fc44
```

niri uses xwayland-satellite for X11 apps.

## Online research summary

Search results show multiple relevant upstream issues/discussions:

- niri discussions/issues about drag and drop between windows.
- niri issue about drag/drop shifting focus.
- niri issue about drag and drop from Nautilus into Zen.
- xwayland-satellite issues about XWayland ↔ Wayland drag-and-drop not working.
- xwayland-satellite issues affecting apps such as Bitwig, Unity, DaVinci Resolve.

Initial interpretation:

- Drag-and-drop between native Wayland apps may work depending on app/toolkit/compositor behavior.
- Drag-and-drop between Wayland and XWayland apps is likely fragile or broken in some cases.
- Obsidian and Nuke are likely XWayland-side cases.
- If Dolphin → Zed fails while Zed is native Wayland, that may point closer to niri or app-specific behavior.

## Why this matters

A workstation environment must support drag-and-drop reliably. If niri/xwayland-satellite cannot provide this for common workflows, then DMS KDE Workstation has three possible paths:

1. Document it as a known limitation and continue.
2. Provide app-specific workarounds, such as forcing Electron apps to Wayland.
3. Decide niri is not acceptable for this workstation profile and use a different compositor/session base.

## Tests needed

Create a simple file:

```bash
echo test > ~/dms-dnd-test.txt
```

Then test these combinations:

| Source              | Target               | Expected                                  | Result |
| ------------------- | -------------------- | ----------------------------------------- | ------ |
| Dolphin             | Dolphin other window | file move/copy works                      | TODO   |
| Dolphin             | Kate                 | file opens or path inserts                | TODO   |
| Dolphin             | Zed                  | file opens in editor                      | TODO   |
| Dolphin             | Zen upload/drop area | file accepted                             | TODO   |
| Dolphin             | Obsidian             | file/link accepted                        | TODO   |
| Dolphin             | Nuke                 | file accepted/imported                    | TODO   |
| Dolphin             | terminal             | path/text appears if terminal supports it | TODO   |
| Zen downloaded file | Dolphin              | works if browser supports drag out        | TODO   |

Important test control:

- Focus the source window first before dragging.
- Then test dragging from an unfocused source window.
- niri has reports around drag from unfocused windows.

## Possible workarounds to evaluate

### 1. Force Electron apps to Wayland

For Obsidian, test adding Wayland socket permission and Electron Wayland flags. Example concepts, not yet applied:

```bash
flatpak override --user --socket=wayland md.obsidian.Obsidian
```

Potential Electron flags may include:

```text
--enable-features=UseOzonePlatform,WaylandWindowDecorations
--ozone-platform=wayland
```

Need a safe Flatpak-specific way to test without permanently breaking launch.

### 2. Keep drag/drop workflows inside KDE apps where possible

Dolphin → Kate/Okular/Gwenview may be more reliable than Dolphin → XWayland apps.

### 3. Avoid XWayland for pro apps where possible

If Nuke supports native Wayland/Qt Wayland reliably, test that. If not, this remains a blocker.

### 4. Track upstream niri/xwayland-satellite fixes

Since xwayland-satellite 0.8.1 is installed, check if newer versions fix drag/drop issues before concluding permanently.

## Current status

Not resolved. Needs manual testing.

This issue is potentially project-critical.

## Manual test results: 2026-05-16

| Source | Target | Result | Notes |
|---|---|---|---|
| Dolphin | Dolphin | PASS | Drag/drop works. |
| Dolphin | Zed | PASS | Drag/drop works. |
| Dolphin | Obsidian | FAIL | Does not work. Obsidian is likely XWayland/Electron path. |
| Dolphin | Nuke | FAIL | Does not work. Nuke likely uses problematic Qt/X11/XWayland/proprietary path. |

Updated interpretation:

Drag/drop is not globally broken in niri. It works between Dolphin and Zed, and between Dolphin windows. The failures are likely related to XWayland/Electron/proprietary-app behavior, not a universal compositor failure.

This is still project-critical because Nuke is a core professional app.
