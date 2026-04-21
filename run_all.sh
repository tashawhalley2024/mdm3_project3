#!/usr/bin/env bash
# Full pipeline: data build -> scoring -> analysis -> plots -> verify.
# Stops on the first failure (set -e).
set -e

python data_reading.py
python scoring.py
python analysis/run_analysis.py

# Slide-build default: two-tier significance palette (p<0.05 vs not).
# For the writeup build, set PLOTS_PRES_MODE=0 to use the four-tier palette.
PLOTS_PRES_MODE=1 python analysis/run_plots.py
# PLOTS_PRES_MODE=0 python analysis/run_plots.py   # writeup build (four-tier)

python verify.py
