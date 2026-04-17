# analysis/

Python scripts for the secularism-women panel analysis. All scripts resolve paths relative to the **repo root** — always run them from there.

---

## Scripts

| Script | What it does | Inputs | Outputs |
|---|---|---|---|
| `run_analysis.py` | Runs all regressions (T1 cross-section, T2 panel FE, T4 Mundlak, Phases 3–10) | `data/outcome_wbl.csv`, `data/predictors.csv`, `data/robustness_outcomes.csv` | `results/results.csv` + robustness CSVs |
| `run_plots.py` | Generates the presentation figure set (currently 00, 01, 02, 05, 06, 07, 09, 10, 11, 12 — see `figures/README.md` for why 03/04/08 are removed) | `results/results.csv`, `data/predictors.csv`, `data/outcome_composite.csv` | `figures/00_map.png` … `figures/12_mundlak_decomposition.png` |
| `compare_indices.py` | *(Deprecated legacy — kept for audit trail only. Reads `results/results_wbl.csv`, which is no longer produced by the main pipeline; running the script as-is will error.)* Compares composite vs WBL index coefficients | `results/results_composite.csv`, `results/results_wbl.csv` *(removed 2026-04-17)* | `results/index_comparison.csv`, `results/index_comparison.md` |
| `sanity_check.py` | Validates WBL index against composite baseline | `sanity_check/baseline.csv`, `sanity_check/actual.csv` *(not in repo — intermediate files)* | `sanity_check/overlap_comparison.csv`, `sanity_check/comparison_scatter.png` |

| `utils.py` | Shared utilities (`robust_minmax` normalisation) | — | — |
| `config.py` | Shared constants (`REGION_MAP`, `FOCAL_PRED`, path anchors) | — | — |

---

## Run Order

```bash
# From repo root:
python analysis/run_analysis.py   # ~5-10 min
python analysis/run_plots.py
python analysis/compare_indices.py
```

`analysis/sanity_check.py` is standalone and requires `sanity_check/baseline.csv` and `sanity_check/actual.csv` (intermediate files, not committed to the repo).

---

## Notes

- **Raw data absence is handled gracefully.** Phases that require `data/raw/qog/` (P6 male placebo) or `data/raw/legal_origins/` (P5 legal origins) check for file existence before running and skip cleanly if the raw files are absent.
- **`config.py` must stay in `analysis/`** alongside the scripts. Both `run_analysis.py` and `run_plots.py` insert their own directory into `sys.path` at runtime to import it.
- The active outcome variable is `wbl_treatment_index` (2013–2022). To switch to the 13-component composite, change `WOMEN_PATH` and `OUTCOME` near the top of `run_analysis.py`.
