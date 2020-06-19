import pandas as pd

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

estaciones_df = pd.read_csv('https://saturdays-ai-gdl2-plata-mibici.s3-us-west-2.amazonaws.com/estaciones.csv')
df = df.merge(estaciones_df, left_on='Origen_Id', right_on='id', how= 'left')
df = df.merge(estaciones_df, left_on='Destino_Id', right_on='id', how= 'left')
df.drop(['id_x', 'id_y'], inplace = True, axis=1)
df.rename(columns={"latitud_x": "latitud_origen", "longitud_x": "longitud_origen"}, inplace = True)
df.rename(columns={"latitud_y": "latitud_destino", "longitud_y": "longitud_destino"}, inplace = True)

df_criminal = pd.read_csv('https://trello-attachments.s3.amazonaws.com/5e7ab7849f172231e1d8b386/5e7d5e0fec43d718240c71c7/cbf8668259455adfbabd3f686e410b41/incidencia_delictiva_jalisco18-19_filter.csv')

municipalities = ["GUADALAJARA", "ZAPOPAN", "SAN PEDRO TLAQUEPAQUE"]
null_values = ["N.D.", "N..D."]

df_criminal = df_criminal[df_criminal["Municipio"].isin(municipalities)]
df_criminal = df_criminal[~df_criminal["Colonia"].isin(null_values)]
