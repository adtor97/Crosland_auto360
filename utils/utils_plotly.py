from plotly import graph_objects as go
import pandas as pd

def build_radar(df_total, df_coll):

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
