# -*- coding: utf-8 -*-
"""Copy of Untitled3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1uvNar-cMyzolRTJoddmIUHu3i_2bKjhZ
"""
""" EDA for Join of atasets

This script allows to read, clean, analize and join MIBICI and criminalincidence datasets,
and show the result of analysis in a histogram. Also, the script does a training model.

Read process: 
    read the files to start the process

Clean process:
    Delete duplicated rows
    Delete Nan-value rows
    Delete the rows with a value less than 15 in the diff_seconds column

Join files:

This file contains the following function:
    * create_onedrive_directdownload
    * trainModel_scale
    * distFrom
"""

import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import ShuffleSplit
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import cross_val_score
from sklearn.compose import ColumnTransformer
import base64


def create_onedrive_directdownload(onedrive_link):
    """Returns a Oncedrive link for MIBICI dataset
        Parameters
        ----------
            onedrive_link: str
            the name of the link
        Returns
        -------
            resultUrl: str

        the encoded str link
    """
    data_bytes64 = base64.b64encode(bytes(onedrive_link, 'utf-8'))
    data_bytes64_String = data_bytes64.decode('utf-8').replace('/','_').replace('+','-').rstrip("=")
    resultUrl = f"https://api.onedrive.com/v1.0/shares/u!{data_bytes64_String}/root/content"
    return resultUrl


mibici_dataset_direct_url = create_onedrive_directdownload('https://1drv.ms/u/s!AllbB8dY7-XlonYbKR5K_UxVhb5N?e=2dyg0K')
estaciones_direct_url = create_onedrive_directdownload('https://1drv.ms/u/s!AllbB8dY7-XlondVkj-i2oSp7X0M?e=fq1fOv')
neighborhoods_lat_lng_direct_url = create_onedrive_directdownload('https://1drv.ms/u/s!AllbB8dY7-XlonigcNaWfXwaC5dC?e=ggEhzD')
criminal_incidence_direct_url = create_onedrive_directdownload('https://1drv.ms/u/s!AllbB8dY7-Xlonl9IYCBVwrS6wug?e=8JW4cU')

date_cols = ['Inicio_del_viaje', 'Fin_del_viaje']

df = pd.read_csv(
    mibici_dataset_direct_url,
    dtype={
        'Anio_de_nacimiento': pd.UInt16Dtype(),
        'Origen_Id': pd.UInt16Dtype(),
        'Destino_Id': pd.UInt16Dtype(),
        'Usuario_Id': pd.UInt32Dtype(),
        'Viaje_Id': pd.UInt32Dtype()
    },
    parse_dates=date_cols,
    date_parser=pd.to_datetime
)

# Eliminar lineas duplicadas ----------
df.drop_duplicates(subset=None, keep='first', inplace=True)

# Eliminar lineas completamente vacías --------
df.dropna(axis=0, how='all', thresh=None, subset=None, inplace=True)

#Sacamos la diferencia en segundos y se agrega a una columna llamada diff_seconds
df['diff_seconds'] = df['Fin_del_viaje'] - df['Inicio_del_viaje']
df['diff_seconds']= df['diff_seconds']/np.timedelta64(1,'s')

#Borramos todo lo que este menos de 15 Segundos en la columna diff_seconds
df.drop(df[df.diff_seconds < 15].index, inplace = True)

# Filtramos los registros para sólo mujeres
df = df[df["Genero"].isin(["F"])]

estaciones_df = pd.read_csv(estaciones_direct_url)
df = df.merge(estaciones_df, left_on='Origen_Id', right_on='id', how= 'left')
df = df.merge(estaciones_df, left_on='Destino_Id', right_on='id', how= 'left')
df.drop(['id_x', 'id_y'], inplace = True, axis=1)
df.rename(columns={"latitud_x": "latitud_origen", "longitud_x": "longitud_origen"}, inplace = True)
df.rename(columns={"latitud_y": "latitud_destino", "longitud_y": "longitud_destino"}, inplace = True)
df['mes'] = df['Inicio_del_viaje'].dt.month

# ======== Criminal Incidence ========

df_criminal = pd.read_csv(criminal_incidence_direct_url)

municipalities = ["GUADALAJARA", "ZAPOPAN", "SAN PEDRO TLAQUEPAQUE"]
null_values = ["N.D.", "N..D."]
crimes = ["LESIONES DOLOSAS", "ROBO DE MOTOCICLETA", "ROBO A CUENTAHABIENTES", "HOMICIDIO DOLOSO", "ROBO A NEGOCIO", "FEMINICIDIO"]
statuses_to_drop = ["ZERO_RESULTS"]

df_criminal = df_criminal[df_criminal["Municipio"].isin(municipalities)]
df_criminal = df_criminal[~df_criminal["Colonia"].isin(null_values)]
df_criminal = df_criminal[df_criminal["Delito"].isin(crimes)]

lat_lng = pd.read_csv(neighborhoods_lat_lng_direct_url)
lat_lng = lat_lng[~lat_lng["status"].isin(statuses_to_drop)]
df_criminal = df_criminal.merge(lat_lng, left_on='Colonia', right_on="colonia", how="left")
df_criminal.drop(['Mes', 'Clave_Mun', 'colonia', 'query', 'status'], axis = 1, inplace=True)

