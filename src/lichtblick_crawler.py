import pandas as pd
import numpy as np
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import streamlit as st


load_dotenv()

url_lichtblick = 'https://anmelden.lichtblick.de/lichtblickitb2cprod.onmicrosoft.com/B2C_1A_signin/oauth2/v2.0/authorize?scope=https%3A%2F%2Flichtblickitb2cprod.onmicrosoft.com%2Fgraph-gateway%2Fservice-view.access+openid+profile+offline_access&response_type=code&client_id=35307b13-91eb-43e0-adc6-4f279766044e&redirect_uri=https%3A%2F%2Flichtblick.de%2Fapi%2Fauth%2Fcallback%2Fsignin&code_challenge=lEa72nqGb2PbZfe_yR1I4Qt7oPwlGZO_wchpBZgauDU&code_challenge_method=S256'
url_lichtblick_2 = 'https://www.lichtblick.de/konto/ueberblick/'
payload = {
    'login_lichtblick': os.getenv("lichtblick_login_user"),
    'password_lichtblick': os.getenv("lichtblick_login_pw"),
}


@st.cache_data
def fetch_data_from_lichtblick(use_headless:bool = True) -> dict:
    chrome_options = Options()

    if use_headless:
        chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url_lichtblick)
    time.sleep(5)

    driver.find_element(By.XPATH,"""//input[@id="email"]""").send_keys(payload["login_lichtblick"])
    driver.find_element(By.XPATH,"""//input[@id="password"]""").send_keys(payload["password_lichtblick"])

    time.sleep(5)
    driver.find_element(By.XPATH,"""//*[@id="next"]""").click()
    time.sleep(5)

    driver.get(url_lichtblick_2)
    time.sleep(5)

    shadow_root = driver.find_element(By.CSS_SELECTOR, "#usercentrics-root").shadow_root
    shadow_root.find_element(By.CSS_SELECTOR,"button[data-testid='uc-accept-all-button']").click()
    time.sleep(5)
    driver.find_element(By.XPATH,"""/html/body/div[1]/main/main/div[2]/article/article/div/div[1]/a[1]/div[1]/div""").click()
    time.sleep(3)

    zaehlerstand = driver.find_elements(By.XPATH,"""/html/body/div[1]/main/main/div[2]/article/section/div/div[2]/div""")
    data_list = (zaehlerstand[0].text).split("\n")

    zaehlerstand_dict = {"date": [], "value": [], "unit": []}
    zaehlerstand_dict["date"].extend([i for i in data_list[::4]])
    zaehlerstand_dict["value"].extend([i.replace(".","").replace(",",".") for i in data_list[2::4]])
    zaehlerstand_dict["unit"].extend([i for i in data_list[3::4]])

    driver.find_element(By.XPATH,"""/html/body/div[1]/main/main/div[2]/article/aside/div/nav/ul/li[2]/a/div/div/span""").click()
    time.sleep(3)
    abschlaege = driver.find_elements(By.XPATH,"""/html/body/div[1]/main/main/div[2]/article/section/div/div/div/div""")
    data_list = (abschlaege[0].text).split("\n")

    abschlaege_dict = {"date": [], "value": [], "unit": []}
    abschlaege_dict["date"].extend([i for i in data_list[::4]])
    abschlaege_dict["value"].extend([i.replace(".","").replace(",",".") for i in data_list[2::4]])
    abschlaege_dict["unit"].extend([i for i in data_list[3::4]])

    return zaehlerstand_dict, abschlaege_dict


@st.cache_data
def load_df_from_dict_lichtbllick(data_dict: dict) -> pd.DataFrame:
    df = pd.DataFrame.from_dict(data_dict)
    df["date"] = df["date"].apply(lambda x: datetime.strptime(x,'%d.%m.%Y').date())

    df.sort_values(by="date", inplace=True)

    df["previous_date"] = df["date"].shift(1).fillna(datetime(2020,3,20).date())
    df["count_days"] = (df["date"] - df["previous_date"]).apply(lambda x: x.days)
    df["value"] = df["value"].apply(lambda x: float(x))
    df["Durchschnitt_Wohnung"] = df["value"].mean()
    df["sum_value"] = df["value"].sum()
    df["x_axis"] = df["date"].apply(lambda x: x.isoformat())
    df["previous_value"] = df["value"].shift(1).fillna(0)
    df["consumption"] = df["value"] - df["previous_value"]
    df["consumption_per_day"] = df["consumption"]/df["count_days"]
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df["consumption_avg"] = df["consumption_per_day"].mean()

    return df