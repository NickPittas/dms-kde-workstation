# DMS + Mango/Niri on Fedora: A Real-World Report From Someone Who Let an LLM Fix His Desktop for 3 Weeks

**TL;DR:** I came from KDE/GNOME/Windows expecting to "install a desktop" and ended up learning what a compositor actually is. I built a companion app, iterated an installer 20+ times, and documented every gap between "it compiled" and "I can actually work." Here's my honest journal.

**Repo:** https://github.com/NickPittas/dms-kde-workstation

---

## What I Wanted

- **Compositor:** A tiling/scrolling Wayland compositor that actually works with creative apps (Blender, Nuke)
- **Shell:** DankMaterialShell (DMS) because it's the most visually polished Quickshell-based desktop shell out there
- **Apps:** KDE/Qt-first stack (Dolphin, Okular, Gwenview, etc.)
- **Theming:** One button to export GTK + Qt themes from DMS
- **Settings:** A real GUI to configure things, not editing `.conf` files

## The Stack I Ended Up With

| Component | Role | Verdict |
|-----------|------|---------|
| **MangoWM** | Wayland compositor (replaced niri) | ✅ DnD works, fast, good animations |
| **DMS** | Shell/bar/theme/panel | ✅ Gorgeous, actively maintained |
| **Quickshell** | DMS's runtime | ✅ Invisible when it works |
| **Qt/PySide6** | My companion settings app | ✅ Had to build it myself |
| **grim/slurp/swappy** | Screenshots | ✅ Better than Spectacle for non-Plasma |

---

## The Good

### 1. Mango fixed what niri couldn't

Under **niri**, drag-and-drop from Dolphin into Nuke/Blender simply didn't work. Under **Mango**, it works out of the box. That was the single deciding factor for switching compositors. Mango also has hot-reload for config changes, which niri doesn't.

### 2. DMS is genuinely beautiful

The matugen-based dynamic theming, the tray, the OSD popups, the overview dashboard — this is the nicest-looking Linux desktop shell I've used. It's not just a bar; it's a complete desktop environment surface.

### 3. The companion settings app became real

Since DMS Settings doesn't have native Mango panels (Window Rules, Keybinds, Startup Apps, etc.), I built a PySide6 companion app that fills those gaps:

- First Run Setup with hard prerequisite gating
- Window Rules with `lswt`-based open-window picker
- Startup Apps that launch after DMS tray is ready
- Theme Bridge for fonts
- SDDM autologin consolidation

It's not native DMS integration, but it's a real GUI that non-terminal users can navigate.

### 4. The installer is now idempotent and safe

After ~20 iterations of "recovery hardening," the baseline installer:
- Detects if prerequisites are missing and refuses to proceed
- Preserves existing Mango/DMS config on re-runs
- Reports every failure with a concrete fix command
- Blocks dangerous operations (like `dnf install` inside Ghostty, which crashes the terminal)

---

## The Bad

### 1. You need to understand ownership

DMS, Mango, and your settings app all want to write to the same config files. Who starts DMS? Is it `dms.service`? Is it Mango's `exec-once`? Is it the settings app? **Getting this wrong means double-starting DMS or starting nothing at all.**

I documented the ownership model in the repo, but it took multiple broken sessions to learn it.

### 2. Tray icons are a diagnosis, not a feature

Dropbox, Sunshine, and other apps don't "just appear" in the DMS tray under Mango. You need:
- `xembedsniproxy` running
- Services restarted with the correct session environment
- A 5-second settle delay after `StatusNotifierWatcher` appears

This isn't DMS's fault — it's Wayland session environment propagation being fragile. But it's not documented anywhere obvious.

### 3. Portal configuration is mandatory and weird

Fedora's `xdg-desktop-portal.service` depends on `graphical-session.target`, which doesn't exist in a Mango session. You need a user override to remove that dependency. Without it, file choosers, screen sharing, and Flatpak integration break.

### 4. The LLM can't test what it writes

