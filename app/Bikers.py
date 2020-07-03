import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

DATA_MODEL = "datos_modelo.csv"

DATA_PREDICCION = "data.csv"

ALL_CRIMES = -1

st.title("Crime Analysis for Bikers")
st.markdown(
    """
    Este proyecto lo hicimos como parte del programa Saturdays.IA, en la sede de Guadalajara, México.
    Saturdays.AI es una organización sin fines de lucro enfocada en hacer que la
    Inteligencia Artificial sea de fácil acceso y capacitar a los participantes
    bajo un esquema colaborativo y basado en proyectos aplicados.

[Ver el codigo aquí](https://github.com/orgs/saturdaysai-gdl2-plata)
"""
)

months = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}

crimes = {
    "Mostrar Todos": ALL_CRIMES,
    "Robo a cuentahabientes": 0,
    "Homicidio doloso": 1,
}


@st.cache(persist=True)
def load_data(data_file):
    data = pd.read_csv(data_file)
    return data


data_model = load_data(DATA_MODEL)
data_model = data_model.sample(8000000)

st.subheader("Datos Reales")

year_select = st.selectbox("Selecciona el año", ("2018", "2019"))

data_model = data_model[data_model["anio"] == int(year_select)]
data_model = data_model.sample(1000000)
month = st.slider("Mes a analizar", 1, 12)

data_model = data_model[data_model["mes"].eq(month)]
st.subheader("Actividad visualizada para %s" % (months[month]))
midpoint = (np.average(data_model["latitud"]), np.average(data_model["longitud"]))

st.write(
    pdk.Deck(
        map_style="mapbox://stylses/mapbox/light-v9",
        initial_view_state={
            "latitude": midpoint[0],
            "longitude": midpoint[1],
            "zoom": 11,
            "pitch": 50,
        },
        layers=[
            pdk.Layer(
                "HexagonLayer",
                data=data_model,
                mapbox_key="pk.eyJ1Ijoicm9jc3giLCJhIjoiY2tjMnFlY2d2MG02bzMwcDJnajRyeHY0MiJ9.xCf-UUXUG7APjdnOzzC9Gw",
                get_position=["longitud", "latitud"],
                radius=100,
                elevation_scale=4,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
                auto_highlight=True,
            ),
        ],
    )
)


if st.checkbox("Ver los datos crudos", False):
    st.subheader("Actividad de %s" % (months[month]))
    st.write(data_model)

# Segundo Mapa
st.subheader("Predicciones")
data_predict = load_data(DATA_PREDICCION)
data_predict = data_predict.sample(8000000)

selected_crime = st.selectbox("Selecciona un Crimen", list(crimes.keys()))

if crimes[selected_crime] != ALL_CRIMES:
    data_predict = data_predict[
        data_predict["y_homicidioDoloso"] == float(crimes[selected_crime])
    ]

data_predict = data_predict[data_predict["anio"] == int(year_select)]
data_predict = data_predict.sample(1000000)
data_predict = data_predict[data_predict["mes"].eq(month)]

st.subheader("Actividad visualizada paras %s" % (months[month]))
midpoint = (
    np.average(data_predict["location_lat"]),
    np.average(data_predict["location_lng"]),
)

st.write(
    pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state={
            "latitude": midpoint[0],
            "longitude": midpoint[1],
            "zoom": 11,
            "pitch": 50,
        },
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=data_predict,
                mapbox_key="pk.eyJ1Ijoicm9jc3giLCJhIjoiY2tjMnFlY2d2MG02bzMwcDJnajRyeHY0MiJ9.xCf-UUXUG7APjdnOzzC9Gw",
                get_position=["location_lng", "location_lat"],
                auto_highlight=True,
                get_radius=100,
                get_fill_color=[
                    "y_homicidioDoloso == 1 ? 255 : 0",
                    "y_homicidioDoloso == 1 ? 10 : 20",
                    110,
                    240,
                ],
                pickable=True,
            ),
        ],
    )
)

if st.checkbox("Ver los datos crudoss", False):
    st.subheader("Actividad de %s" % (months[month]))
    st.write(data_predict)
