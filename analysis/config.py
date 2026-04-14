from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Pew
PEW_DIR = RAW_DIR / "pew" / "Global-Restrictions-on-Religion-2007-2022-Dataset"
PEW_CSV = PEW_DIR / "PublicDataset_ReligiousRestrictions_2007to2022.csv"

# V-Dem (Core v15)
VDEM_DIR = RAW_DIR / "vdem"
VDEM_CSV = VDEM_DIR / "V-Dem-CY-Core-v15.csv"

# QoG Standard TS (Jan 2025)
QOG_DIR = RAW_DIR / "qog"
QOG_CSV = QOG_DIR / "qog_std_ts_jan25.csv"

# EPR (Phase 3)
EPR_DIR = RAW_DIR / "epr"
EPR_CSV = EPR_DIR / "EPR-2021.csv"

# ── Analysis constants ─────────────────────────────────────────────────────────
YEAR_MIN = 2007
YEAR_MAX = 2022

FOCAL_PRED   = "gri_religious_courts_norm"
FOCAL_PRED_2 = "gri_apostasy_norm"

# Presentation palette — semantic colours used consistently across all figures
PALETTE = {
    "courts":        "#7F8C8D",   # slate grey — the null predictor
    "apostasy":      "#C0392B",   # deep red — the signal predictor
    "sig_high":      "#C0392B",   # p < 0.01
    "sig_med":       "#E67E22",   # p < 0.05
    "sig_low":       "#F1C40F",   # p < 0.10
    "null":          "#95A5A6",   # not significant
    "highlight_bg":  "#FDF2E9",   # pale highlight for hero rows
    "map_lo":        "#FFF5E1",   # choropleth low
    "map_hi":        "#8B1A1A",   # choropleth high
    "female":        "#C0392B",
    "male":          "#BDC3C7",
    "pre_band":      "#EDF2F7",
    "robust_band":   "#D4EDDA",
}

