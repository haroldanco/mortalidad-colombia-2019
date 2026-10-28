"""Aplicación web interactiva: mortalidad no fetal en Colombia, 2019 (Dash + Plotly)."""
import os

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dash_table, dcc, html

AQUI = os.path.dirname(os.path.abspath(__file__))
SEXOS = {"1": "Hombre", "2": "Mujer", "3": "Indeterminado"}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
GRUPOS_EDAD = {0: "<1 hora", 1: "<1 día", 2: "1-6 días", 3: "7-27 días", 4: "28-29 días", 5: "1-5 meses", 6: "6-11 meses",
               7: "1 año", 8: "2-4", 9: "5-9", 10: "10-14", 11: "15-19", 12: "20-24", 13: "25-29", 14: "30-34",
               15: "35-39", 16: "40-44", 17: "45-49", 18: "50-54", 19: "55-59", 20: "60-64", 21: "65-69",
               22: "70-74", 23: "75-79", 24: "80-84", 25: "85-89", 26: "90-94", 27: "95-99", 28: "100+", 29: "Desconocida"}
COLOR = {"Hombre": "#1F5FA8", "Mujer": "#D9822B", "Indeterminado": "#7A7A7A"}


# ------------------------------------------------------------------ datos
def cargar():
    d = pd.read_csv(os.path.join(AQUI, "data", "defunciones.csv.gz"), dtype={"cod_dane": str, "sexo": str, "cod3": str})
    m = pd.read_csv(os.path.join(AQUI, "data", "municipios.csv"), dtype={"cod_dane": str, "cod_dpto": str})
    c = pd.read_csv(os.path.join(AQUI, "data", "causas.csv"), dtype=str)
    d = d.merge(m[["cod_dane", "departamento", "municipio"]], on="cod_dane", how="left")
    d["sexo"] = d["sexo"].map(SEXOS)
    d["etiqueta_mpio"] = d["municipio"].str.title() + " (" + d["departamento"].str.title() + ")"
    d["causa"] = d["cod3"].map(dict(zip(c["cod3"], c["causa"]))).fillna("Sin descripción")
    centros = m.groupby("departamento", as_index=False).agg(lat=("lat", "mean"), lon=("lon", "mean"))
    return d, centros


DATOS, CENTROS = cargar()
DEPARTAMENTOS = sorted(DATOS["departamento"].dropna().unique())


def vacio(titulo):
    fig = px.scatter(title=titulo)
    fig.update_layout(template="plotly_white")
    return fig


def estilo(fig, titulo):
    fig.update_layout(title=dict(text=titulo, x=0.01, font=dict(size=15)), template="plotly_white",
                      margin=dict(l=10, r=10, t=50, b=10), legend_title_text="")
    return fig


# ------------------------------------------------------------------ diseño
def tarjeta(id_, titulo):
    return dbc.Card(dbc.CardBody([html.Div(titulo, className="text-muted small"), html.H4(id=id_, className="mb-0")]))


def grafico(id_, alto=380):
    return dbc.Card(dcc.Graph(id=id_, style={"height": f"{alto}px"}, config={"displaylogo": False}), className="mb-3")


app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], title="Mortalidad en Colombia 2019")
server = app.server

app.layout = dbc.Container([
    html.H2("Mortalidad no fetal en Colombia, 2019", className="mt-3 mb-0"),
    html.P("Fuente: DANE, Estadísticas Vitales (defunciones no fetales 2019).", className="text-muted"),
    dbc.Row([
        dbc.Col([html.Label("Sexo"), dcc.Dropdown(id="f-sexo", clearable=False, value="Todos",
                options=[{"label": x, "value": x} for x in ("Todos", "Hombre", "Mujer", "Indeterminado")])], md=3),
        dbc.Col([html.Label("Departamento"), dcc.Dropdown(id="f-dpto", clearable=False, value="Todos",
                options=[{"label": "Todos", "value": "Todos"}] + [{"label": x.title(), "value": x} for x in DEPARTAMENTOS])], md=5),
    ], className="mb-3"),
    dbc.Row([dbc.Col(tarjeta("k-total", "Defunciones"), md=3), dbc.Col(tarjeta("k-homicidios", "Homicidios"), md=3),
             dbc.Col(tarjeta("k-mes", "Mes con más defunciones"), md=3), dbc.Col(tarjeta("k-edad", "Grupo de edad más frecuente"), md=3)],
            className="mb-3"),
    dbc.Row([dbc.Col(grafico("g-mapa", 460), md=6), dbc.Col(grafico("g-lineas", 460), md=6)]),
    dbc.Row([dbc.Col(grafico("g-violentas"), md=6), dbc.Col(grafico("g-circular"), md=6)]),
    dbc.Row([dbc.Col(dbc.Card([html.H6("Diez principales causas de muerte", className="p-3 pb-0"),
                               dash_table.DataTable(id="t-causas", page_size=10, style_as_list_view=True,
                                                    style_header={"fontWeight": "bold", "backgroundColor": "#F0F3F7"},
                                                    style_cell={"textAlign": "left", "padding": "6px", "whiteSpace": "normal", "height": "auto"},
                                                    style_cell_conditional=[{"if": {"column_id": "Defunciones"}, "textAlign": "right"}])],
                              className="mb-3"), md=6),
             dbc.Col(grafico("g-histograma"), md=6)]),
    dbc.Row([dbc.Col(grafico("g-apiladas", 560), md=12)]),
], fluid=True, className="pb-4")


