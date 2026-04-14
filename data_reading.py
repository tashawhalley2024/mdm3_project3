import pandas as pd
import numpy as np
import os
import glob

# ============================================
# HELPER FUNCTIONS
# ============================================

def load_indicator(folder_path):
    dfs = []

    for year in range(2013, 2024):
        year_path = os.path.join(folder_path, str(year))
        files = glob.glob(os.path.join(year_path, "**", "*.*"), recursive=True)

        for file_path in files:
            file_name = os.path.basename(file_path).lower()

            # Skip metadata files and temporary Excel files
            if "metadata" in file_name or file_name.startswith("~$"):
                continue

            try:
                if file_path.endswith(".csv"):
                    temp_df = pd.read_csv(file_path)
                elif file_path.endswith((".xlsx", ".xls")):
                    temp_df = pd.read_excel(file_path)
                else:
                    continue

                temp_df["Year"] = year
                temp_df["Source_File"] = os.path.basename(file_path)
                dfs.append(temp_df)

            except Exception as e:
                print(f"Could not read {file_path}: {e}")

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def load_lifeexp(subfolder_name):
    dfs = []

    for year in range(2013, 2024):
        folder = os.path.join("data", "lifeexp", str(year), subfolder_name)
        files = glob.glob(os.path.join(folder, "**", "*.*"), recursive=True)

        for file_path in files:
            file_name = os.path.basename(file_path).lower()

            # skip metadata files and temporary Excel files
            if "metadata" in file_name or file_name.startswith("~$"):
                continue

            try:
                if file_path.endswith(".csv"):
                    temp_df = pd.read_csv(file_path)
                elif file_path.endswith((".xlsx", ".xls")):
                    temp_df = pd.read_excel(file_path)
                else:
                    continue

                temp_df["Year"] = year
                temp_df["Source_File"] = os.path.basename(file_path)
                dfs.append(temp_df)

            except Exception as e:
                print(f"Could not read {file_path}: {e}")

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def sort_panel(df):
    return df.sort_values(["ISO Code", "Year"])


# ============================================
# LOAD IN THE FILES
# ============================================

