#!/usr/bin/env python

import base64, io
import dash
from dash import dcc, html, dash_table, Dash, callback_context
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from os.path import isfile, isdir, abspath, join as pjoin, dirname, splitext, basename
from os import makedirs, getenv, remove, listdir

import re
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

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',dbc.themes.BOOTSTRAP,'styles.css']
app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True, title='EEG Qc Tool', assets_folder=ROOTDIR, assets_url_path="/")
log= logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

suffixes= "_QCimpedance, _QClineNoise, _QCcounts, _QCresponseAccuracy, _QCresponseTime, _QCrestAlpha".split(', ')

app.layout= html.Div(
    children= [
        html.H3('EEG Quality Checking Tool'),
        html.Hr(),
        'Provide values for filtering:',
        html.Br(),
        html.Br(),

        dbc.Row([
            # date filter
            dbc.Col(
                html.Div([
                    dcc.Input(id='start',placeholder='yyyy/mm/dd'),
                    '--',
                    dcc.Input(id='end',placeholder='yyyy/mm/dd'),
                ])
            ),

            # site filter
            dbc.Col(html.Div(dcc.Input(id='site',placeholder='site'))),
            
            # column filter
            dbc.Col(html.Div(dcc.Dropdown(id='qcimg', className='ddown',
                options=suffixes, multi=True, placeholder='column(s)',value=['_QCresponseAccuracy','_QCresponseTime']))),

            # QC score filter
            dbc.Col(html.Div(dcc.Dropdown(id='score', className='ddown', placeholder='score',options=[1,2,3,4]))),

            # technician filter
            dbc.Col(html.Div(dcc.Input(id='tech',placeholder='technician'))),
            
            # filter button
            dbc.Col(html.Button('Filter', id='global-filter', n_clicks=0))
        ]),
        
        html.Br(),
        html.Button('Save', id='save'),
        html.Div(id='last-save'),

        html.Br(),
        html.Hr(),
        html.Div(id='table'),
        html.Br()
    ]

)



@app.callback(Output('table','children'),
    [Input('start','value'), Input('end','value'),
    Input('site','value'),
    Input('qcimg','value'),
    Input('global-filter', 'n_clicks')])
def render_table(start, end, site, qcimg, click):

    changed = [p['prop_id'] for p in callback_context.triggered][0]
    if click>0:
        if 'global-filter' not in changed:
            raise PreventUpdate


    dirs= glob(ROOTDIR+'/**/Figures', recursive=True)


    # filter by date
    if start and end:
        start=int(start.replace('/',''))
        end=int(end.replace('/',''))
        
        dirs2=[]
        for d in dirs:
            ses= int(re.search('ses-(.+?)/', d).group(1))
            if ses>=start and ses<=end:
                dirs2.append(d)
        
        dirs= dirs2.copy()


    # filter by site
    if site:
        # example d: PHOENIX/PROTECTED/PronetLA/processed/LA00012/eeg/ses-20211118/Figures
        # prepend / to facilitiate filtering
        site= '/'+site 
        dirs= [d for d in dirs if site in d]


    # filter by QC score


    # filter by technician


    headers= ['Subject','Session']+ suffixes
    rows= [dbc.Row([dbc.Col(html.Div(h)) for h in headers])]
    for i,d in enumerate(dirs):
        parts= d.split('/')
        sub= parts[-4]
        ses= parts[-2].split('-')[1]
        imgs= glob(f'{d}/*[!QC].png')
 
        print(imgs)

        # filter by columns
        if qcimg:
            imgs2=[]
            for img in imgs:
                for q in qcimg:
                    if img.endswith(f'{q}.png'):
                        imgs2.append(img)

            imgs= imgs2.copy()
 
        print(imgs)
 
        rows.append(
            dbc.Row(
                [dbc.Col(html.Div(sub)), dbc.Col(html.Div(ses))]+ \
                [dbc.Col(html.Img(src=img.replace(ROOTDIR,''))) for img in imgs]
            )
        )


    # callback for save and last-save

    
    return rows





if __name__=='__main__':
    app.run_server(debug=True, host='localhost')

