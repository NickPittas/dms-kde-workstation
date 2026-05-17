# Mango Recovery Hardening Plan

This plan fixes the installation and first-run failures without changing the project goal.

## Problem Statement

The current project is not safe for a fresh user:

- a user can install Mango, switch sessions, and land in an empty Mango desktop
- DMS installation and startup ownership are not explained clearly enough
- portal, environment, and compositor prerequisites are not enforced before session switch
- keybinding ownership is duplicated between Mango, DMS, and this app
- machine-local fixes were promoted into the baseline without proving they generalize
- app-specific launcher hacks were used where global or canonical fixes are required
- the app reports too little when critical system actions fail

## Requirements

1. Assume the user has **no Linux experience**.
2. The user must be able to run **one guided setup app from a currently working session**.
3. The app must configure the required baseline **before** the user switches to Mango.
4. The app must block unsafe progression when hard prerequisites are missing.
5. DMS-owned settings must be changed through **DMS-owned files/flows**, not parallel conflicting storage.
6. Mango-owned settings must be changed through **Mango config / Mango-supported mechanisms**.
7. Environment and portal handling must follow compositor and portal best practices, not local guesswork.
8. App-specific fixes must be optional exceptions, not baseline assumptions.
9. Every critical action must provide **clear success/failure guidance**.
10. Recovery paths must be documented before any risky action is encouraged.

## Architecture Ownership

### DMS owns
- shell startup model
- shell UI, tray, quickshell plugins
- DMS IPC-facing keybind actions
- theme/color export workflow
- DMS settings.json and other DMS-managed shell state

### Mango owns
- compositor startup
- compositor keybindings
- layouts, tags, input, window rules, animation, exec/autostart lines
- compositor environment import behavior
- compositor-supported portal routing files

### This app owns
- preflight validation
- safe baseline deployment
- guided install instructions
- validation and repair tooling
- Mango-side controls where Mango is the single source of truth
- opening DMS settings when a setting belongs to DMS
- writing DMS-managed files only when using the same canonical storage DMS uses

### This app must not own
- duplicate keybinding systems that conflict with DMS or Mango
- user-app-specific launcher hacks as baseline behavior
- silent admin actions
- machine-specific assumptions presented as universal defaults

## Research Notes

### Mango
- Mango config lives at `~/.config/mango/config.conf`.
- Mango portal configuration prefers `~/.config/xdg-desktop-portal/mango-portals.conf`.
- Mango docs warn that newer Mango versions already handle environment sync for portals; redundant `dbus-update-activation-environment` lines should be avoided when Mango already provides this.

### DMS
- DMS docs recommend **systemd user service** startup when session integration supports it.
- DMS docs warn not to run both systemd-managed DMS and compositor `dms run` startup at the same time.
- For Mango-like compositors, DMS docs still treat manual compositor startup as a valid fallback when per-session systemd binding is not clean.

### Portal / systemd environment
- xdg-desktop-portal-wlr guidance says `XDG_CURRENT_DESKTOP` and `WAYLAND_DISPLAY` must be visible to dbus/systemd user services before portals activate.
- environment variables set only in shell startup files are not enough for dbus-activated user services.
- environment.d is appropriate for stable session-wide values; dynamic values like `WAYLAND_DISPLAY` must not be hardcoded there.

## Phases

## Phase 1 — Safety Rails and Clear Install Path
Goal: prevent users from switching into a dead Mango session.

Tasks:
- [x] Rewrite README around a **do not switch yet** preflight-first workflow.
- [x] Add exact Fedora instructions for installing DMS and Mango, with source links reflected in docs.
- [x] Add a “What happens if you switch too early” recovery section.
- [x] Make `apply-mango-baseline` fail fast if Mango or DMS prerequisites are missing.
- [x] Make First Run Setup show hard blockers for Mango, DMS, Quickshell, and portal packages.
- [x] Make First Run Setup say clearly: **stay in KDE/niri until all blockers are green**.

## Phase 2 — Ownership and Conflict Cleanup
Goal: stop configuration from fighting itself.

Tasks:
- [ ] Document DMS-vs-Mango-vs-app ownership in repo docs.
- [ ] Audit keybinding creation paths and remove duplicated/conflicting ownership.
- [ ] Ensure DMS-related settings are edited only through DMS-owned storage or by sending the user to DMS.
- [ ] Review autostart/startup ownership and keep one canonical path.

## Phase 3 — Environment and Portal Correctness
Goal: replace fragile local hacks with reproducible session behavior.

Tasks:
- [x] Audit environment.d contents and remove dynamic/session-specific variables from static files.
- [ ] Validate Mango portal guidance against repo overrides and update accordingly.
- [ ] Ensure the app can explain which environment values require logout vs live reload.
- [ ] Add checks for portal package presence, portal files, and active user services.

## Phase 4 — Generalize App Launch and Toolkit Behavior
Goal: stop assuming the user has the same apps as the maintainer.

Tasks:
- [ ] Identify hardcoded app-specific launch fixes.
- [ ] Replace baseline launcher hacks with global environment/toolkit fixes where possible.
- [ ] Keep app-specific fixes only as explicit optional recipes/presets.
- [ ] Separate workstation baseline behavior from optional personal app tweaks.

## Phase 5 — User Guidance, Failure Handling, and Validation
Goal: make the system understandable and recoverable.

Tasks:
- [ ] Improve error messaging for admin tasks and failed checks.
- [ ] Add novice-friendly explanations for every critical page action.
- [ ] Add a guided verification checklist after apply.
- [ ] Run fresh-machine validation and record results.

## First Implementation Slice

Start with the lowest-risk, highest-impact fixes:

1. [x] recovery plan + task tracker
2. [x] README install-flow rewrite
3. [x] First Run Setup blocker model
4. [x] baseline script hard prerequisite checks

## Verification Standard

A change is only accepted if it answers:

- Can a novice follow it without guessing?
- Does it stop the user from entering Mango too early?
- Does it use the canonical owner for the setting?
- Does it fail loudly with recovery advice?
- Does it avoid assuming specific personal apps are installed?
