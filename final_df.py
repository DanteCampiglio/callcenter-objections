import pandas as pd

# Rutas de archivos
detecciones_path = "/home/sagemaker-user/tmp/syngenta_callcenter/output/detecciones_validadas_bedrock.csv"
metricas_path = (
    "/home/sagemaker-user/tmp/syngenta_callcenter/output/metricas_llamadas.csv"
)
resumen_path = (
    "/home/sagemaker-user/tmp/syngenta_callcenter/output/resumen_llamadas.csv"
)

# Cargar CSVs
df_detecciones = pd.read_csv(detecciones_path, sep=";")
df_metricas = pd.read_csv(metricas_path)
df_resumen = pd.read_csv(resumen_path, sep=";", quotechar='"', engine="python")


# Normalizar nombres de columnas para join
df_detecciones["archivo"] = df_detecciones["archivo_origen"]
df_metricas["archivo"] = df_metricas["archivo"].str.strip()
df_resumen["archivo"] = df_resumen["archivo"].str.strip()

# Unir: primero detecciones con métricas
df_merge = pd.merge(df_metricas, df_detecciones, on="archivo", how="left")

# Unir con resúmenes
df_merge = pd.merge(df_merge, df_resumen, on="archivo", how="left")

# Guardar resultado final
salida_path = (
    "/home/sagemaker-user/tmp/syngenta_callcenter/output/tabla_final_llamadas.csv"
)
df_merge.to_csv(salida_path, index=False, sep=";", encoding="utf-8")

print(f"[INFO] Tabla final guardada en {salida_path}")
print(df_merge.head())
