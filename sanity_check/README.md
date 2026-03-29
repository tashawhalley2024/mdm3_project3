# sanity_check/

Validation of the WBL-based outcome index against the 13-component composite index.

---

## Purpose

Confirms that the two outcome indices (WBL and composite) measure similar underlying constructs before using them in separate analyses. A high correlation validates that results from the composite index (2007–2022) are interpretable alongside WBL index results (2013–2022).

**Result: r = 0.880** on the overlapping sample — strong agreement.

---

## Files

| File | Contents |
|---|---|
| `sanity_check_report.md` | Full narrative report: methodology, coverage statistics, correlation, interpretation |
| `overlap_comparison.csv` | Matched country-year pairs with both index values and signed/absolute differences |
| `comparison_scatter.png` | Scatter plot of WBL index vs composite index (normalised); shows tight linear relationship |
| `actual_histogram.png` | Histogram of WBL index values across the matched sample |

---

## Re-running

The sanity check script (`analysis/run_sanity_check.py`) requires two intermediate input files that are **not committed to this repo**:
- `sanity_check/baseline.csv` — composite index values (iso3, year, baseline_value)
- `sanity_check/actual.csv` — WBL index values (iso3, year, actual_value)

These were generated from the full pipeline (V-Dem/WDI ETL) which requires the large raw datasets. The outputs above represent the final validated state.

To re-run from scratch, rebuild the inputs from the ETL pipeline (see [`docs/DATA_SOURCES.md`](../docs/DATA_SOURCES.md)), then:
```bash
python analysis/sanity_check.py
```
