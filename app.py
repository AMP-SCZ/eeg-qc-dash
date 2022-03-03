#!/usr/bin/env python

import base64, io
import dash
from dash import dcc, html, dash_table, Dash, callback_context, MATCH, ALL
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from os.path import isfile, isdir, abspath, join as pjoin, dirname, splitext, basename
from os import makedirs, getenv, remove, listdir

import re
from datetime import datetime
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
        html.Div([html.Button('Save', id='save', n_clicks=0), html.Div(id='last-saved')]),
        html.Br(),
        html.Hr(),
        html.Div(id='table'),
        html.Br(),
        dcc.Store(id='properties')
    ]

)



@app.callback([Output('table','children'),
    Output('properties','data')],
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

    if not isfile('.scores.csv'):
        # initialize scores
        df= pd.DataFrame(columns=['sub','ses','score'])
        props={}
    else:
        # load scores
        df= pd.read_csv('.scores.csv')

    # filter by technician


    headers= ['Subject','Session', 'Score']+ qcimg
    rows= [dbc.Row([dbc.Col(html.Div(h)) for h in headers])]
    for i,d in enumerate(dirs):
        parts= d.split('/')
        sub= parts[-4]
        ses= parts[-2].split('-')[1]
        imgs= glob(f'{d}/*[!QC].png')
       
        # initialize scores 
        if not isfile('.scores.csv'):
            # df.loc[i]= [sub, ses, 0]
            props[f'{sub}_{ses}']=0

        # filter by columns
        if qcimg:
            imgs2=[]
            for img in imgs:
                for q in qcimg:
                    if img.endswith(f'{q}.png'):
                        imgs2.append(img)

            imgs= imgs2.copy()
 
        # print(imgs)
 
        rows.append(
            dbc.Row(
                [dbc.Col(html.Div(sub)), dbc.Col(html.Div(ses))]+ \
                # [dbc.Col(dcc.Dropdown(value=df.loc[i]['score'], id= {'sub':sub,'ses':ses}, options=[1,2,3,4]))]+ \
                [dbc.Col(dcc.Dropdown(value=props[f'{sub}_{ses}'], id= {'sub_ses':f'{sub}_{ses}'}, options=[0,1,2,3,4]))]+ \
                [dbc.Col(html.Img(src=img.replace(ROOTDIR,''))) for img in imgs]
            )
        )
 

    # callback for save and last-save

    
    return rows,props


@app.callback(Output('last-saved','children'),
    [Input('save','n_clicks'),
    Input({'sub_ses':ALL},'value'),
    Input({'sub_ses':ALL},'id'),
    Input('properties','data')])
def save_data(click,scores,ids,props):
    if click>0:
        # read all sub, ses, score dropdown
        # save them in .scores.csv
        # populate status in last-save
        pass
        
        # print(props)
 
        for n,s in zip(ids,scores):
            print(n,s)
            props[n['sub_ses']]=s

        # save props.npy
        
        # return 'Last saved on '+ datetime.now().ctime()
    
        print(props) 

    raise PreventUpdate


if __name__=='__main__':
    app.run_server(debug=True, host='localhost')

