# DMS + Mango/Niri on Fedora: A Real-World Report From Someone Who Let an LLM Fix His Desktop for 3 Weeks

**TL;DR:** I wanted a KDE-integrated Wayland workstation with a nice shell, working drag-and-drop for creative apps, and a GUI settings surface. I ended up building a whole companion app, 20+ installer iterations, and learning more about `xdg-desktop-portal` than I ever wanted to. Here's the honest report.

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

## What The Official Docs Don't Tell You (Or: What Would Have Happened Without Help)

This is the part I wish existed when I started. Here's what happens if you follow the "standard" install path for each component.

### Following Mango's official install instructions

Mango's docs say: install COPR, install `mangowm`, reboot, copy the default config to `~/.config/mango/config.conf`.

**What actually happens:** You log in and see a **gray screen with a mouse cursor. Nothing else.** No bar, no launcher, no terminal keybind, no way to open any app. You're stuck. The default config assumes you have `rofi`, `ghostty`, `waybar`, and a dozen other tools already installed and configured. If you don't, you have no way to launch anything.

**Recovery:** Drop to a TTY (Ctrl+Alt+F3), log in, and edit the config from the terminal. But you need to know which apps you actually have installed, which key codes Mango accepts, and how to reload the config without logging out.

### Installing DMS separately

DMS docs say: `sudo dnf copr enable avengemedia/dms && sudo dnf install dms`. Done.

**What actually happens:** DMS is installed but **never starts under Mango.** DMS has a systemd user service (`dms.service`) that works under KDE/Plasma, but under Mango you need an explicit `exec-once=env QT_QPA_PLATFORMTHEME=qt6ct QT_QPA_PLATFORMTHEME_QT6=qt6ct dms run` in your Mango config. Without that line, you get the gray screen forever.

**Worse:** If you enable `dms.service` AND add the `exec-once` line, DMS starts twice and breaks. There's no error message — the shell just acts weird.

### The reboot trap

Mango docs say "reboot if you have issues."

**What actually happens:** If your config is broken, rebooting just puts you back in the same broken state. If SDDM autologin is set to Mango and Mango is broken, you **can't get back to a working desktop without editing config files from a TTY.** There is no "safe mode" or fallback.

### File choosers silently fail

You install Blender or a Flatpak app. You try to open a file. The file chooser either:
- Doesn't appear at all
- Appears but can't see your home directory
- Crashes the app

**Why:** Fedora's `xdg-desktop-portal.service` depends on `graphical-session.target`, which doesn't exist in Mango sessions. You need a systemd user override to remove that dependency. This is **not mentioned** in Mango docs, DMS docs, or Fedora docs. You just think your app is broken.

### Drag-and-drop under niri

You install niri because it has great DMS integration. You install Blender. You try to drag a texture from Dolphin into Blender.

**What happens:** Nothing. The drag cursor shows a 🚫. No error message, no log, no indication why.

**Why:** niri's DnD implementation doesn't support the specific protocol Blender/Nuke use. This is a compositor limitation, not an app bug. You only discover this after hours of searching. (Mango fixed this — that's why I switched.)

### Keyboard layout switching

You have US + Greek layouts. Under KDE, Alt+Shift just works. Under Mango:

**What happens:** Alt+Shift does nothing. Or it only switches in some apps. Or it switches but the indicator doesn't show the change.

**Why:** Mango needs explicit `switch_keyboard_layout` binds in its config, plus `xkeyboard-config` layout definitions. KDE's settings don't propagate to the compositor. You have to hand-edit `bind=` lines.

### Qt apps look like garbage

You open Dolphin, Okular, or any KDE app. It looks like this:
- White background with black text
- Checkerboard pattern in some widgets
- Wrong font, wrong colors, no icons

**Why:** Outside Plasma, Qt apps don't know which theme engine to use. You need `qt5ct` and `qt6ct-kde` installed, plus `QT_QPA_PLATFORMTHEME=qt6ct` in your environment. DMS can export the theme, but only if those packages exist *before* the export. There's no error message — apps just look wrong.

### Tray icons

You install Dropbox, Sunshine, or any app with a tray icon. It starts. You see nothing in the DMS tray.

**Why:** Multiple reasons, all invisible:
1. The app started before the session environment was fully propagated
2. `xembedsniproxy` isn't running (needed for XEmbed tray icons)
3. The app registered a StatusNotifier item but DMS's `StatusNotifierWatcher` wasn't ready yet
4. The app just doesn't support StatusNotifier at all

You don't get "tray icon failed to register." You get **silence.**

### Window Rules under Mango

You want Ghostty to be transparent or Pavucontrol to float. DMS has a Window Rules tab... which is **hidden** under Mango because DMS only enables it for niri/Hyprland.

**Your option:** Edit `windowrule=` lines in `~/.config/mango/config.conf` by hand. The syntax is `windowrule=property:value,appid:com.example.app`. Get one comma wrong and the rule is silently ignored. There's no validation, no feedback, no GUI.

### Startup apps

You put `.desktop` files in `~/.config/autostart/`. You log into Mango. They don't start.

**Why:** systemd generates `app-foo@autostart.service` units for those, but they depend on `graphical-session.target`, which Mango doesn't provide. Your apps are technically "started" but blocked waiting for a target that never arrives. You need an explicit post-startup helper that waits for DMS to be ready, then launches them.

### Screenshots

You press Print Screen. Nothing happens. Or Spectacle opens and immediately crashes because it "needs Plasma."

**Why:** Spectacle is a Plasma app. Under a non-Plasma session, you need `grim` (capture), `slurp` (region select), and `swappy` (editor). Each has its own flags, and `slurp`'s selection overlay looks weird under Mango unless you tune the opacity. You have to build the whole toolchain yourself.

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

**Then yes.** Clone the repo, run the readiness check, and follow the First Run Setup.

**If you want:**
- Something that works out of the box with zero config
- Guaranteed tray icons for every app
- Native Mango support in DMS Settings

**Then wait.** Both DMS and Mango are actively improving, but the integration between them still has rough edges that require workarounds.

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

*Built with a lot of patience, `git commit`, and an LLM that couldn't log into Mango but tried really hard anyway.*
