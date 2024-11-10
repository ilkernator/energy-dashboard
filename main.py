import pandas as pd
import streamlit as st

from src.lichtblick_crawler import fetch_data_from_lichtblick, load_df_from_dict_lichtbllick
from src.naturstrom_crawler import fetch_data_from_naturstrom, load_df_from_dict_naturstrom


def create_streamlit_elements_naturstrom(data: pd.DataFrame) -> None:
    min_value=data["from"].min()
    max_value=data["to"].max()
    value = (min_value, max_value)

    Model = st.slider(
       '',
        min_value=min_value,
        max_value=max_value,
        value=value,
        format="MMM YYYY"
    )

    selmin, selmax = Model
   
    data = df.loc[(df['from'] >= selmin) & (df['to'] <= selmax)]

    col3, col4, col9, col5 = st.columns([1, 1, 1, 2])
    col3.metric("Gesamtverbrauch", f'{int(data.value.sum())} kW')
    col4.metric("Gesamtkosten", f'{round(data.cost_eur.sum(),2)} €')
    col9.metric("Aktueller Abschlag", f'{round(data.abschlag.max(),2)} €/Monat')
    col5.metric(
        "Betrachteter Zeitraum", 
        f'{selmin.strftime("%b %Y")} - {selmax.strftime("%b %Y")} ({data["days_total"].sum().days} Tage)')
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Durchschnittskosten pro Tag :moneybag:")
        st.line_chart(
            data,
            x="test_col", 
            y=["avg_cost_per_day"], 
            x_label = "Abrechnungszeitraum", 
            y_label="€",
            color=["#f19885"]
        )
        
    with col2:
        st.subheader("Naturstrom Preisentwicklung :chart:")
        st.line_chart(
            data,
            x="test_col", 
            y=["price_ct_kwh"], 
            x_label = "Abrechnungszeitraum", 
            y_label="ct/kwh"
        )
    with st.container():
        st.subheader("Durchschnittsverbrauch pro Tag :zap:")
        st.line_chart(
            data,
            x="test_col", 
            y=["Tagesdurchschnitt", "Durchschnitt_Referenz", "Durchschnitt_Wohnung"], 
            x_label = "Abrechnungszeitraum", 
            y_label=["kW"],
            color=["#61a1f2", "#e87be5", "#51f088"]
        )
    col6, col7,col8 = st.columns([1,1,3])
    col6.metric("Durchschnitt_Referenz", f'{round(data["Durchschnitt_Referenz"].max(),2)} kW')
    col7.metric("Durchschnitt_Wohnung", f'{round(data["Durchschnitt_Wohnung"].max(),2)} kW')
    

