"""Convierte los archivos originales del DANE en tablas pequeñas para la aplicación.

Uso:  python preparar_datos.py [carpeta_con_los_xlsx]

Entradas (descargadas del DANE, ver README):
    Anexo1.NoFetal2019_CE_15-03-23.xlsx, Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx, Divipola_CE_.xlsx
Salidas en data/:
    defunciones.csv.gz  conteos agrupados (municipio, mes, sexo, grupo de edad, manera de muerte, causa)
    municipios.csv      divipola con coordenadas
    causas.csv          códigos CIE-10 de tres caracteres con su descripción
"""
import os
import sys

import pandas as pd

ORIGEN = sys.argv[1] if len(sys.argv) > 1 else "."
DESTINO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DESTINO, exist_ok=True)


def ruta(nombre):
    return os.path.join(ORIGEN, nombre)


defunciones = pd.read_excel(ruta("Anexo1.NoFetal2019_CE_15-03-23.xlsx"), sheet_name="No_Fetales_2019", dtype=str)
defunciones["cod3"] = defunciones["COD_MUERTE"].str[:3]
agrupado = (defunciones.groupby(["COD_DANE", "MES", "SEXO", "GRUPO_EDAD1", "MANERA_MUERTE", "cod3"], as_index=False)
            .size().rename(columns={"size": "n"}))
agrupado.columns = ["cod_dane", "mes", "sexo", "grupo_edad", "manera", "cod3", "n"]
agrupado[["mes", "grupo_edad"]] = agrupado[["mes", "grupo_edad"]].astype(int)
agrupado.to_csv(os.path.join(DESTINO, "defunciones.csv.gz"), index=False)

div = pd.read_excel(ruta("Divipola_CE_.xlsx"), sheet_name="Hoja1", dtype=str)
geo = pd.read_excel(ruta("Divipola_CE_.xlsx"), sheet_name="Hoja3", header=None, skiprows=2, dtype=str)
geo = geo[[2, 5, 6]].rename(columns={2: "COD_DANE", 5: "lon", 6: "lat"})
for c in ("lon", "lat"):
    geo[c] = geo[c].str.replace(",", ".").astype(float)
mun = div[["COD_DANE", "COD_DEPARTAMENTO", "DEPARTAMENTO", "MUNICIPIO"]].merge(geo, on="COD_DANE", how="left")
mun.columns = ["cod_dane", "cod_dpto", "departamento", "municipio", "lon", "lat"]
mun.to_csv(os.path.join(DESTINO, "municipios.csv"), index=False)

cie = pd.read_excel(ruta("Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx"), header=None, skiprows=9, dtype=str)
causas = cie[[2, 3]].dropna().drop_duplicates(subset=2)
causas.columns = ["cod3", "causa"]
causas["causa"] = causas["causa"].str.strip()
causas.to_csv(os.path.join(DESTINO, "causas.csv"), index=False)

print("Registros originales:", len(defunciones), "| filas agrupadas:", len(agrupado))
