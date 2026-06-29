import pandas as pd
import numpy as np
import wbdata
import datetime
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf


# Define the World Bank indicators to extract

indicators = {
    "SP.DYN.TFRT.IN": "fertility_rate",
    "NY.GDP.PCAP.KD.ZG": "gdp_per_capita_growth"
}


# 30 European countries using World Bank country codes

countries = [
    "DEU", "FRA", "ITA", "ESP", "POL", "SWE", "NLD", "BEL", "GRC", "PRT",
    "CZE", "HUN", "ROU", "AUT", "CHE", "NOR", "DNK", "FIN", "SVK", "BGR",
    "HRV", "SVN", "LTU", "LVA", "EST", "IRL", "GBR", "UKR", "SRB", "ALB"
]


# Pull data from the World Bank API

df = wbdata.get_dataframe(indicators, country=countries)

print(df.head(10))


# Check summary statistics to identify any data quality issues

print(df.describe())


# Check missing value counts per variable

print(df.isnull().sum())


# Drop all rows with missing values

df = df.dropna()


# Reset index to bring country and date out as columns

df_reset = df.reset_index()


# Convert date column to datetime format

df_reset["date"] = pd.to_datetime(df_reset["date"])


# Trim to the 1990 to 2020 study period

df_model = df_reset[
    (df_reset["date"].dt.year >= 1990) &
    (df_reset["date"].dt.year <= 2020)
].copy()


# Add a numeric year column for use in the fixed effects model

df_model["year"] = df_model["date"].dt.year

print(f"Date range: {df_model['year'].min()} to {df_model['year'].max()}")
print(f"Observations: {df_model.shape[0]}")
print(f"Countries: {df_model['country'].nunique()}")


# Chart 1: Fertility rate trends across all 30 countries
# Shows the broad decline in birth rates relative to the 2.1 replacement threshold

plt.figure(figsize=(14, 6))
for country in df_model["country"].unique():
    country_data = df_model[df_model["country"] == country]
    plt.plot(country_data["date"], country_data["fertility_rate"], alpha=0.5)

plt.axhline(y=2.1, color="red", linestyle="--", linewidth=1.5, label="Replacement Level (2.1)")
plt.title("Fertility Rate Across European Countries (1990-2020)")
plt.xlabel("Year")
plt.ylabel("Fertility Rate")
plt.legend()
plt.tight_layout()
plt.show()


# Chart 2: Average fertility rate by country
# Ranks all 30 countries to show which are most affected by demographic decline

avg_fertility = df_model.groupby("country")["fertility_rate"].mean().sort_values()

plt.figure(figsize=(12, 8))
plt.barh(avg_fertility.index, avg_fertility.values, color="steelblue")
plt.axvline(x=2.1, color="red", linestyle="--", linewidth=1.5, label="Replacement Level (2.1)")
plt.title("Average Fertility Rate by Country (1990-2020)")
plt.xlabel("Average Fertility Rate")
plt.ylabel("Country")
plt.legend()
plt.tight_layout()
plt.show()


# Chart 3: Fertility rate vs GDP per capita growth scatter
# Explores the raw relationship between the two variables before modelling

plt.figure(figsize=(10, 6))
plt.scatter(df_model["fertility_rate"], df_model["gdp_per_capita_growth"], alpha=0.3, color="steelblue")
plt.axvline(x=2.1, color="red", linestyle="--", linewidth=1.5, label="Replacement Level (2.1)")
plt.title("Fertility Rate vs GDP Per Capita Growth (1990-2020)")
plt.xlabel("Fertility Rate")
plt.ylabel("GDP Per Capita Growth (%)")
plt.legend()
plt.tight_layout()
plt.show()


# Chart 4: Correlation heatmap
# Shows the pairwise correlation between fertility rate and GDP growth

corr_matrix = df_model[["fertility_rate", "gdp_per_capita_growth"]].corr()

fig, ax = plt.subplots(figsize=(6, 5))
cax = ax.matshow(corr_matrix, cmap="coolwarm")
fig.colorbar(cax)

ax.set_xticks(range(len(corr_matrix.columns)))
ax.set_yticks(range(len(corr_matrix.columns)))
ax.set_xticklabels(corr_matrix.columns, rotation=45, ha="left")
ax.set_yticklabels(corr_matrix.columns)

for i in range(len(corr_matrix)):
    for j in range(len(corr_matrix)):
        ax.text(j, i, f"{corr_matrix.iloc[i, j]:.2f}", ha="center", va="center", color="black")

plt.title("Correlation Heatmap (1990-2020)", pad=20)
plt.tight_layout()
plt.show()


# Fixed effects OLS regression
# Country and year dummies absorb unobserved heterogeneity across both dimensions

model_gdp = smf.ols(
    "gdp_per_capita_growth ~ fertility_rate + C(country) + C(year)",
    data=df_model
).fit()

print(model_gdp.summary())


# Extract the fertility rate coefficient and key model diagnostics

coef = round(model_gdp.params["fertility_rate"], 4)
pval = f"{model_gdp.pvalues['fertility_rate']:.3f}"
rsq = round(model_gdp.rsquared, 3)
obs = int(model_gdp.nobs)

print("Fixed Effects Panel Regression Results")
print("Dependent Variable: GDP Per Capita Growth")
print("=" * 45)
print(f"Fertility Rate Coefficient : {coef}")
print(f"P-Value                    : {pval}")
print(f"R-Squared                  : {rsq}")
print(f"Observations               : {obs}")
print(f"Countries                  : 30")
print(f"Period                     : 1990 to 2020")
print("=" * 45)
print(f"Significant at 1% level    : {'Yes' if float(pval) < 0.01 else 'No'}")