I used an LLM (via the **pi coding agent harness**) to iterate on this project. It could write scripts, edit Python, refactor the settings app, and generate documentation. **But it could not:**
- Log into Mango and see if DMS actually launched
- Test drag-and-drop into Blender
- Verify that a tray icon appeared
- Catch that `strftime("%Y%m%d-%H%M%S")` got corrupted by a naive `sed` replacement

Every fix had to be validated by a human (me). The loop was: LLM writes → I test → it breaks → I describe symptoms → LLM tries again. Some iterations took hours.

---

## The Ugly

### 1. Running `dnf install` inside Ghostty crashes your terminal

Ghostty crashes with a fontconfig SEGV when `dnf` rebuilds font caches. If you're SSH'd into a remote machine via Ghostty and run the installer, your terminal dies mid-install and the machine is left in an unknown state. We had to add explicit Ghostty detection to the installer to prevent this.

### 2. `lswt` doesn't exist in Fedora repos

To get window app IDs for the Window Rules page, we needed `lswt` (list Wayland toplevels). Fedora doesn't package it. The installer now builds it from source automatically, but that's a `git clone` + `make` + `sudo make install` just to get a window list.

### 3. DMS Settings tabs are compositor-gated

DMS has a Keybinds tab and a Window Rules tab in its native Settings. **But:**
- Keybinds only enable if the compositor is detected as niri/Hyprland/DWL (Mango reports as DWL, so this works)
- Window Rules only enable for niri/Hyprland, **not Mango**

This means DMS's own Window Rules editor is hidden under Mango. You have to use our companion app or edit `windowrule=` lines by hand.

### 4. Qt theming needs a bridge

DMS exports matugen themes for GTK3/4 and Qt5/6, but Qt apps need `qt5ct`/`qt6ct-kde` installed **before** the export, and they need explicit `[Fonts]` sections in the qtct configs. If you miss this step, Qt apps come up white or checkerboard-patterned.

---

## What I Wish I Knew Before I Started: A Journal of Discovery

This section is for anyone coming from Windows, Ubuntu, Pop!_OS, or Fedora KDE/GNOME — full desktop environments where "install the DE" means you get a panel, app launcher, file manager, settings app, and screenshot tool all at once.

**Here's what I didn't understand:** Niri, Mango, and Hyprland are **compositors** (window managers). They manage windows. That's it. They don't ship with app launchers, file chooser portals, tray managers, or screenshot tools. KDE and GNOME do — because they're **desktop environments**, not just window managers.

This isn't a failing of the compositor developers. It's a mismatch between my expectations ("I installed a desktop, where's the rest of it?") and what I actually installed ("I installed a window manager, I need to build the rest myself").

Here are the specific discoveries that cost me the most time.

### Discovery 1: "Install the compositor" ≠ "you have a desktop"

**My expectation:** Install Mango, log in, and have a working desktop like KDE.

**What happened:** Gray screen. Mouse cursor. Nothing else. No bar. No launcher. No terminal keybind. No way to open anything.

**What I learned:** The "default config" that Mango docs mention assumes you already installed `rofi`, `ghostty`, `waybar`, and configured keybinds for all of them. I had none of those. I was staring at a gray screen with no escape hatch.

**The fix:** Drop to a TTY (Ctrl+Alt+F3), log in with your username/password, and edit `~/.config/mango/config.conf` from the terminal. You need at least one `bind=` line that launches a terminal you actually have installed. Without that, you can't fix anything from inside the session.

**What would have helped:** A note in the install docs saying "before you log in, make sure you have at least one terminal installed and one keybind configured to launch it."

### Discovery 2: DMS doesn't start itself

**My expectation:** `sudo dnf install dms` means DMS will start when I log in.

**What happened:** I installed DMS, logged into Mango, and... still gray. DMS never appeared. I thought it was broken.

**What I learned:** DMS has a systemd user service (`dms.service`) that auto-starts under KDE/Plasma because Plasma provides `graphical-session.target`. Mango doesn't. You need to explicitly tell Mango to start DMS via an `exec-once=` line in the Mango config.

