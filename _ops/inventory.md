# ProjectsHome Inventory Report

**Generated**: 2026-02-18
**Root**: `D:\ProjectsHome`
**Scanner**: Claude Opus 4.6 (Project Consolidation Engineer)

---

## Summary

| Metric | Count |
|--------|-------|
| Top-level directories | 29 |
| Git repositories (local) | 13 |
| Non-repo project folders | 16 |
| GitHub repos (lance-fisher) | 10 |
| Loose root files | 25+ |
| PROJECTS.json entries | 28 |

---

## Inventory Table

### Git Repositories

| # | Project | Local Path | Remote URL | Branch | Last Commit | Dirty | README | CLAUDE.md | Action |
|---|---------|-----------|------------|--------|-------------|-------|--------|-----------|--------|
| 1 | e2ee-messenger | `e2ee-messenger/` | github.com/lance-fisher/e2ee-messenger | main | 2026-02-12 | Y | Y | Y | **Keep** - own repo, active |
| 2 | exo | `exo/` | github.com/lance-fisher/exo | claude/init-scls-uOi0s | 2026-02-08 | Y | Y | N | **Archive** - phone staging repo, projects extracted |
| 3 | frontier-bastion | `frontier-bastion/` | github.com/lance-fisher/exo | claude/rts-game-prototype-FmTk4 | 2026-02-05 | Y | Y | Y | **Repoint** - remote still points to exo, should point to frontier-bastion repo |
| 4 | harmony-medspa | `harmony-medspa/` | github.com/lance-fisher/exo | claude/medspa-mobile-app-AKyo6 | 2026-02-03 | Y | Y | Y | **Repoint** - remote still points to exo, should point to harmony-medspa repo |
| 5 | lancewfisher-v2 | `lancewfisher-v2/` | NONE | master | 2026-02-18 | Y | N | N | **Create remote** - splash page needs GitHub repo |
| 6 | master-trading-system | `master-trading-system/` | NONE | master | 2026-02-14 | Y | Y | Y | **Evaluate** - possible duplicate/successor of master-trade-bot |
| 7 | polymarket-bots | `polymarket-bots/` | github.com/lance-fisher/polymarketbtc15massistant | claude/polymarket-copy-bot-xcdOo | 2026-02-14 | N | Y | N | **Archive/Merge** - branch of polymarketbtc15massistant, likely superseded |
| 8 | polymarketbtc15massistant | `polymarketbtc15massistant/` | github.com/lance-fisher/polymarketbtc15massistant | main | 2026-02-12 | Y | Y | Y | **Keep** - own repo, canonical |
| 9 | tax-prep-system | `tax-prep-system/` | NONE | master | 2026-01-31 | Y | N | N | **Create remote** (pending approval) |
| 10 | trading-profit-engine | `trading-profit-engine/` | github.com/lance-fisher/trading-profit-engine | master | 2026-02-12 | Y | N | Y | **Keep** - own repo, active |
| 11 | _bookmark_bot | `_bookmark_bot/` | NONE | master | no commits | Y | Y | Y | **Convert** - init commits, create remote (pending approval) |
| 12 | openclaw/workspace | `openclaw/workspace/` | nested git | - | - | - | - | - | **Note** - nested git inside non-repo parent |
| 13 | .claude-data plugins | `.claude-data/plugins/...` | nested git | - | - | - | - | - | **Ignore** - Claude internal plugin cache |

### Non-Repo Project Folders

