# NeonPlan 3D (fork) – notes for Claude

- This is `tobsen1302/neonplan3d`, a fork of `Mastershort/neonplan3d` (MIT). Keep the original copyright notice in LICENSE. Talk to the user in German; code, identifiers and comments in English.
- Domain `neonplan3d`, minimum Home Assistant 2025.1. The original's private plan (`private/docs/`) is not part of the fork.
- Fork-specific: Pro add-ons listed in `FORK_INCLUDED` (`frontend/src/features.ts`) are unlocked without a pack.
- Frontend lives in `frontend/` (Lit 3 + TypeScript, no decorators; three.js in a separate lazily loaded bundle).
  Bundles are committed to `custom_components/neonplan3d/frontend/`, and CI fails when they are stale, so run `npm run build` before committing.
- Checks: `npm test`, `npm run typecheck`, `npm run build` (size budgets), `ruff check` / `ruff format`.
  HA integration tests only run in the Linux CI.
- Visual self-check: `npm run screenshot` renders `preview/index.html` (invented demo data, mock hass) into `preview/screenshots/`.
- Deploy to the user's HA: `npm run deploy` (target in the untracked `deploy.local.json`). Never commit real floor plans, IPs or device names.
- After each change set: bump the version in `manifest.json`, add a CHANGELOG entry, commit, push, check CI, and tell the user in German what is new and how to test it.