**The fix:** Add this to `~/.config/mango/config.conf`:
```
exec-once=env QT_QPA_PLATFORMTHEME=qt6ct QT_QPA_PLATFORMTHEME_QT6=qt6ct dms run
```

**The trap I fell into:** I enabled `dms.service` AND added the `exec-once` line. DMS started twice. Some parts worked, some didn't. There was no error message saying "DMS is running twice." It just acted weird.

**What would have helped:** A single sentence: "Under non-Plasma compositors, disable `dms.service` and use `exec-once` in your compositor config instead."

### Discovery 3: "Reboot if you have issues" is dangerous advice

**My expectation:** If something's broken, reboot and it'll fix itself.

**What happened:** I set SDDM autologin to Mango. Mango config was broken. Reboot → still broken. Reboot again → still broken. I was locked out of my desktop.

**What I learned:** There is no "safe mode" for Mango. If your config is broken and autologin is enabled, every reboot puts you back in the same broken session. Your only escape is a TTY.

**The fix:** Before enabling autologin, test the session manually first. Log in via SDDM without autologin, so you can always switch back to KDE if Mango breaks.

### Discovery 4: File choosers are invisible failures

**My expectation:** Install Blender, open file dialog, pick a file.

**What happened:** Nothing. No dialog. No error. Blender just... didn't open the file. I thought Blender was broken.

**What I learned:** File choosers on Wayland go through `xdg-desktop-portal`. Fedora's portal service depends on `graphical-session.target`, which doesn't exist in Mango sessions. The portal is technically running but blocked waiting for a target that never arrives.

**The fix:** Create a systemd user override that removes the `graphical-session.target` dependency:
```
mkdir -p ~/.config/systemd/user
systemctl --user edit xdg-desktop-portal.service
# add: [Unit] After=default.target
```

**What would have helped:** A note saying "if file choosers don't appear, check portal service dependencies."

### Discovery 5: niri's drag-and-drop doesn't work with Blender/Nuke

**My expectation:** Drag a texture from Dolphin into Blender. It works on every other desktop.

**What happened:** The drag cursor shows 🚫. Nothing drops. No error, no log, no diagnostic.

**What I learned:** Different compositors implement DnD protocols differently. Niri's implementation doesn't support the specific protocol that Blender and Nuke use for drag-and-drop. This isn't a bug — it's just how that compositor works. But there's no way to discover this except by trying it.

**The fix:** Switch to Mango, where DnD works with these apps. (This was my main reason for switching.)

### Discovery 6: Keyboard layouts don't migrate from KDE

**My expectation:** I set US + Greek in KDE settings with Alt+Shift toggle. It'll work in Mango too.

**What happened:** Alt+Shift did nothing.

**What I learned:** Compositor-level keyboard layouts are separate from DE-level keyboard settings. Mango doesn't read KDE's settings. You need explicit `bind=` lines in Mango's config.

**The fix:** Add to Mango config:
```
bind=ALT,Shift_L,spawn,switch_keyboard_layout
```

### Discovery 7: Qt apps need a "theme bridge"

**My expectation:** Open Dolphin. It looks like Dolphin.

**What happened:** White background, black text, checkerboard patterns, missing icons. It looked like a broken Windows 95 app.

**What I learned:** Outside Plasma, Qt apps don't know which theme engine to use. You need `qt5ct`/`qt6ct-kde` installed, plus `QT_QPA_PLATFORMTHEME=qt6ct` set in your environment. DMS can export the theme to qtct, but only if those packages are installed *before* the export.

**The fix:**
1. Install `qt5ct qt6ct-kde`
2. Set `QT_QPA_PLATFORMTHEME=qt6ct` in `~/.config/environment.d/`
3. Export DMS Theme/Colors once

**What would have helped:** "Before exporting themes, install qt5ct and qt6ct-kde or Qt apps will look unstyled."

### Discovery 8: Tray icons fail silently

**My expectation:** Install Dropbox. See a tray icon.

