#!/usr/bin/env python
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import date


# source: https://data.bls.gov/pdq/SurveyOutputServlet
# monthly unemployment rate
raw_unemployment_data = pd.read_csv(Path("raw_data/USUnemployment.csv"), index_col="Year")

first_year = raw_unemployment_data.index[0]
last_year = raw_unemployment_data.index[-1]

mean_unemployment = pd.Series(
    (raw_unemployment_data.mean(axis="columns") / 100).array,
    name = "mean_unemployment",
    index = pd.date_range(start=date(year=first_year,month=12,day=31), end=date(year=last_year,month=12,day=31), freq="YE")
)

# source: https://fred.stlouisfed.org/series/CPIAUCNS 
# monthly CPI
raw_inflation_data = pd.read_csv(
    Path("raw_data/CPIAUCNS.csv"), 
    parse_dates=["observation_date"], 
    date_format="%Y-%m-%d",
    index_col="observation_date"
).squeeze()


inflation_rate = (
    raw_inflation_data
    .resample("YE")
    .apply(lambda x: x.iat[-1] / x.iat[0] - 1)
)

inflation_rate.name = "inflation_rate"

#The reason why the Phillips-curve was stable up until 1970 are the stable inflation expectations. 
#Considering that people are neither dump nor blind it is safe to assume that the inflation expectations from 1900 to 1970 were the mean of the inflation in the said time period
# https://fred.stlouisfed.org/series/MICH
# Median expected price change next 12 months, Surveys of Consumers.
raw_inflation_expectations = pd.read_csv(
    Path("raw_data/michigan_inflation_expectations.csv"),
    parse_dates=["observation_date"],
    date_format="%Y-%m-%d",
    index_col="observation_date"
).squeeze()

expected_inflation = pd.Series(
    (raw_inflation_expectations / 100), 
    name="expected_inflation",
    index=pd.date_range(start="1913-01-01", end="2024-12-31", freq="YS")
)

# expected inflation for the current year as a mean of the expectations in the first 3 months of the year
expected_inflation = expected_inflation.resample("YS").apply(lambda x: x.loc[x.index.month<4].mean())

# assumption: the inflation expectation for the next year is the mean inflation in the previous year
day = pd.tseries.offsets.DateOffset(1)
expected_inflation_before_1978 = pd.Series(inflation_rate.array, inflation_rate.index + day).loc[:"1977-01-01"]
expected_inflation = expected_inflation.fillna(value=expected_inflation_before_1978).dropna()
expected_inflation.head()


dataset = pd.concat(
    [inflation_rate, mean_unemployment, expected_inflation.resample("YE").ffill()], 
    axis="columns", 
    join="inner"
).round(5)
dataset.index.name = "year"

dataset.to_csv("dataset.csv")
