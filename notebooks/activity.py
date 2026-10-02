import pandas as pd
d = pd.read_csv("../data/sources/web_orders_2025.csv")["Order Date"]
right = pd.to_datetime(d, format="%d/%m/%Y")
guess = pd.to_datetime(d, format="mixed")
print((right != guess).sum())

crm = pd.read_excel("../data/sources/crm_customers.xlsx", skiprows=2)
web = pd.read_csv("../data/sources/web_orders_2025.csv")
twice = crm.loc[crm["Customer ID"].duplicated(), "Customer ID"]
print(len(twice), web["Customer ID"].isin(twice).sum())
print(len(web.merge(crm, on="Customer ID", how="left")))