**What happened:** Dropbox started. No tray icon. No error.

**What I learned:** Tray icons on Wayland are a multi-layer protocol stack. The app needs to register a StatusNotifier item. The shell needs a StatusNotifierWatcher. For XEmbed tray icons, you need `xembedsniproxy`. The app might start before the environment is ready. Any of these failing means no icon — with no error message.

**The fix:** A post-startup helper that waits for DMS tray to be ready, then restarts tray-sensitive services.

### Discovery 9: Window Rules have no GUI under Mango

**My expectation:** DMS Settings has a Window Rules tab. I can click and configure rules.

**What happened:** The tab exists in DMS Settings, but it's **hidden** under Mango because DMS only enables it for niri/Hyprland.

**What I learned:** DMS's native Window Rules UI is compositor-gated. Mango isn't in the list.

**The fix:** Edit `windowrule=` lines in `~/.config/mango/config.conf` by hand, or use a companion app.

### Discovery 10: Autostart `.desktop` files don't start

**My expectation:** Put `.desktop` files in `~/.config/autostart/`. They start on login.

**What happened:** systemd generated the services, but they depend on `graphical-session.target`, which Mango doesn't provide. The services are "started" but blocked.

**What I learned:** Compositors don't automatically provide the systemd targets that KDE/GNOME do.

**The fix:** A post-startup helper that explicitly launches apps after the UI is ready.

### Discovery 11: Screenshots need a whole toolchain

**My expectation:** Press Print Screen. Get a screenshot.

**What happened:** Nothing. Spectacle opened and crashed because it "needs Plasma."

**What I learned:** Under a non-Plasma session, you need to assemble your own screenshot pipeline: `grim` for capture, `slurp` for region selection, `swappy` for editing. Each has its own flags.

**The fix:** Install `grim slurp swappy`, write wrapper scripts, bind them to Print Screen in Mango config.

---

## What I Learned

---

## What I Learned

1. **Compositor choice matters more than shell choice for creative workflows.** DnD is a compositor feature, not a shell feature.
2. **Environment propagation is the hardest part of Wayland sessions.** `environment.d`, `dbus-update-activation-environment`, `systemctl import-environment`, and compositor `exec-once` all interact in confusing ways.
3. **LLMs are great for structured iteration, terrible for integration testing.** Use them for code generation and refactoring, not for validating that a desktop session actually works.
4. **Idempotent installers are worth the effort.** Being able to re-run the baseline safely after a failure saved the project multiple times.
5. **Don't ship personal defaults as universal defaults.** Your browser, editor, and sync services are not everyone's defaults. The baseline should be neutral.

---

## Should You Try This?

**If you want:**
- A beautiful, themed Wayland desktop with DMS
- Working DnD for creative apps
- KDE/Qt app integration
- A GUI-first setup experience

**And you are comfortable with:**
- Fedora + COPR repos + Terra repo
- Reading logs when things don't start
- Occasionally dropping to a TTY to fix a broken session
- Contributing issues back to DMS/Mango upstream

**Then yes.** Clone the repo, run the readiness check, and follow the First Run Setup. It's a journey, but it's a rewarding one.

**If you want:**
- Something that works out of the box with zero config
- A "Next Next Finish" installer experience
- Someone else to handle tray icons, portals, and startup apps for you

**Then use KDE or GNOME.** That's what they're for. Compositors like Mango and niri are building blocks, not finished products. They're for people who want to assemble their own desktop — and who don't mind learning how the pieces fit together.

That said, both DMS and Mango are actively improving, and the gap between "compositor" and "usable desktop" is getting smaller every release.

---

## The Repo

https://github.com/NickPittas/dms-kde-workstation

It includes:
- Idempotent baseline installer
- Pre-switch readiness checker
- Post-login health checker
- PySide6 companion settings app
- `lswt` auto-install
- Documentation on every workaround and failure mode

---

*Built with a lot of patience, some broken sessions, and an LLM that couldn't see the screen but helped me document everything I learned along the way.*
