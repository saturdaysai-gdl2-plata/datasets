import pandas as pd
import numpy as np
import base64


def create_onedrive_directdownload(onedrive_link):
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

df['anio'] = df['Inicio_del_viaje'].dt.year
df_filtrado = df.drop(['Viaje_Id', 'Usuario_Id', 'Genero', 'Anio_de_nacimiento', 'Inicio_del_viaje', 'Fin_del_viaje', 'Origen_Id', 'Destino_Id', 'diff_seconds'], axis = 1)
df_primero = df_filtrado.loc[:, [ 'latitud_origen', 'longitud_origen', 'mes', 'anio']]
df_segundo = df_filtrado.loc[:, [ 'latitud_destino', 'longitud_destino', 'mes', 'anio']]
df_primero.rename(columns={'latitud_origen': 'latitud','longitud_origen':'longitud'}, inplace=True)
df_segundo.rename(columns={'latitud_destino': 'latitud','longitud_destino':'longitud'}, inplace=True)
df_new = pd.concat([df_primero, df_segundo])