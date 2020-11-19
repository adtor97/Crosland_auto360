from plotly import graph_objects as go
import pandas as pd
import plotly_express as px


def build_radar_coll(df_total, df_coll, df_auto):

    df_pilares_grouped = df_total.groupby("Pilar", as_index = False).mean()
    df_pilares_coll_grouped = df_coll.groupby("Pilar", as_index = False).mean()
    df_pilares_auto_grouped = df_auto.groupby("Pilar", as_index = False).mean()

    fig = go.Figure()

    if len(df_pilares_grouped)>0:
        fig.add_trace(go.Scatterpolar(
            r = df_pilares_grouped['value'].append(pd.Series(df_pilares_grouped['value'][0])),
            theta = df_pilares_grouped['Pilar'].append(pd.Series(df_pilares_grouped['Pilar'][0])),
            name = "Promedio general"
        ))
    else: pass

    if len(df_pilares_coll_grouped)>0:
        fig.add_trace(go.Scatterpolar(
            r = df_pilares_coll_grouped['value'].append(pd.Series(df_pilares_coll_grouped['value'][0])),
            theta = df_pilares_coll_grouped['Pilar'].append(pd.Series(df_pilares_coll_grouped['Pilar'][0])),
            name = "Tu promedio"
        ))
    else: pass

    if len(df_pilares_auto_grouped)>0:
        fig.add_trace(go.Scatterpolar(
            r = df_pilares_auto_grouped['value'].append(pd.Series(df_pilares_auto_grouped['value'][0])),
            theta = df_pilares_auto_grouped['Pilar'].append(pd.Series(df_pilares_auto_grouped['Pilar'][0])),
            name = "Autoevaluación"
        ))
    else: pass

    fig.update_traces(hoverinfo='r')
    return fig

def build_radar_general(df_total):

    df_pilares_grouped = df_total.groupby("Pilar", as_index = False).mean()

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r = df_pilares_grouped['value'].append(pd.Series(df_pilares_grouped['value'][0])),
        theta = df_pilares_grouped['Pilar'].append(pd.Series(df_pilares_grouped['Pilar'][0])),
        #name = "Promedio general"
    ))

    #fig = fig.to_html(full_html=False)
    #print(fig)
    return fig

def build_lines_coll(df_coll):

    df_pilares_grouped = df_coll.groupby(["Pilar", "Periodo"], as_index = False).mean()
    df_coll = df_coll.groupby("Periodo", as_index = False).mean()
    #print(df_pilares_grouped)
    df_pilares_grouped = df_pilares_grouped.sort_values("Periodo").reset_index(drop=True)

    fig = go.Figure()

    for pilar in df_pilares_grouped.Pilar.unique():

        df_pilar = df_pilares_grouped.loc[df_pilares_grouped["Pilar"] == pilar]
        fig.add_trace(go.Line(
            x = df_pilar['Periodo'],
            y = df_pilar['value'],
            name = pilar,
                    ))

    fig.add_trace(go.Line(
        x = df_coll['Periodo'],
        y = df_coll['value'],
        name = "General"
                ))

    fig.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=1.02,
    xanchor="right",
    x=1,
    font=dict(size=12),
    bgcolor='rgba(0,0,0,0)',
        ))

    #fig = fig.to_html(full_html=False)
    return fig