| # | Project | Local Path | Has CLAUDE.md | Has package.json | Has requirements.txt | In PROJECTS.json | Action |
|---|---------|-----------|---------------|-----------------|---------------------|-----------------|--------|
| 1 | auton | `auton/` | Y | N (pyproject) | N | Y | **Convert to repo** |
| 2 | data | `data/` | N | N | N | N | **Archive** - just trading.db (180KB) |
| 3 | galleon-splash | `galleon-splash/` | N | N | N | Y | **Convert to repo** or merge with lancewfisher-v2 |
| 4 | galleon-storm | `galleon-storm/` | N | N | N | N | **Merge** into galleon-splash (variant, single HTML) |
| 5 | home-hub | `home-hub/` | Y | Y | N | Y | **Convert to repo** |
| 6 | JumpQuest | `JumpQuest/` | Y | N | N | Y | **Convert to repo** |
| 7 | lancewfisher-splash | `lancewfisher-splash/` | N | N | N | Y | **Archive** - superseded by lancewfisher-v2 |
| 8 | market-dashboard | `market-dashboard/` | Y | N | N | Y | **Convert to repo** |
| 9 | master-trade-bot | `master-trade-bot/` | Y | Y | N | Y | **Evaluate** - may be superseded by master-trading-system |
| 10 | noco-app-demos | `noco-app-demos/` | Y | Y | N | Y | **Convert to repo** |
| 11 | one-three-net | `one-three-net/` | Y | N | N | Y | **Convert to repo** |
| 12 | openclaw | `openclaw/` | N | N | N | Y | **Archive** - paused, copy of C:\Users\lance\.openclaw |
| 13 | polymarket-sniper | `polymarket-sniper/` | Y | N | Y | Y | **Convert to repo** |
| 14 | profit-desk | `profit-desk/` | Y | N (pyproject) | N | Y | **Convert to repo** |
| 15 | project-hub | `project-hub/` | N | N | N | Y | **Convert to repo** - this IS ProjectHub |
| 16 | solana-bot | `solana-bot/` | Y | Y | N | Y | **Archive** - paused, folded into master-trade-bot |
| 17 | trading-shared | `trading-shared/` | N | N | N | Y | **Keep** - shared docs, not a standalone project |

### Remote-Only GitHub Repos (no local clone found)

| # | GitHub Repo | URL | Default Branch | Private | Local Match | Action |
|---|-------------|-----|---------------|---------|-------------|--------|
| 1 | scls | github.com/lance-fisher/scls | main | N | None | **Investigate** - exo branch extraction? |
| 2 | project-dashboard | github.com/lance-fisher/project-dashboard | main | N | `project-hub/`? | **Investigate** - may be earlier version |
| 3 | mission-control | github.com/lance-fisher/mission-control | main | N | None | **Investigate** - exo branch extraction? |
| 4 | trading-bot | github.com/lance-fisher/trading-bot | main | N | None | **Investigate** - exo branch extraction? |

### Duplicate / Overlap Analysis

| Pair | Issue | Recommendation |
|------|-------|---------------|
| `master-trade-bot` vs `master-trading-system` | MTS is a git repo (newer, 2026-02-14), MTB is not. Both active trading systems. | Clarify which is canonical. Likely MTS supersedes MTB. |
| `polymarket-bots` vs `polymarketbtc15massistant` | PB is a branch clone of PB15M repo. Different branch (copy-bot). | PB is a feature branch checkout. Merge or archive. |
| `lancewfisher-splash` vs `lancewfisher-v2` | V2 is the active splash page. Splash is the old version. | Archive lancewfisher-splash. |
| `galleon-splash` vs `galleon-storm` | Storm is a single HTML variant of splash. | Merge storm into splash as a concept file. |
| `project-hub` vs `project-dashboard` (GitHub) | project-dashboard may be an earlier iOS version. | Confirm, then deprecate project-dashboard on GitHub. |
| `frontier-bastion` local vs `frontier-bastion` GitHub repo | Local remote points to exo, but a dedicated frontier-bastion repo exists on GitHub. | Repoint local remote to the dedicated repo. |
| `harmony-medspa` local vs `harmony-medspa` GitHub repo | Local remote points to exo, but a dedicated harmony-medspa repo exists on GitHub. | Repoint local remote to the dedicated repo. |
| `data/trading.db` vs `master-trading-system/data/trading.db` | Root data/ has a standalone trading.db. MTS also has one. | Check if root data/ is stale. Archive if so. |

### Loose Root Files

