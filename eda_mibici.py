# -*- coding: utf-8 -*-
"""EDA MiBici.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1GlEczc1xrR4VW9-VFL7xajgSIArtXpIh

## Downloading dataset and making basic preparations to handle data
"""

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

# upload_to_s3(df)

def upload_to_s3(df):
    """## Upload dataset to an AWS S3 bucket"""
    import s3fs

    s3 = s3fs.S3FileSystem(key='<access-key>', secret='<secret-key>')

    # Use 'w' for py3, 'wb' for py2
    with s3.open('<bucket_name>/<filename>.csv', 'w') as f:
        df.to_csv(f, index=False)
        
  #Eliminar lineas duplicadas ----------
print(df.shape)
df.head(10)
df.tail()
df_unique= df.drop_duplicates(subset=None, keep='first', inplace=False)
print(df_unique.shape)

#Eliminar lineas completamente vacías --------
df_noempty = df_unique.dropna(axis=0, how='all', thresh=None, subset=None, inplace=False)
print(df_noempty.shape)
