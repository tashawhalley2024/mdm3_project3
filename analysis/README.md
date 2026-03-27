# analysis/

Python scripts for the secularism-women panel analysis. All scripts resolve paths relative to the **repo root** — always run them from there.

---

## Scripts

| Script | What it does | Inputs | Outputs |
|---|---|---|---|
| `analyse_secularism_women.py` | Runs all regressions (T1 cross-section, T2 panel FE, Phases 3–10) | `data/wbl_treatment_index.csv`, `data/secularism_composition_normalised.csv`, `data/gender_gap_panel.csv` | `results/secularism_women_results.csv` + robustness CSVs |
| `plot_secularism_women.py` | Generates 10 publication figures | `results/secularism_women_results.csv`, `data/secularism_composition_normalised.csv`, `data/women_secularism_normalised.csv` | `figures/*.png` |
| `compare_indices.py` | Compares composite vs WBL index coefficients | `results/secularism_women_results_composite.csv`, `results/secularism_women_results_wbl.csv` | `results/index_comparison.csv`, `results/index_comparison.md` |
| `run_sanity_check.py` | Validates WBL index against composite baseline | `sanity_check/baseline.csv`, `sanity_check/actual.csv` *(not in repo — intermediate files)* | `sanity_check/overlap_comparison.csv`, `sanity_check/comparison_scatter.png` |
| `utils.py` | Shared utilities (`robust_minmax` normalisation) | — | — |
| `config.py` | Shared constants (`REGION_MAP`, `FOCAL_PRED`, path anchors) | — | — |

---

## Run Order

```bash
# From repo root:
python analysis/analyse_secularism_women.py   # ~5-10 min
python analysis/plot_secularism_women.py
python analysis/compare_indices.py
```

`run_sanity_check.py` is standalone and requires `sanity_check/baseline.csv` and `sanity_check/actual.csv` (intermediate files, not committed to the repo).

---

## Notes

- **Raw data absence is handled gracefully.** Phases that require `data/raw/qog/` (P6 male placebo) or `data/raw/legal_origins/` (P5 legal origins) check for file existence before running and skip cleanly if the raw files are absent.
- **`config.py` must stay in `analysis/`** alongside the scripts. Both `analyse_` and `plot_` insert their own directory into `sys.path` at runtime to import it.
- The active outcome variable is `wbl_treatment_index` (2013–2022). To switch to the 13-component composite, change `WOMEN_PATH` and `OUTCOME` near the top of `analyse_secularism_women.py`.
