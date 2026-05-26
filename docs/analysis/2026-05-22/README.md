# 2026-05-22 deployment — post-mission analysis appendix

Analysis appendix for the 2026-05-22 BizzyBoat deployment
([#160](https://github.com/rolker/unh_echoboats_project11/issues/160)), collected under the
data-analysis umbrella ([#169](https://github.com/rolker/unh_echoboats_project11/issues/169)).

- [`findings.md`](findings.md) — full per-section findings (§1–§14): tier-1 `bag_analysis`
  report, mission timeline, topic completeness + bag integrity, tide/chart-datum chain,
  diagnostics (incl. annunciator gaps), survey-pattern execution + efficiency, and the
  five sub-issue dives.

## Sub-issue outcomes
| Sub-issue | Outcome |
|---|---|
| [#168](https://github.com/rolker/unh_echoboats_project11/issues/168) survey efficiency | closed |
| [#164](https://github.com/rolker/unh_echoboats_project11/issues/164) SE-undulation | closed (awaiting recurrence-with-data) |
| [#167](https://github.com/rolker/unh_echoboats_project11/issues/167) power | closed — durable doc `bizzyboat_project11/docs/bizzyboat_power.md` (PR #176) |
| [#165](https://github.com/rolker/unh_echoboats_project11/issues/165) hover drift | closed — fix tracked in `rolker/unh_marine_navigation#33` |
| [#166](https://github.com/rolker/unh_echoboats_project11/issues/166) CAMP freeze | **open** — root cause unconfirmed; capture plan in `rolker/camp#52` |

## Provenance (not committed)
- Extraction DB: `~/data/logs/analysis/2026-05-22_deployment.db`
- Tier-1 report (`summary.md` + 7 PNG plots): `~/data/logs/analysis/2026-05-22/report/`
- Analysis scripts: `~/data/logs/analysis/2026-05-22_*.py`, `2026-05_*.py`
