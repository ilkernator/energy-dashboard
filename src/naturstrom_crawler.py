import pandas as pd
import time
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
import streamlit as st


load_dotenv()

url_naturstrom = 'https://kundenservice.naturstrom.de/powercommerce/nsh/fo/portal/start'
payload = {
    'login_naturstrom': os.getenv("naturstrom_login_user"),
    'password_naturstrom': os.getenv("naturstrom_login_pw"),
}

@st.cache_data
def fetch_data_from_naturstrom(use_headless:bool = True) -> dict:
    progress_text = "Fetching data from website. Please wait."
    percent_complete = 0
    bar = st.progress(percent_complete, text=progress_text)
    chrome_options = Options()

    ua = UserAgent()
    userAgent = ua.random
    chrome_options.add_argument(f'user-agent={userAgent}')
    if use_headless:
        chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url_naturstrom)
    percent_complete += 5
    bar.progress(percent_complete, text="Driver is up and running...")
    time.sleep(4)
    # login to website
    percent_complete += 5
    bar.progress(percent_complete, text="Login to Website...")
    driver.find_element(By.XPATH,"""//*[@id="CybotCookiebotDialogBodyButtonDecline"]""").click()
    driver.find_element(By.XPATH,"""//input[@id="login"]""").send_keys(payload["login_naturstrom"])
    driver.find_element(By.XPATH,"""//input[@id="password"]""").send_keys(payload["password_naturstrom"])
    time.sleep(5)
    driver.find_element(By.XPATH,"""//*[@id="loginButton"]""").submit()
    time.sleep(25)
    percent_complete += 60
    bar.progress(percent_complete, text="Login complete...")
    abschlag = driver.find_element(By.XPATH,"""//*[@id="budgetBillingPlanContent1"]/div/p/span""")
    abschlag_fmt = int(abschlag.text.split(",")[0])

    driver.execute_script("window.scrollTo(0, 1000)")
    time.sleep(5)
    percent_complete += 10
    bar.progress(percent_complete, text="Access Consumption Page...")
    driver.find_element(By.XPATH,"""//*[@id="widgetMeterConsumptionLink"]""").click()
    time.sleep(3)
    percent_complete += 10
    bar.progress(percent_complete, text="Find Consumption Data...")
    driver.find_element(By.XPATH,"""//*[@id="main-process-cage"]/div/div[1]/div[3]/div[4]/div/div/div[2]/div[1]/ul/li[2]/a""").click()
    time.sleep(8)
    percent_complete += 5
    bar.progress(percent_complete, text="Find Consumption Data...")
    rows = driver.find_elements(By.XPATH,"""//*[@id="ems-analysis-details-tab1"]/div/div[2]/table/tbody""")
    time.sleep(2)
    list_of_rows = (rows[0].text).split("\n")
    my_dict = {"from": [], "to": [], "value": [], "unit": []}

    for row in list_of_rows:
        splitted_elements = re.split(r"(\s)",row)
        my_dict["from"].append(datetime.strptime(splitted_elements[0],'%d.%m.%Y').date())
        my_dict["to"].append(datetime.strptime(splitted_elements[4],'%d.%m.%Y').date())
        my_dict["value"].append(float(splitted_elements[6].replace(".","").replace(",",".")))
        my_dict["unit"].append(splitted_elements[8])
    
    percent_complete += 5
    bar.progress(percent_complete, text="Complete...")
    bar.empty()

    return my_dict, abschlag_fmt


@st.cache_data
def load_df_from_dict_naturstrom(data_dict: dict) -> pd.DataFrame:
    df = pd.DataFrame.from_dict(data_dict)
    df["days_total"] = df["to"] - df["from"]
    df["Tagesdurchschnitt"] = df.apply(lambda row: row.value / row.days_total.days, axis=1)

    price_df = pd.read_csv("resources/electric_prices.csv", sep=',')
    price_df["to"] = price_df["to"].apply(lambda x: datetime.strptime(x,'%d.%m.%Y').date())
    df = pd.merge(df,price_df, on='to', how='left')

    df["cost_eur"] = (df['price_ct_kwh'] *  df['value'])/100
    df["avg_cost_per_day"]= df.apply(lambda row: row.cost_eur / row.days_total.days, axis=1)
    df["x_axis"] = df.apply(lambda x: x["from"].strftime("%b %y") + " - " + x["to"].strftime("%b %y"), axis=1)
    df["test_col"] = df["to"].apply(lambda x: (f"{x.isoformat()}"))
    df["Durchschnitt_Referenz"] = 5.479
    df["Durchschnitt_Wohnung"] = df["Tagesdurchschnitt"].mean()
    
    return df