def create_steamlit_elements_lichtblick(zaehlerstand_df: pd.DataFrame, abschlag_df: pd.DataFrame) -> None:

    abschlag_df.rename(columns={"value": "Abschlag"}, inplace=True)
    zaehlerstand_df.rename(columns={"value": "Zählerstand_Wohnung"}, inplace=True)
    zaehlerstand_df.rename(columns={"consumption_per_day": "Tagesdurchschnitt"}, inplace=True)
    zaehlerstand_df.rename(columns={"consumption_avg": "Verbrauch_Durchschnitt"}, inplace=True)
    
    
    min_value_zaehlerstand=zaehlerstand_df["date"].min()
    min_value_abschlag=abschlag_df["date"].min()
    absolute_min = min(min_value_zaehlerstand, min_value_abschlag)

    max_value_zaehlerstand=zaehlerstand_df["date"].max()
    max_value_abschlag=abschlag_df["date"].max()
    absolute_max = max(max_value_zaehlerstand, max_value_abschlag)

    value_2 = (absolute_min, absolute_max)

    Model_2 = st.slider(
       '',
        min_value=absolute_min,
        max_value=absolute_max,
        value=value_2,
        format="MMM YYYY"
    )

    selmin_2, selmax_2 = Model_2
   
    zaehlerstand_df["Durchschnitt_Referenz"] = 910/365 
    zaehlerstand_df["Referenz_2_PH_Gesamt"] = zaehlerstand_df["Durchschnitt_Referenz"] * ((selmax_2-selmin_2).days)
    abschlag_df = abschlag_df.loc[(abschlag_df['date'] >= selmin_2) & (abschlag_df['date'] <= selmax_2)]
    zaehlerstand_df = zaehlerstand_df.loc[(zaehlerstand_df['date'] >= selmin_2) & (zaehlerstand_df['date'] <= selmax_2)]

    col11, col12, col13, col14 = st.columns([1, 1, 1, 2])
    col11.metric("Gesamtverbrauch", f"{round(zaehlerstand_df.loc[zaehlerstand_df['date'].idxmax()]['Zählerstand_Wohnung'],0)} m3")
    col12.metric("Gesamtkosten", f'{round(abschlag_df["Abschlag"].sum(),2)} €')
    col13.metric("Aktueller Abschlag", f"{round(abschlag_df.loc[abschlag_df['date'].idxmax()]['Abschlag'],0)} €/Monat")
    col14.metric(
        "Betrachteter Zeitraum", 
        f'{selmin_2.strftime("%b %Y")} - {selmax_2.strftime("%b %Y")} ({(selmax_2-selmin_2).days} Tage)'
    )
    
    st.divider()
    col9, col10 = st.columns(2)
    with col9:
        st.subheader("Abschlag :moneybag:")
        st.line_chart(
            abschlag_df,
            x="x_axis", 
            y=["Abschlag", "Durchschnitt_Wohnung"], 
            x_label = "Abrechnungsdatum", 
            y_label="€",
            color=["#f19885", "#51f088"]
        )

    with col10:
        st.subheader("Zählerstand :chart:")
        st.line_chart(
            zaehlerstand_df,
            x="x_axis", 
            y=["Zählerstand_Wohnung", "Referenz_2_PH_Gesamt"], 
            x_label = "Abrechnungsdatum", 
            y_label="m3",
            color=["#51f088", "#61a1f2"]
        )

    with st.container():
        st.subheader("Durchschnittsverbrauch pro Tag :dash:")
        st.line_chart(
            zaehlerstand_df,
            x="x_axis", 
            y=["Verbrauch_Durchschnitt", "Durchschnitt_Referenz", "Tagesdurchschnitt"], 
            x_label = "Abrechnungsdatum", 
            y_label=["m3"],
            color=["#61a1f2", "#51f088", "#e87be5"]
        )

    col15, col16,col17 = st.columns([1,1,3])
    col15.metric("Durchschnitt_Referenz", f'{round(zaehlerstand_df["Durchschnitt_Referenz"].max(),2)} m3')
    col16.metric("Durchschnitt_Wohnung", f'{round(zaehlerstand_df["Verbrauch_Durchschnitt"].max(),2)} m3')


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    st.title("Energieverbrauch")
    st.subheader("Fürstenbergerstraße 157 :house:")
    
    tab1, tab2 = st.tabs(["Strom", "Gas"])

    with tab1:
        st.subheader("Stromverbrauch :zap:")
        st.caption("Übersicht über den Stromverbrauch und die daraus entstandenen Kosten basierend auf Naturstrom-Daten.")
        st.divider()
        raw_data, abschlag = fetch_data_from_naturstrom()
        df: pd.DataFrame = load_df_from_dict_naturstrom(raw_data)
        df["abschlag"] = abschlag
        create_streamlit_elements_naturstrom(df)

    with tab2:
        st.subheader("Gasverbrauch :dash:")
        st.caption("Übersicht über den Gasverbrauch und die daraus entstandenen Kosten basierend auf Lichtblick-Daten.")
        st.divider()
        zaehlerstand, abschlaege = fetch_data_from_lichtblick()
        df_zaehlerstand = load_df_from_dict_lichtbllick(zaehlerstand)
        df_abschlag = load_df_from_dict_lichtbllick(abschlaege)
        create_steamlit_elements_lichtblick(df_zaehlerstand, df_abschlag)