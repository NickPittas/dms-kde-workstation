# DMS KDE Workstation

Goal: turn the lessons from the Noctalia/DankMaterialShell/niri troubleshooting into a reproducible Fedora workstation profile.

This is not meant to be a minimal rice. It is a practical stack:

```text
MangoWM = primary compositor/window management for creative workstation use
DankMaterialShell = shell/panel/theme surface
KDE/Qt apps = workstation application suite
wlr/GTK/KDE portals = file pickers, screenshots/screencast, compatibility
GTK = compatibility fallback, not the primary identity

niri = secondary/experimental profile until Blender/Nuke drag-and-drop is fixed there
```

## Repository layout

```text
docs/        Design docs, architecture, known issues
plans/       Stabilization and implementation plans
profiles/    Fedora package/profile definitions
configs/     Candidate config files to deploy later
scripts/     Future health-check/install/repair scripts
notes/       Field notes and decisions while testing
tests/       Manual test cases and expected results
upstream/    Optional local upstream source checkouts (not tracked in the public repo)
```

## Current status

- This repo contains a validated Mango baseline, installer script, health checks, and the Qt settings app.
- Local upstream checkouts can live under `upstream/`, but they are not part of the public repo.
- Main install path: `scripts/apply-mango-baseline --apply --install-packages`.

## High-level phases

1. Stabilize the reference DMS KDE Workstation.
2. Document every accepted package/config/fix.
3. Maintain health-check and repair scripts.
4. Maintain the Fedora installer/profile.
5. Maintain the Mango Workstation Settings UI.

## Core principle

If a setting requires a terminal command today, the finished stack should either:

1. expose it in DMS Control Center, or
2. open the correct external GUI tool, or
3. run a safe repair action with backup and explanation.