# ------------------------------------------------------------------ interacción
@app.callback(
    [Output("k-total", "children"), Output("k-homicidios", "children"), Output("k-mes", "children"), Output("k-edad", "children"),
     Output("g-mapa", "figure"), Output("g-lineas", "figure"), Output("g-violentas", "figure"), Output("g-circular", "figure"),
     Output("t-causas", "data"), Output("t-causas", "columns"), Output("g-histograma", "figure"), Output("g-apiladas", "figure")],
    [Input("f-sexo", "value"), Input("f-dpto", "value")])
def actualizar(sexo, dpto):
    por_sexo = DATOS if sexo == "Todos" else DATOS[DATOS["sexo"] == sexo]
    d = por_sexo if dpto == "Todos" else por_sexo[por_sexo["departamento"] == dpto]
    if d.empty:
        f = vacio("Sin datos para esta selección")
        return "0", "0", "-", "-", f, f, f, f, [], [], f, f

    # indicadores
    total = int(d["n"].sum())
    homicidios = int(d.loc[d["manera"] == "Homicidio", "n"].sum())
    mensual = d.groupby("mes", as_index=False)["n"].sum()
    mes_pico = MESES[int(mensual.loc[mensual["n"].idxmax(), "mes"]) - 1]
    edad = d.groupby("grupo_edad")["n"].sum()
    edad_pico = GRUPOS_EDAD[int(edad.idxmax())]

    # 1. mapa por departamento (respeta el filtro de sexo, muestra todo el país)
    dep = por_sexo.groupby("departamento", as_index=False)["n"].sum().merge(CENTROS, on="departamento")
    dep["Departamento"] = dep["departamento"].str.title()
    mapa = px.scatter_geo(dep, lat="lat", lon="lon", size="n", color="n", hover_name="Departamento",
                          hover_data={"n": ":,", "lat": False, "lon": False}, size_max=42,
                          color_continuous_scale="YlOrRd", labels={"n": "Defunciones"})
    mapa.update_geos(fitbounds="locations", visible=False, showcountries=True, countrycolor="#999",
                     showland=True, landcolor="#EEF2F6", showocean=True, oceancolor="#DCEBF7")
    estilo(mapa, "Defunciones por departamento")

    # 2. líneas: defunciones por mes
    mensual["Mes"] = mensual["mes"].map(lambda x: MESES[x - 1])
    lineas = px.line(mensual, x="Mes", y="n", markers=True, labels={"n": "Defunciones"})
    lineas.update_traces(line_color="#1F5FA8")
    lineas.update_yaxes(rangemode="tozero")
    estilo(lineas, "Defunciones por mes")

    # 3. barras: municipios con más homicidios
    hom = (d[d["manera"] == "Homicidio"].groupby("etiqueta_mpio", as_index=False)["n"].sum()
           .nlargest(5, "n").sort_values("n"))
    violentas = px.bar(hom, x="n", y="etiqueta_mpio", orientation="h", text="n", labels={"n": "Homicidios", "etiqueta_mpio": ""})
    violentas.update_traces(marker_color="#B3261E")
    estilo(violentas, "Cinco ciudades con más homicidios")

    # 4. circular: municipios con menor número de defunciones
    mpio = d.groupby("etiqueta_mpio", as_index=False)["n"].sum().sort_values(["n", "etiqueta_mpio"]).head(10)
    circular = px.pie(mpio, names="etiqueta_mpio", values="n", hole=0.35)
    circular.update_traces(textinfo="value", sort=False)
    estilo(circular, "Diez ciudades con menos defunciones registradas")

    # 5. tabla: diez principales causas
    causas = (d.groupby(["cod3", "causa"], as_index=False)["n"].sum().nlargest(10, "n"))
    causas.columns = ["Código", "Causa", "Defunciones"]
    columnas = [{"name": c, "id": c} for c in causas.columns]
    datos_tabla = causas.to_dict("records")

    # 6. histograma: edad al morir
    edades = d.groupby("grupo_edad", as_index=False)["n"].sum()
    edades["Grupo de edad"] = edades["grupo_edad"].map(GRUPOS_EDAD)
    hist = px.bar(edades, x="Grupo de edad", y="n", labels={"n": "Defunciones"})
    hist.update_traces(marker_color="#2E7D6B")
    hist.update_xaxes(categoryorder="array", categoryarray=list(GRUPOS_EDAD.values()), tickangle=-60)
    hist.update_layout(bargap=0.02)
    estilo(hist, "Distribución de defunciones por grupo de edad")

    # 7. barras apiladas por sexo en cada departamento (todo el país)
    ap = DATOS.groupby(["departamento", "sexo"], as_index=False)["n"].sum()
    orden = ap.groupby("departamento")["n"].sum().sort_values().index
    ap["Departamento"] = ap["departamento"].str.title()
    apiladas = px.bar(ap, y="Departamento", x="n", color="sexo", orientation="h", color_discrete_map=COLOR,
                      category_orders={"Departamento": [o.title() for o in orden]}, labels={"n": "Defunciones", "sexo": ""})
    estilo(apiladas, "Defunciones por departamento y sexo")

    fmt = lambda x: f"{x:,}".replace(",", ".")
    return (fmt(total), fmt(homicidios), mes_pico, edad_pico, mapa, lineas, violentas, circular,
            datos_tabla, columnas, hist, apiladas)


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", 8050)))
