# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
from datetime import date
import plotly.express as px
import pandas as pd
import cycle_time_analys as ana
import firebase_app as fire
import time
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


df_sca = fire.get_data()


df_sca['date_created'] = pd.to_datetime(df_sca['date_created'],unit='ms')
df_sca['date_starting'] = pd.to_datetime(df_sca['date_starting'],unit='ms')
df_sca['date_resolution'] = pd.to_datetime(df_sca['date_resolution'],unit='ms')
df_sca['date_created_short'] = df_sca['date_created'].dt.date
df_sca['date_starting_short'] = df_sca['date_starting'].dt.date
df_sca['date_resolution_short'] = df_sca['date_resolution'].dt.date
print(df_sca['lead_time'].value_counts())
#print(df_sca['date_created'].dt.date)
fig = px.scatter(df_sca, x="date_created", y="lead_time",
                 color="quality", hover_name="summary",trendline="lowess",
                 hover_data=["story_points", "cycle_time", "date_resolution", "date_created","date_starting_short"],
                 log_x=False, size_max=60)

fig.update_layout(title='Lead Time Scatter Plot',
                   xaxis_title='Fecha Creación Tarea',
                   yaxis_title='Lead Time')
fig.update_xaxes(rangeslider_visible=True,ticklabelmode="period")
#fig.show()

fig2 = px.histogram(df_sca, x="date_resolution_short")
fig2.update_xaxes(
    dtick="M1",
    tickformat="%b\n%Y",
    ticklabelmode="period")
fig2.update_layout(title='Throughput Histogram',
                   xaxis_title='Periodo',
                   yaxis_title='Throughput')
fig2.update_xaxes(rangeslider_visible=True)

fig3 = px.scatter(df_sca, x="date_starting", y="cycle_time",
                 color="quality", hover_name="summary",trendline="lowess",
                 hover_data=["story_points", "lead_time", "date_resolution", "date_created","date_starting_short"],
                 log_x=False, size_max=60)
fig3.update_layout(title='Cycle Time Scatter Plot',
                   xaxis_title='Fecha Inicio Tarea',
                   yaxis_title='Cycle Time')
fig3.update_xaxes(ticklabelmode="period", rangeslider_visible=True)

mean_cycle_time = np.mean(df_sca['cycle_time'])
lead_cycle_time = np.mean(df_sca['lead_time'])

app.layout = html.Div([
    html.H6("Cycle Time vs Lead Time. TBBT"),
    html.Div(id='output-container-date-picker-range'),
    dcc.Graph(
        id='lead_time_scatter',
        figure=fig
    ),
    dcc.Graph(
        id='cycle_time_scatter',
        figure=fig3
    ),
    dcc.Graph(
        id='throughput_histo',
        figure=fig2
    ),
     html.H6("Cycle Time mean is {}".format(mean_cycle_time)),
     
     html.H6("Lead Time mean is {}".format(lead_cycle_time))
])

if __name__ == '__main__':
    app.run_server(debug=True)