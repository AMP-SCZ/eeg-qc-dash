#!/usr/bin/env python

import base64, io
import dash
from dash import dcc, html, dash_table, Dash, callback_context, MATCH, ALL
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from os.path import isfile, isdir, abspath, join as pjoin, dirname, splitext, basename
from os import makedirs, getenv, remove, listdir

import re, pickle
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
        dbc.Row([
            dbc.Col(html.Img(src='https://avatars.githubusercontent.com/u/75388309?s=400&u=0d32212fdb2b3bf3854ed6624ce9f011ca6de29c&v=4', id='ampscz'),width=2),
            dbc.Col(dcc.Markdown("""
### EEG Quality Checking Tool
Developed by Tashrif Billah, Sylvain Bouix, Spero Nicholas, Daniel Mathalon, and Gregory Light

https://github.com/AMP-SCZ/eeg-qc-dash
[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.6326486.svg)]
(https://doi.org/10.5281/zenodo.6326486)

* Provide value in the box(es) and click `FILTER`
* Click `SAVE` to save your QC scores
* Enter date as `yyyy/mm/dd`
* Example of `site`: LA, PA, Avg
* Score 0 indicates not yet checked
            """)),
        ]),
        html.Hr(),
        html.Br(),

        dbc.Row([
            # date filter
            dbc.Col(
                html.Div([
                    dcc.Input(id='start',placeholder='yyyy/mm/dd',debounce=True),
                    '--',
                    dcc.Input(id='end',placeholder='yyyy/mm/dd',debounce=True),
                ]),
                width='auto'
            ),

            # column filter
            dbc.Col(html.Div(dcc.Dropdown(id='qcimg', className='ddown',
                options=suffixes, multi=True, placeholder='column(s)',
                value=['_QCresponseAccuracy','_QCresponseTime'])),
                width=3
            ),

            # site filter
            dbc.Col(html.Div(dcc.Input(id='site',placeholder='site',debounce=True)),
                width='auto'
            ),

            # QC score filter
            dbc.Col(html.Div(dcc.Dropdown(id='score', className='ddown', placeholder='score',
                options=[0,1,2,3,4]))
            ),

            # technician filter
            dbc.Col(html.Div(dcc.Input(id='tech',placeholder='technician',debounce=True))),
            
        ]),
        
        dcc.Loading(html.Div(id='loading'),type='cube'),
        html.Br(),
        
        dbc.Row([
            # filter button
            dbc.Col(html.Button('Filter', id='global-filter', n_clicks=0)),
            dbc.Col([html.Button('Save', id='save', n_clicks=0), html.Div(id='last-saved')]),
        ]),
        html.Br(),
        html.Br(),

        html.Div(id='table'),
        html.Br(),
        
        dcc.Store(id='properties')

    ]

)


props_file= '.scores.pkl'


@app.callback([Output('table','children'),
    Output('properties','data'),
    Output('loading','children')],
    [Input('start','value'), Input('end','value'),
    Input('site','value'),
    Input('qcimg','value'),
    Input('score','value'),
    Input('global-filter', 'n_clicks')])
def render_table(start, end, site, qcimg, score, click):
    
    changed = [p['prop_id'] for p in callback_context.triggered][0]
    # trigger initial callback but condition future callbacks
    if changed=='.':
        pass
    elif (start or end or site or qcimg or score) and ('global-filter' not in changed):
        raise PreventUpdate

    
    print('executing render_table')
    
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
        # site= '/'+site
        dirs= [d for d in dirs if site in d]


    if not isfile(props_file):
        # initialize scores
        props={}
    else:
        # load scores
        with open(props_file,'rb') as f:
            props= pickle.load(f)


    # TODO 
    # filter by technician


    headers= ['Index','Subject','Session','QC Score']+ qcimg
    head= [html.Tr([html.Th(h) for h in headers])]
    body=[]
    i=1
    for d in dirs:
        parts= d.split('/')
        sub= parts[-4]
        ses= parts[-2].split('-')[1]
        imgs= glob(f'{d}/*[!QC].png')
       
        # initialize scores 
        if not isfile(props_file):
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
        
        # filter by QC score
        # although this filter is similar to by date and by site
        # it is placed inside the for loop to take advantage of sub_ses
        if score is not None and props[f'{sub}_{ses}']!=score:
            continue
 
        body.append(
            html.Tr(
                [html.Td(i), html.Td(sub), html.Td(ses)]+ \
                [html.Td(dcc.Dropdown(value=props[f'{sub}_{ses}'],
                    id= {'sub_ses':f'{sub}_{ses}'}, options=[0,1,2,3,4]))]+ \
                [html.Td(html.Img(src=img.replace(ROOTDIR,''))) for img in imgs]
            )
        )
        
        i+=1
 

    with open(props_file,'wb') as f:
        pickle.dump(props,f)

    table=dbc.Table([html.Thead(head),html.Tbody(body)],
        bordered=True,
        hover=True)

    return table,props,True



@app.callback(Output('last-saved','children'),
    [Input('save','n_clicks'),
    Input({'sub_ses':ALL},'value'),
    Input({'sub_ses':ALL},'id'),
    Input('properties','data')])
def save_data(click,scores,ids,props):

    changed = [p['prop_id'] for p in callback_context.triggered][0]
    if 'save' not in changed:
        raise PreventUpdate

    print('executing save_data')

    # load all scores 
    with open(props_file,'rb') as f:
        props_all= pickle.load(f)

    # update changed scores
    for n,s in zip(ids,scores):
        props[n['sub_ses']]=s

    # print(props)

    # save all scores
    with open(props_file,'wb') as f:
        pickle.dump(props,f)
  

    return 'Last saved on '+ datetime.now().ctime()


if __name__=='__main__':
    app.run_server(debug=True, host='localhost')