# ISO3 -> simplified UN region mapping (superset, ~187 countries)
REGION_MAP = {
    # Europe
    "ALB": "Europe", "AND": "Europe", "AUT": "Europe", "BEL": "Europe",
    "BIH": "Europe", "BGR": "Europe", "BLR": "Europe", "CHE": "Europe",
    "CYP": "Europe", "CZE": "Europe", "DEU": "Europe", "DNK": "Europe",
    "ESP": "Europe", "EST": "Europe", "FIN": "Europe", "FRA": "Europe",
    "GBR": "Europe", "GEO": "Europe", "GRC": "Europe", "HRV": "Europe",
    "HUN": "Europe", "IRL": "Europe", "ISL": "Europe", "ITA": "Europe",
    "KOS": "Europe", "LTU": "Europe", "LUX": "Europe", "LVA": "Europe",
    "MDA": "Europe", "MKD": "Europe", "MLT": "Europe", "MNE": "Europe",
    "NLD": "Europe", "NOR": "Europe", "POL": "Europe", "PRT": "Europe",
    "ROU": "Europe", "RUS": "Europe", "SRB": "Europe", "SVK": "Europe",
    "SVN": "Europe", "SWE": "Europe", "UKR": "Europe", "XKX": "Europe",
    # Americas (North, Central, Caribbean, South)
    "ATG": "Americas", "BHS": "Americas", "BLZ": "Americas", "BRB": "Americas",
    "CAN": "Americas", "CRI": "Americas", "CUB": "Americas", "DMA": "Americas",
    "DOM": "Americas", "GRD": "Americas", "GTM": "Americas", "GUY": "Americas",
    "HND": "Americas", "HTI": "Americas", "JAM": "Americas", "KNA": "Americas",
    "LCA": "Americas", "MEX": "Americas", "NIC": "Americas", "PAN": "Americas",
    "SLV": "Americas", "SUR": "Americas", "TTO": "Americas", "USA": "Americas",
    "VCT": "Americas", "ARG": "Americas", "BOL": "Americas", "BRA": "Americas",
    "CHL": "Americas", "COL": "Americas", "ECU": "Americas", "PER": "Americas",
    "PRY": "Americas", "URY": "Americas", "VEN": "Americas",
    # MENA
    "ARE": "MENA", "BHR": "MENA", "DZA": "MENA", "EGY": "MENA",
    "IRN": "MENA", "IRQ": "MENA", "ISR": "MENA", "JOR": "MENA",
    "KWT": "MENA", "LBN": "MENA", "LBY": "MENA", "MAR": "MENA",
    "OMN": "MENA", "PSE": "MENA", "QAT": "MENA", "SAU": "MENA",
    "SYR": "MENA", "TUN": "MENA", "TUR": "MENA", "YEM": "MENA",
    # Sub-Saharan Africa
    "AGO": "Sub-Saharan Africa", "BDI": "Sub-Saharan Africa",
    "BEN": "Sub-Saharan Africa", "BFA": "Sub-Saharan Africa",
    "BWA": "Sub-Saharan Africa", "CAF": "Sub-Saharan Africa",
    "CIV": "Sub-Saharan Africa", "CMR": "Sub-Saharan Africa",
    "COD": "Sub-Saharan Africa", "COG": "Sub-Saharan Africa",
    "COM": "Sub-Saharan Africa", "CPV": "Sub-Saharan Africa",
    "DJI": "Sub-Saharan Africa", "ERI": "Sub-Saharan Africa",
    "ETH": "Sub-Saharan Africa", "GAB": "Sub-Saharan Africa",
    "GHA": "Sub-Saharan Africa", "GIN": "Sub-Saharan Africa",
    "GMB": "Sub-Saharan Africa", "GNB": "Sub-Saharan Africa",
    "GNQ": "Sub-Saharan Africa", "KEN": "Sub-Saharan Africa",
    "LBR": "Sub-Saharan Africa", "LSO": "Sub-Saharan Africa",
    "MDG": "Sub-Saharan Africa", "MLI": "Sub-Saharan Africa",
    "MOZ": "Sub-Saharan Africa", "MRT": "Sub-Saharan Africa",
    "MUS": "Sub-Saharan Africa", "MWI": "Sub-Saharan Africa",
    "NAM": "Sub-Saharan Africa", "NER": "Sub-Saharan Africa",
    "NGA": "Sub-Saharan Africa", "RWA": "Sub-Saharan Africa",
    "SDN": "Sub-Saharan Africa", "SEN": "Sub-Saharan Africa",
    "SLE": "Sub-Saharan Africa", "SOM": "Sub-Saharan Africa",
    "SSD": "Sub-Saharan Africa", "STP": "Sub-Saharan Africa",
    "SWZ": "Sub-Saharan Africa", "SYC": "Sub-Saharan Africa",
    "TCD": "Sub-Saharan Africa", "TGO": "Sub-Saharan Africa",
    "TZA": "Sub-Saharan Africa", "UGA": "Sub-Saharan Africa",
    "ZAF": "Sub-Saharan Africa", "ZMB": "Sub-Saharan Africa",
    "ZWE": "Sub-Saharan Africa",
    # Asia-Pacific (South, Southeast, East Asia & Pacific)
    "AFG": "Asia-Pacific", "AUS": "Asia-Pacific", "BGD": "Asia-Pacific",
    "BTN": "Asia-Pacific", "CHN": "Asia-Pacific", "FJI": "Asia-Pacific",
    "FSM": "Asia-Pacific", "IDN": "Asia-Pacific", "IND": "Asia-Pacific",
    "JPN": "Asia-Pacific", "KHM": "Asia-Pacific", "KIR": "Asia-Pacific",
    "KOR": "Asia-Pacific", "LAO": "Asia-Pacific", "LKA": "Asia-Pacific",
    "MDV": "Asia-Pacific", "MHL": "Asia-Pacific", "MMR": "Asia-Pacific",
    "MNG": "Asia-Pacific", "MYS": "Asia-Pacific", "NPL": "Asia-Pacific",
    "NRU": "Asia-Pacific", "NZL": "Asia-Pacific", "PAK": "Asia-Pacific",
    "PHL": "Asia-Pacific", "PLW": "Asia-Pacific", "PNG": "Asia-Pacific",
    "PRK": "Asia-Pacific", "SAM": "Asia-Pacific", "SGP": "Asia-Pacific",
    "SLB": "Asia-Pacific", "THA": "Asia-Pacific", "TLS": "Asia-Pacific",
    "TON": "Asia-Pacific", "TUV": "Asia-Pacific", "VNM": "Asia-Pacific",
    "VUT": "Asia-Pacific", "WSM": "Asia-Pacific",
    # Central Asia & Caucasus
    "ARM": "Central Asia", "AZE": "Central Asia", "KAZ": "Central Asia",
    "KGZ": "Central Asia", "TJK": "Central Asia", "TKM": "Central Asia",
    "UZB": "Central Asia",
}
