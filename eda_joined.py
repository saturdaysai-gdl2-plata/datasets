import pandas as pd
import numpy as np

date_cols = ['Inicio_del_viaje', 'Fin_del_viaje']

df = pd.read_csv(
    'https://saturdays-ai-gdl2-plata-mibici.s3-us-west-2.amazonaws.com/data.csv',
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

estaciones_df = pd.read_csv('https://saturdays-ai-gdl2-plata-mibici.s3-us-west-2.amazonaws.com/estaciones.csv')
df = df.merge(estaciones_df, left_on='Origen_Id', right_on='id', how= 'left')
df = df.merge(estaciones_df, left_on='Destino_Id', right_on='id', how= 'left')
df.drop(['id_x', 'id_y'], inplace = True, axis=1)
df.rename(columns={"latitud_x": "latitud_origen", "longitud_x": "longitud_origen"}, inplace = True)
df.rename(columns={"latitud_y": "latitud_destino", "longitud_y": "longitud_destino"}, inplace = True)
df['mes'] = df['Inicio_del_viaje'].dt.month

# ======== Criminal Incidence ========

df_criminal = pd.read_csv('https://trello-attachments.s3.amazonaws.com/5e7ab7849f172231e1d8b386/5e7d5e0fec43d718240c71c7/cbf8668259455adfbabd3f686e410b41/incidencia_delictiva_jalisco18-19_filter.csv')

municipalities = ["GUADALAJARA", "ZAPOPAN", "SAN PEDRO TLAQUEPAQUE"]
null_values = ["N.D.", "N..D."]
crimes = ["LESIONES DOLOSAS", "ROBO DE MOTOCICLETA", "ROBO A CUENTAHABIENTES", "HOMICIDIO DOLOSO", "ROBO A NEGOCIO", "FEMINICIDIO"]
statuses_to_drop = ["ZERO_RESULTS"]

df_criminal = df_criminal[df_criminal["Municipio"].isin(municipalities)]
df_criminal = df_criminal[~df_criminal["Colonia"].isin(null_values)]
df_criminal = df_criminal[df_criminal["Delito"].isin(crimes)]
df_criminal = df_criminal[~df_criminal["status"].isin(statuses_to_drop)]

lat_lng = pd.read_csv("https://saturdays-ai-gdl2-plata-mibici.s3-us-west-2.amazonaws.com/neighborhoods_latlng.csv")
df_criminal = df_criminal.merge(lat_lng, left_on='Colonia', right_on="colonia", how="left")
df_criminal.drop(['Mes', 'Clave_Mun', 'colonia', 'query', 'status'], axis = 1, inplace=True)


def distFrom(lat1, lng1, lat2, lng2):
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
neighborhood_location_lat_lng['Nearest_station'] = ""
neighborhood_location_lat_lng['Distance_to_nearest_station'] = ""

nearest_stations = []
min_distances = []

for _, row in neighborhood_location_lat_lng.iterrows():
    distances = []
    for _, station in estaciones_df.iterrows():
        dist = distFrom(float(row['location_lat']), float(row['location_lng']), float(station['latitud']), float(station['longitud']))
        distances.append({'station': station['id'], 'distance': dist})

    distances_df = pd.DataFrame(distances)
    distances_df = distances_df[distances_df['distance'] == distances_df['distance'].min()]
    nearest_stations.append(int(distances_df['station'].values[0]))
    min_distances.append(distances_df['distance'].values[0])

neighborhood_location_lat_lng['Distance_to_nearest_station'] = min_distances
neighborhood_location_lat_lng['Nearest_station'] = nearest_stations

df_criminal = df_criminal.merge(lat_lng, left_on='Colonia', right_on="Colonia", how="left")
neighborhood_location_lat_lng.drop(['location_lat', 'location_lng'], axis = 1, inplace=True)
df_criminal = df_criminal.merge(neighborhood_location_lat_lng, left_on='Colonia', right_on="Colonia", how="left")

df_criminal_with_stations_near = df_criminal[df_criminal['Distance_to_nearest_station'] <= 1.5]
