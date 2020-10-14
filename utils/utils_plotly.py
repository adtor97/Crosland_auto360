from plotly import graph_objects as go
import pandas as pd
import plotly_express as px


def build_radar_coll(df_total, df_coll):

    df_pilares_grouped = df_total.groupby("Pilar", as_index = False).mean()
    df_pilares_coll_grouped = df_coll.groupby("Pilar", as_index = False).mean()

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r = df_pilares_grouped['value'].append(pd.Series(df_pilares_grouped['value'][0])),
        theta = df_pilares_grouped['Pilar'].append(pd.Series(df_pilares_grouped['Pilar'][0])),
        name = "Promedio general"
    ))

    fig.add_trace(go.Scatterpolar(
        r = df_pilares_coll_grouped['value'].append(pd.Series(df_pilares_coll_grouped['value'][0])),
        theta = df_pilares_coll_grouped['Pilar'].append(pd.Series(df_pilares_coll_grouped['Pilar'][0])),
        name = "Tu promedio"
    ))

    fig = fig.to_html(full_html=False)
    return fig

def build_radar_general(df_total):

    df_pilares_grouped = df_total.groupby("Pilar", as_index = False).mean()

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r = df_pilares_grouped['value'].append(pd.Series(df_pilares_grouped['value'][0])),
        theta = df_pilares_grouped['Pilar'].append(pd.Series(df_pilares_grouped['Pilar'][0])),
        title = "Promedio general"
    ))

    fig = fig.to_html(full_html=False)
    return fig

def build_lines_coll(df_coll):

    df_pilares_grouped = df_coll.groupby(["Pilar", "Periodo"], as_index = False).mean()
    df_coll = df_coll.groupby("Periodo", as_index = False).mean()
    print(df_pilares_grouped)
    df_pilares_grouped = df_pilares_grouped.sort_values("Periodo")

    fig = px.line(df_pilares_grouped[["value", "Periodo", "Pilar"]], x = "Periodo", y = "value", color='Pilar')
    fig.add_scatter(x = df_coll["Periodo"], y = df_coll["value"], name = "General",mode='lines')

    fig = fig.to_html(full_html=False)
    return fig