if __name__ == "__main__":
    # De jure measures are laws/rights
    # De facto outcomes are lived outcomes like representation / health / violence prevalence
    # Keep thematic groups separate so the panel preserves different dimensions of treatment of women

    # load the huge collections set

    file_path = "data/WBL2024-1-0-Historical-Panel-Data.xlsx"
    wbl_raw = pd.read_excel(file_path, sheet_name="WBL Panel 2024")

    # Keep only 2013–2023
    wbl_raw = wbl_raw[(wbl_raw["Report Year"] >= 2013) & (wbl_raw["Report Year"] <= 2023)].copy()

    # Standardise year column name
    wbl_raw = wbl_raw.rename(columns={"Report Year": "Year"})

    # Common identifier columns
    id_cols = ["Economy", "ISO Code", "Region", "Income Group", "Year"]


    # 1. Mobility
    mobility = wbl_raw[id_cols + [
        "Can a woman choose where to live in the same way as a man?",
        "Can a woman travel outside her home in the same way as a man?",
        "Can a woman apply for a passport in the same way as a man?",
        "Can a woman travel outside the country in the same way as a man?"
    ]].copy()

    # 2. Workplace rights
    workplace = wbl_raw[id_cols + [
        "Can a woman get a job in the same way as a man?",
        "Does the law prohibit discrimination in employment based on gender?",
        "Is there legislation on sexual harassment in employment?",
        "Are there criminal penalties or civil remedies for sexual harassment in employment?"
    ]].copy()

    # 3. Pay equality
    pay = wbl_raw[id_cols + [
        "Does the law mandate equal remuneration for work of equal value?",
        "Can a woman work at night in the same way as a man?",
        "Can a woman work in a job deemed dangerous in the same way as a man?",
        "Can a woman work in an industrial job in the same way as a man?"
    ]].copy()

    # 4. Family, legal status, and safety
    marriage = wbl_raw[id_cols + [
        "Is the law free of legal provisions that require a married woman to obey her husband?",
        "Can a woman be head of household in the same way as a man?",
        "Is there legislation specifically addressing domestic violence?",
        "Can a woman obtain a judgment of divorce in the same way as a man?",
        "Does a woman have the same rights to remarry as a man?"
    ]].copy()

    # 5. Parenthood and care
    # Binary indicators only — used for scoring (continuous leave-length vars in parenthood_detail)
    parenthood = wbl_raw[id_cols + [
        "Is paid leave of at least 14 weeks available to mothers?",
        "Does the government administer 100 percent of maternity leave benefits?",
        "Is there paid leave available to fathers?",
        "Is there paid parental leave?",
        "Is dismissal of pregnant workers prohibited?"
    ]].copy()

    # Continuous leave-length variables — saved separately, not scored
    parenthood_detail = wbl_raw[id_cols + [
        "Length of paid maternity leave",
        "Length of paid paternity leave",
        "Shared days",
        "Days for the mother",
        "Days for the father"
    ]].copy()

    # 6. Economic and financial rights
    entrepreneurship = wbl_raw[id_cols + [
        "Does the law prohibit discrimination in access to credit based on gender?",
        "Can a woman sign a contract in the same way as a man?",
        "Can a woman register a business in the same way as a man?",
        "Can a woman open a bank account in the same way as a man?"
    ]].copy()

    # 7. Assets and property rights
    assets = wbl_raw[id_cols + [
        "Do women and men have equal ownership rights to immovable property?",
        "Do sons and daughters have equal rights to inherit assets from their parents?",
        "Do male and female surviving spouses have equal rights to inherit assets?",
        "Does the law grant spouses equal administrative authority over assets during marriage?",
        "Does the law provide for the valuation of nonmonetary contributions?"
    ]].copy()

    # 8. Pension and long-term security
    pension = wbl_raw[id_cols + [
        "Is the age at which women and men can retire with full pension benefits the same?",
        "Is the age at which women and men can retire with partial pension benefits the same?",
        "Is the mandatory retirement age for women and men the same?",
        "Are periods of absence due to childcare accounted for in pension benefits?"
    ]].copy()

    # load external indicator sets
    adolefert = load_indicator("data/adolefert")
    parliament = load_indicator("data/parliament")
    maternalmort = load_indicator("data/maternalmort")
    lifeexp_female = load_lifeexp("lifeexpfem")
    lifeexp_total = load_lifeexp("lifeexptotal")

    print("WBL datasets:")
    print("mobility:", mobility.shape)
    print("workplace:", workplace.shape)
    print("pay:", pay.shape)
    print("marriage:", marriage.shape)
    print("parenthood:", parenthood.shape)
    print("entrepreneurship:", entrepreneurship.shape)
    print("assets:", assets.shape)
    print("pension:", pension.shape)

    print("\nOther indicators:")
    print("adolefert:", adolefert.shape)
    print("parliament:", parliament.shape)
    print("maternalmort:", maternalmort.shape)
    print("lifeexp_female:", lifeexp_female.shape)
    print("lifeexp_total:", lifeexp_total.shape)

    print("\nColumn names:")
    print("adolefert columns:", adolefert.columns.tolist() if not adolefert.empty else "EMPTY")
    print("parliament columns:", parliament.columns.tolist() if not parliament.empty else "EMPTY")
    print("maternalmort columns:", maternalmort.columns.tolist() if not maternalmort.empty else "EMPTY")
    print("lifeexp_female columns:", lifeexp_female.columns.tolist() if not lifeexp_female.empty else "EMPTY")
    print("lifeexp_total columns:", lifeexp_total.columns.tolist() if not lifeexp_total.empty else "EMPTY")

    print("\nAll indicator files loaded successfully.")

    # standardise indicator names

    adolefert = adolefert.rename(columns={
        "Economy Code": "ISO Code",
        "Adolescent fertility rate (births per 1,000 women ages 15-19)": "adolescent_fertility"
    })

    parliament = parliament.rename(columns={
        "Economy Code": "ISO Code",
        "Proportion of seats held by women in national parliaments (%)": "women_parliament_pct"
    })

    maternalmort = maternalmort.rename(columns={
        "Economy Code": "ISO Code",
        "Maternal mortality ratio (modeled estimate, per 100,000 live births)": "maternal_mortality"
    })

    lifeexp_female = lifeexp_female.rename(columns={
        "Economy Code": "ISO Code",
        "Life expectancy at birth, female (years)": "lifeexp_female"
    })

    lifeexp_total = lifeexp_total.rename(columns={
        "Economy Code": "ISO Code",
        "Life expectancy at birth, total (years)": "lifeexp_total"
    })

    # keep only the needed columns
    adolefert = adolefert[["Economy", "ISO Code", "Year", "adolescent_fertility"]].copy()
    parliament = parliament[["Economy", "ISO Code", "Year", "women_parliament_pct"]].copy()
    maternalmort = maternalmort[["Economy", "ISO Code", "Year", "maternal_mortality"]].copy()
    lifeexp_female = lifeexp_female[["Economy", "ISO Code", "Year", "lifeexp_female"]].copy()
    lifeexp_total = lifeexp_total[["Economy", "ISO Code", "Year", "lifeexp_total"]].copy()

    # create categories

    # 1. Mobility
    mobility_group = mobility.copy()

    # 2. Workplace rights
    workplace_group = workplace.copy()

    # 3. Pay equality
    pay_group = pay.copy()

    # 4. Family, legal status, and safety
    family_safety_group = marriage.copy()

    # 5. Parenthood and care
    parenthood_group = parenthood.copy()

    # 6. Economic and financial rights
    economic_rights_group = entrepreneurship.copy()

    # 7. Assets and property rights
    assets_group = assets.copy()

    # 8. Pension and long-term security
    pension_group = pension.copy()

    # Country reference info
    country_info = wbl_raw[["ISO Code", "Region", "Income Group"]].drop_duplicates(subset=["ISO Code"])

    # 9. Health outcomes
    health_group = (
        adolefert
        .merge(maternalmort.drop(columns=["Economy"]), on=["ISO Code", "Year"], how="outer")
        .merge(lifeexp_female.drop(columns=["Economy"]), on=["ISO Code", "Year"], how="outer")
        .merge(lifeexp_total.drop(columns=["Economy"]), on=["ISO Code", "Year"], how="outer")
    )

    health_group = health_group.merge(country_info, on="ISO Code", how="left")

    health_group = health_group[[
        "Economy", "ISO Code", "Region", "Income Group", "Year",
        "adolescent_fertility",
        "maternal_mortality",
        "lifeexp_female",
        "lifeexp_total"
    ]].copy()

    # 10. Political representation
    political_representation_group = parliament.copy()
    political_representation_group = political_representation_group.merge(country_info, on="ISO Code", how="left")

    political_representation_group = political_representation_group[[
        "Economy", "ISO Code", "Region", "Income Group", "Year",
        "women_parliament_pct"
    ]].copy()

    print("\nPreview of grouped datasets:")
    print("\nmobility_group:")
    print(mobility_group.head())

    print("\nhealth_group:")
    print(health_group.head())

    print("\npolitical_representation_group:")
    print(political_representation_group.head())

    # sort all groups by country and year
    mobility_group = sort_panel(mobility_group)
    workplace_group = sort_panel(workplace_group)
    pay_group = sort_panel(pay_group)
    family_safety_group = sort_panel(family_safety_group)
    parenthood_group = sort_panel(parenthood_group)
    parenthood_detail = sort_panel(parenthood_detail)
    economic_rights_group = sort_panel(economic_rights_group)
    assets_group = sort_panel(assets_group)
    pension_group = sort_panel(pension_group)
    health_group = sort_panel(health_group)
    political_representation_group = sort_panel(political_representation_group)

    # ============================================
    # SAVE OUTPUT DATASETS
    # ============================================

    # Create output folder if it doesn't exist
    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)

    # Save WBL thematic groups
    mobility_group.to_csv(f"{output_folder}/mobility_group.csv", index=False)
    workplace_group.to_csv(f"{output_folder}/workplace_group.csv", index=False)
    pay_group.to_csv(f"{output_folder}/pay_group.csv", index=False)
    family_safety_group.to_csv(f"{output_folder}/family_safety_group.csv", index=False)
    parenthood_group.to_csv(f"{output_folder}/parenthood_group.csv", index=False)
    parenthood_detail.to_csv(f"{output_folder}/parenthood_detail.csv", index=False)
    economic_rights_group.to_csv(f"{output_folder}/economic_rights_group.csv", index=False)
    assets_group.to_csv(f"{output_folder}/assets_group.csv", index=False)
    pension_group.to_csv(f"{output_folder}/pension_group.csv", index=False)

    # Save external thematic groups
    health_group.to_csv(f"{output_folder}/health_group.csv", index=False)
    political_representation_group.to_csv(
        f"{output_folder}/political_representation_group.csv", index=False
    )

    print("\nAll datasets saved to 'output/' folder successfully.")
