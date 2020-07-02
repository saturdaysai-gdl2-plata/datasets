import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import ShuffleSplit
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import cross_val_score
from sklearn.compose import ColumnTransformer
import numpy as np
import base64

def create_onedrive_directdownload(onedrive_link):
    data_bytes64 = base64.b64encode(bytes(onedrive_link, 'utf-8'))
    data_bytes64_String = data_bytes64.decode('utf-8').replace('/','_').replace('+','-').rstrip("=")
    resultUrl = f"https://api.onedrive.com/v1.0/shares/u!{data_bytes64_String}/root/content"
    return resultUrl

##MiBici
mibici_dataset_direct_url = create_onedrive_directdownload('https://1drv.ms/u/s!AllbB8dY7-XlonYbKR5K_UxVhb5N?e=2dyg0K')
estaciones_direct_url = create_onedrive_directdownload('https://1drv.ms/u/s!AllbB8dY7-XlondVkj-i2oSp7X0M?e=fq1fOv')

date_cols = ['Inicio_del_viaje', 'Fin_del_viaje']

print('Loading MiBici data...')
df = pd.read_csv(
    mibici_dataset_direct_url,
    #dtype={
    #    'Anio_de_nacimiento': pd.UInt16Dtype(),
    #    'Origen_Id': pd.UInt16Dtype(),
    #    'Destino_Id': pd.UInt16Dtype(),
    #    'Usuario_Id': pd.UInt32Dtype(),
    #    'Viaje_Id': pd.UInt32Dtype()
    #},
    parse_dates=date_cols,
    date_parser=pd.to_datetime
)
print('Done.')

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

del(estaciones_df)

df.drop(['id_x', 'id_y'], inplace = True, axis=1)
df.rename(columns={"latitud_x": "latitud_origen", "longitud_x": "longitud_origen"}, inplace = True)
df.rename(columns={"latitud_y": "latitud_destino", "longitud_y": "longitud_destino"}, inplace = True)
df['mes'] = df['Inicio_del_viaje'].dt.month

df['anio'] = df['Inicio_del_viaje'].dt.year
df_filtrado = df.drop(['Viaje_Id', 'Usuario_Id', 'Genero', 'Anio_de_nacimiento', 'Inicio_del_viaje', 'Fin_del_viaje', 'Origen_Id', 'Destino_Id', 'diff_seconds'], axis = 1)

del(df)

df_primero = df_filtrado.loc[:, [ 'latitud_origen', 'longitud_origen', 'mes', 'anio']]
df_segundo = df_filtrado.loc[:, [ 'latitud_destino', 'longitud_destino', 'mes', 'anio']]

del(df_filtrado)

df_primero.rename(columns={'latitud_origen': 'latitud','longitud_origen':'longitud'}, inplace=True)
df_segundo.rename(columns={'latitud_destino': 'latitud','longitud_destino':'longitud'}, inplace=True)
df_new = pd.concat([df_primero, df_segundo])

del(df_primero)
del(df_segundo)

df_new.rename(columns={'latitud': 'location_lat','longitud':'location_lng'}, inplace=True)
X_test = df_new[['anio', 'mes', 'location_lat', 'location_lng']]
del(df_new)

##Criminal

criminal_incidence_direct_url = create_onedrive_directdownload('https://1drv.ms/u/s!AllbB8dY7-Xlonl9IYCBVwrS6wug?e=8JW4cU')
neighborhoods_lat_lng_direct_url = create_onedrive_directdownload('https://1drv.ms/u/s!AllbB8dY7-XlonigcNaWfXwaC5dC?e=ggEhzD')

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

df_criminal['y_lesionesDolosas'] = 0
df_criminal['y_roboMotocicleta'] = 0
df_criminal['y_roboCuentahabientes'] = 0
df_criminal['y_homicidioDoloso'] = 0
df_criminal['y_roboNegocio'] = 0
df_criminal['y_feminicidio'] = 0

df_criminal.loc[df_criminal.Delito == 'LESIONES DOLOSAS', 'y_lesionesDolosas'] = 1
df_criminal.loc[df_criminal.Delito == 'ROBO DE MOTOCICLETA', 'y_roboMotocicleta'] = 1
df_criminal.loc[df_criminal.Delito == 'ROBO A CUENTAHABIENTES', 'y_roboCuentahabientes'] = 1
df_criminal.loc[df_criminal.Delito == 'HOMICIDIO DOLOSO', 'y_homicidioDoloso'] = 1
df_criminal.loc[df_criminal.Delito == 'ROBO A NEGOCIO', 'y_roboNegocio'] = 1
df_criminal.loc[df_criminal.Delito == 'FEMINICIDIO', 'y_feminicidio'] = 1

df_criminal.rename(columns={"Año": "anio", "Número_mes": "mes"}, inplace=True)

print("Deleting invalid coordinates...")
print("Total of rows: ", len(df_criminal.index))
indexNames = df_criminal[(df_criminal.location_lat < 20.3257581) | (df_criminal.location_lat > 20.9982375) | (df_criminal.location_lng < -103.6650327) | (df_criminal.location_lng > -103.0809884) ].index
df_criminal.drop(indexNames , inplace=True)
print("Total of rows after deletion: ", len(df_criminal.index))
print("Deleting invalid coordinates... Done.")

##trainAndPredict

def trainAndPredict(model, features, data, scaler, output, categorical_cols, X_test):
    #y = data.ocupacion
    y = data[output]
    X = data[features]
    #categorical_cols = ['diaDeLaSemana']

    #scaler = RobustScaler()
    categorical_transformer = Pipeline(steps=[
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    scaler = Pipeline(steps=[
        ('sca', scaler) 
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', categorical_transformer, categorical_cols),
            ('sca', scaler, features)                    
        ])

    my_pipeline = Pipeline(steps=[('preprocessor', preprocessor),('model', model)])
    
    print('Model Fitting...')
    my_pipeline.fit(X, y)
    print('Done.')
    
    print('Predicting...')
    y_pred = my_pipeline.predict(X_test)
    print('Done.')
    
    return y_pred

output = 'y_homicidioDoloso'
features = ['anio', 'mes', 'location_lat', 'location_lng']
all_rows = features + output_list
model = DecisionTreeClassifier()
data = df_criminal[(df_criminal['y_roboCuentahabientes'] == 1) | (df_criminal['y_homicidioDoloso'] == 1)][all_rows].dropna()
scaler = MinMaxScaler()
categorical_cols = ['anio', 'mes']
convert_dict = {'anio': float, 'mes': float, output: float}
data = data.astype(convert_dict) 

y_pred = trainAndPredict(model, features, data, scaler, output, categorical_cols, X_test)

X_test.assign(y_homicidioDoloso = y_pred)
del(y_pred)

print('Saving file...')
X_test.to_csv(r'data.csv', index = False)
print('Done.')

print('All finished successfully.')