print("Deleting invalid coordinates...")
print("Total of rows: ", len(df_criminal.index))
indexNames = df_criminal[(df_criminal.location_lat < 20.3257581) | (df_criminal.location_lat > 20.9982375) | (df_criminal.location_lng < -103.6650327) | (df_criminal.location_lng > -103.0809884) ].index
df_criminal.drop(indexNames , inplace=True)
print("Total of rows after deletion: ", len(df_criminal.index))
print("Deleting invalid coordinates... Done.")


def trainModel_scale(model, features, data, nFoldList, nTest, scaler, output):
    for i in nFoldList:
        #y = data.ocupacion
        y = data[output]
        X = data[features]
        #categorical_cols = ['diaDeLaSemana']

        #scaler = RobustScaler()
        #categorical_transformer = Pipeline(steps=[
        #    ('onehot', OneHotEncoder(handle_unknown='ignore'))
        #])

        scaler = Pipeline(steps=[
            ('sca', scaler)
        ])


        preprocessor = ColumnTransformer(
            transformers=[
                #('cat', categorical_transformer, categorical_cols),
                ('sca', scaler, features)
            ])

        my_pipeline = Pipeline(steps=[('preprocessor', preprocessor),('model', model)])

        cv = ShuffleSplit( test_size = i, n_splits = nTest )
        #scores = -1 * cross_val_score(my_pipeline, X, y,
        #                              cv = cv,
        #                              scoring='neg_mean_absolute_error')
        scores = cross_val_score(my_pipeline, X, y,
                              cv = cv,
                              #scoring='accuracy')
                              scoring='precision')

        print("nFold", i)
        print(scores)
        #print("MAE scores: %0.5f(+/- %0.4f)" % (scores.mean(), scores.std()))


print("Test 1: DecisionTreeClassifier - Minmaxscaler...")
features = ['anio', 'mes', 'location_lat', 'location_lng']
output = 'y_lesionesDolosas'
all_rows = features
all_rows.append(output)
#model = linear_model.LinearRegression()
model = DecisionTreeClassifier()
nFoldList = [ 0.25, 0.20, 0.10 ]
nTest = 3
#data = ocupacionEstaciones_data.copy()
#data= df_criminal.copy()
data = df_criminal[all_rows].dropna()
convert_dict = {'anio': float, 'mes': float, 'y_lesionesDolosas': float}
data = data.astype(convert_dict)
#data = df_criminal.astype(np.float64)
print("Total of rows: ", len(data.index))
scaler = MinMaxScaler()
trainModel_scale(model, features, data, nFoldList, nTest, scaler, output)
print("Test 1: DecisionTreeClassifier - Minmaxscaler... Done.")

def distFrom(lat1, lng1, lat2, lng2):
    """Returns the haversine distance between two points
        Parameters
        ----------
            lat1: double
                Point 1 latitude 
            lng1: double
                Point 1 longitude
            lat2: double
                Point 2 latitude 
            lng2: double
                Point 2 longitude
        Returns
        -------
            R * c: double
                the haversine distance
    """

    #Radio de la Tierra en km
    R = 6373.0

    lat1 = np.radians(lat1)
    lon1 = np.radians(lng1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lng2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (np.sin(dlat/2))**2 + np.cos(lat1) * np.cos(lat2) * (np.sin(dlon/2))**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c


neighborhood_location_lat_lng = df_criminal.loc[:, ['Colonia', 'location_lat', 'location_lng']]
neighborhood_location_lat_lng.drop_duplicates(subset=['Colonia'], keep=False, inplace=True)

stations_with_crime_near = []

for _, neighborhood_info in neighborhood_location_lat_lng.iterrows():
    for _, station in estaciones_df.iterrows():
        dist = distFrom(
            float(neighborhood_info['location_lat']),
            float(neighborhood_info['location_lng']),
            float(station['latitud']),
            float(station['longitud'])
        )
        if dist <= 0.5:
            stations_with_crime_near.append(int(station['id']))

stations_with_crime_near = set(stations_with_crime_near)

stations = []

for _, station in estaciones_df.iterrows():
    station_id = int(station['id'])
    stations.append({'id': station_id, 'hasCrime': station_id in stations_with_crime_near})

stations = pd.DataFrame(stations)

# Filtramos los registros de MiBici sólo para mujeres
df_mibici_gender_filtered = df[df["Genero"].isin(["F"])]

trips_sum = df_mibici_gender_filtered['Origen_Id'].value_counts() + df_mibici_gender_filtered['Destino_Id'].value_counts()

trips_sum = pd.DataFrame(trips_sum)

stations_crimes_and_trips = stations.merge(trips_sum, right_index=True, left_on='id', how='right')

stations_crimes_and_trips.rename(columns={0: 'tripsSum'}, inplace=True)

stations_crimes_and_trips.sort_values(by="id", inplace=True)

import seaborn as sns
import matplotlib.pyplot as plt

a4_dims = (20, 15)
_, ax = plt.subplots(figsize=a4_dims)

chart = sns.barplot(x=stations_crimes_and_trips['id'], y=stations_crimes_and_trips['tripsSum'], hue=stations_crimes_and_trips['hasCrime'], ax=ax)
chart.set_xticklabels(chart.get_xticklabels(), rotation=45)

