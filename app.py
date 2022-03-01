#!/usr/bin/env python

import base64, io
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from os.path import isfile, isdir, abspath, join as pjoin, dirname, splitext, basename
from os import makedirs, getenv, remove, listdir

import pandas as pd
import numpy as np
import logging
from glob import glob

from subprocess import check_call

SCRIPTDIR=dirname(abspath(__file__))

# initial list of Figures
ROOTDIR= getenv("EEG_QC_PHOENIX")
if not ROOTDIR:
    print('Define env var EEG_QC_PHOENIX and try again')
    exit(1)
dirs= glob(ROOTDIR+'/**/Figures', recursive=True)
print(ROOTDIR)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',dbc.themes.BOOTSTRAP,'styles.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True, title='EEG Qc Tool', assets_folder=ROOTDIR, assets_url_path="/")
log= logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app.layout= html.Div(
    children= [
        html.H3('EEG Qc Tool'),

        html.Div(dcc.Input(id='start')), '--', html.Div(dcc.Input(id='end')),
        html.Div(html.Button('Filter', id='date-filter', n_clicks=0)),

        html.Button('Save', id='save'),
        html.Div(id='last-save'),

        html.Hr(),
        html.Div(id='table'),
        html.Br()
    ]

)

suffixes= "_QCimpedance, _QClineNoise, _QCcounts, _QCresponseAccuracy, _QCresponseTimes, _QCrestAlpha".split(', ')

@app.callback(Output('table','children'),
    [Input('start','value'), Input('end','value'), Input('date-filter', 'n_clicks')])
def render_table(start, end, click):

    # df= pd.DataFrame(columns=['sub-id','ses-id']+ suffixes)
    rows= []
    for i,d in enumerate(dirs[:3]):
        parts= d.split('/')
        sub= parts[-4]
        ses= parts[-2].split('-')[1]
        imgs= glob(f'{d}/*_QC*png')
        imgs= [img for img in imgs if not img.endswith('_QC.png')]
        
        rows.append(
            dbc.Row(
                [dbc.Col(html.Div(sub)), dbc.Col(html.Div(ses))]+ \
                [dbc.Col(html.Img(src=img.replace(ROOTDIR,''))) for img in imgs[3:]]
            )
        )


    if click and start and end:
        start=""
        end=""
        
        # filter the data

    
    return rows


# TODO
# callback for save and last-save

if __name__=='__main__':
    app.run_server(debug=True, host='localhost')