| File | Size | Date | Action |
|------|------|------|--------|
| `CLAUDE.md` | 3.3KB | 2026-02-12 | **Keep** - workspace root context |
| `PROJECTS.json` | 21.9KB | 2026-02-18 | **Keep** - project registry |
| `MEDIA_ORGANIZER_STOPPOINT.md` | 2.8KB | 2026-02-07 | **Keep** - reference doc |
| `SECURITY_HARDENING.md` | 4.0KB | 2026-02-07 | **Keep** - reference doc |
| `sync-phone-projects.py` | 17.1KB | 2026-02-12 | **Keep** - phone sync script |
| `sync-phone-projects.bat` | 109B | 2026-02-12 | **Keep** - wrapper |
| `setup_scls.bat` | 4.3KB | 2026-02-08 | **Archive** - one-time setup |
| `project-health-report.txt` | 1.2KB | 2026-02-08 | **Archive** - stale report |
| `auton.pid` | 3B | 2026-02-13 | **Archive** - stale PID file |
| `nul` | 0B | 2026-02-18 | **Delete** - Windows artifact |
| `%TEMP%mts_state.json` | 3.9KB | 2026-02-14 | **Archive** - misnamed temp file |
| `_gen.js`, `_gen.py`, `_gen.ps1`, etc. | Various | 2026-02-08 | **Archive** - scratch/experiment files |
| `_audit_template.txt`, `_mkaudit.py`, etc. | Various | 2026-02-08 | **Archive** - audit tooling scratch |
| `_robocopy_pictures.bat` | 139B | 2026-02-06 | **Archive** - one-time migration script |
| `_bootstrap.py`, `_build.py` | Various | 2026-02-08 | **Archive** - scratch scripts |
| `_inventory_scan.ps1`, `_detailed_scan.ps1` | Various | 2026-02-18 | **Delete** - generated by this session |

---

## GitHub Repos Mapped to Local

| GitHub Repo | Local Path | Remote Configured | Status |
|-------------|-----------|-------------------|--------|
| lance-fisher/exo | `exo/` | Y | Staging repo for phone projects |
| lance-fisher/polymarketbtc15massistant | `polymarketbtc15massistant/` | Y (also in polymarket-bots) | Active |
| lance-fisher/e2ee-messenger | `e2ee-messenger/` | Y | Active |
| lance-fisher/trading-profit-engine | `trading-profit-engine/` | Y | Active |
| lance-fisher/frontier-bastion | `frontier-bastion/` | **Mispointed** (to exo) | Needs repoint |
| lance-fisher/harmony-medspa | `harmony-medspa/` | **Mispointed** (to exo) | Needs repoint |
| lance-fisher/scls | None | N/A | No local clone |
| lance-fisher/project-dashboard | None or `project-hub/`? | N/A | Investigate |
| lance-fisher/mission-control | None | N/A | Investigate |
| lance-fisher/trading-bot | None | N/A | Investigate |

---

## Recommendations Summary

### Immediate (Safe, Non-Destructive)

1. **Repoint remotes** for frontier-bastion and harmony-medspa to their dedicated GitHub repos
2. **Create _ops infrastructure** in project-hub for consolidation tracking
3. **Archive loose root files** to `_Archive/2026-02-18_1900/`
4. **Clean up temp scanner scripts** (`_inventory_scan.ps1`, `_detailed_scan.ps1`)

### Requires Approval

5. **Create GitHub repos** for: lancewfisher-v2, auton, home-hub, JumpQuest, project-hub, one-three-net
6. **Archive projects**: lancewfisher-splash (superseded), exo (staging repo), data/ (stale DB)
7. **Resolve duplicates**: master-trade-bot vs master-trading-system, polymarket-bots vs polymarketbtc15massistant
8. **Investigate remote-only repos**: scls, project-dashboard, mission-control, trading-bot

### Future Phases

9. **Convert non-repo projects** to git repos
10. **Normalize all repos**: .gitignore, README, docs/ structure
11. **Build sync automation**
12. **Update ProjectHub** to index everything
