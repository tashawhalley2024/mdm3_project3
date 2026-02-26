#the data is good but every indicator is separated into different files, to make it all 
#clear and readable i have made this python file to read all the csvs, load them in and
#deal with any issues so the other file can just be working on calculating correlation
#there are so many indicators that I think we should read through and decide which are best
#this is just putting some in so we can work out a method

import pandas as pd
import numpy as np

#LOAD IN THE FILES

#De jure measures are laws/rights
#de facto outcomes are liek violence prevalence/ representation
#keep as SEPERATE subscores as laws and experience diverge

''' This is the BINARY DATA, so answers only yes/no'''
#so far only collecting data for if women can lead a household, get a job, if women and men are paid the same and if there is dv legislation

def binary_dict(df, country_col="Economy"):
    # func turns the bianry data files into dictionary with country:1/0/None
    binary_col = df.columns[-1]
    
    return (
        df
        .set_index(country_col)[binary_col]
        .apply(lambda x: None if pd.isna(x) else int(x))
        .to_dict()
    )

household_dict =binary_dict(pd.read_csv('household/householddata.csv')) #can women lead the household, year 2023
job_dict =binary_dict(pd.read_csv('job/jobdata.csv')) #can women get a job same way as man, year 2023
pay_dict =binary_dict(pd.read_csv('renumeration/renumerationdata.csv')) #do women and men get paid the same, year 2023
dv_dict =binary_dict(pd.read_csv('domesticviolence/domesticviolence.csv')) #is there legislation on domestic violence, year 2023


''' This is the CONTINOUS DATA, so answers only yes/no'''
#so far jsut % seats in parliament and experiences of physical/sexual assault, we need to have a lot more but a lot of the data sets miss so many countries


def cont_dict(df, country_col="Economy"):
	#func turns the continuous data files into dictionary with country: %
    value_col = df.columns[-1]  
    
    return (
        df
        .set_index(country_col)[value_col]
        .apply(lambda x: None if pd.isna(x) else float(x))
        .to_dict()
    )

parliament_dict =cont_dict(pd.read_csv('parliamentaryseats/seats.csv')) #percent of seats in parliament held by women, year 2024, can be a mix of years to include more countries, we must decide
physsexa_dict =cont_dict(pd.read_csv('sexualassault/sa.csv')) #percent of women experienced physical/sexual violence in last 12 months, year 2018



#im thinking create some kind of score? higher the score better treatment of women 
# score has three sections, rights, representation, safety
#computes overall score as average of sections
#report covereage next to score and do some sensitivity checks

# so far i standardise the continupus variables by /100 i think maybe we should divide by std (z-scores)

'''take dictionaries, normalise/inverts the numbers, return dataframe with pillar scores, overall score and coverage'''

# 1 = better, 0 = worse, None = missing
binary_indicators = {
    "household_rights": household_dict,
    "job_rights": job_dict,
    "equal_pay_rights": pay_dict,
    "dv_legislation": dv_dict,
}

# continuous (%). convert to 0–1 and invert the violence one- maybe change this?.
continuous_indicators = {
    "women_parliament_pct": parliament_dict,   # higher is better
    "violence_12m_pct": physsexa_dict,         # higher is worse (we will invert)
}

df = pd.DataFrame({**binary_indicators, **continuous_indicators})

def make_womens_treatment_scores(
    df,
    parliament_col="women_parliament_pct",
    violence_col="violence_12m_pct",
    binary_cols=("household_rights", "job_rights", "equal_pay_rights", "dv_legislation"), # add more columns when we get more date
    weights = None, # change to dictionary of pillar weights when we want that
    coverage_penalty = True,
    min_coverage_frac = None #this will drop the low covereage countries we should decide if we wanr
):
	out = df.copy()

    # normalises the continuous to 0-1, do this on more if we get more continuous data
    
    #if %seats is over 50 set score as 1, otherwise since equal is 50/50 multiply by 2
	pct = out[parliament_col] / 100.0

	out["parliament_score"] = np.where(
		pct >= 0.5,
		1.0,
		2 * pct
	)

	#also normalised but inverted since lower violence score is better
	out["safety_outcome_score"] = 1 - (out[violence_col] /100 )

	#SEPARATE INTO SECTIONS

	# rights score is an average of binary rights (ignores missing)
	out["rights_score"] = out[list(binary_cols)].mean(axis=1, skipna=True)
	# representation score is parliament_score
	out["representation_score"] = out["parliament_score"]
	# safety score is an average of dv legislation and safety outcome score
	out["safety_score"] = out[["dv_legislation", "safety_outcome_score"]].mean(axis=1, skipna=True)


	if weights is None:
		weights = {
			"rights_score": 1/3,
			"representation_score": 1/3,
			"safety_score": 1/3,
		}

	# Weighted overall with renormalization
	pillar_cols = list(weights.keys())

	def weighted_row(row):
		available = {k: weights[k] for k in pillar_cols if pd.notna(row[k])}
		if not available:
			return None
		weight_sum = sum(available.values())
		return sum(row[k] * w for k, w in available.items()) / weight_sum

	out["overall_score"] = out.apply(weighted_row, axis=1)


	# Coverage
	underlying_cols = list(binary_cols) + [parliament_col, violence_col]
	out["coverage_count"] = out[underlying_cols].notna().sum(axis=1)
	out["coverage_frac"] = out["coverage_count"] / len(underlying_cols) 

	if coverage_penalty: # basically i multiple the overall score by coverage frac to make sure countries with NaN values arent inflated
		out["adjusted_score"] = out["overall_score"] * out["coverage_frac"]
	else:
		out["adjusted_score"] = out["overall_score"]

	if min_coverage_frac is not None: # turned off right now, but we can change frac number to stop including countries with minimal coverage
		out = out[out["coverage_frac"] >= float(min_coverage_frac)].copy()



	return out[
			["rights_score", "representation_score", "safety_score",
			"overall_score", "adjusted_score", "coverage_count", "coverage_frac"]
    ]


scores = make_womens_treatment_scores(df) #,min_coverage_frac = 0.8
ranked = scores.sort_values("adjusted_score", ascending=False)
print(ranked.head(20))