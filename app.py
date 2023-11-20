#!/usr/bin/env python

import base64, io
import dash
from dash import dcc, html, dash_table, Dash, callback_context, MATCH, ALL
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from os.path import isfile, isdir, abspath, join as pjoin, dirname, splitext, basename
from os import makedirs, getenv, remove, listdir, stat

import re, pickle
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
from glob import glob
import json
from time import time

from subprocess import check_call

from flask import Flask
server=Flask(__name__)

SCRIPTDIR=dirname(abspath(__file__))

# initial list of Figures
ROOTDIR= getenv("EEG_QC_PHOENIX")
URL_PREFIX= getenv("DASH_URL_BASE_PATHNAME",'')
if not ROOTDIR:
    print('Define env var EEG_QC_PHOENIX and try again')
    exit(1)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',dbc.themes.BOOTSTRAP,'styles.css']
app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True, title='EEG QC', assets_folder=ROOTDIR, assets_url_path="/",server=server)
log= logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

ALT_IMG=pjoin(URL_PREFIX,'blank.png')

with open('subject-id-gen/sites.json') as f:
    sites= json.load(f)

sites2=[]
for s in sites:
    sites2.append({'label':s['id']+' | '+s['name'], 'value':s['id']})
sites=sites2.copy()

score_options=[
    {'label':'-9 | Unchecked','value':-9},
    {'label':'-8 | Ignore','value':-8},
    {'label':'-7 | Under Review','value':-7},
    {'label':'1 | Fail','value':1},
    {'label':'2 | Some Usable','value':2},
    {'label':'3 | Pass','value':3},
    {'label':'4 | Excellent','value':4}
]



app.layout= html.Div(
    children= [
        html.Details([html.Summary('Collapse/Expand Introduction'),
        html.Br(),
        dbc.Row([
            dbc.Col(html.Img(src='https://avatars.githubusercontent.com/u/75388309?s=400&u=0d32212fdb2b3bf3854ed6624ce9f011ca6de29c&v=4', id='ampscz'),width=2),
            dbc.Col([
                dbc.Row(dcc.Markdown("""
### EEG Quality Checking Tool
Developed by Tashrif Billah, Sylvain Bouix, Spero Nicholas, Daniel Mathalon, and Gregory Light

https://github.com/AMP-SCZ/eeg-qc-dash
[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.6326486.svg)]
(https://doi.org/10.5281/zenodo.6326486)
            """)),
                dbc.Row([
                    dbc.Col(dcc.Markdown("""
* Provide value in the box(es) and click `FILTER`
* Click `SAVE` to save your QC scores
* Enter date as `yyyy/mm/dd`
                """),width='auto'),
                    dbc.Col(dcc.Markdown("""
* Example of `site`: LA, PA, ME
* Score -9 indicates not yet checked
* Refresh browser to reset all filters
                """),width='auto')
                ])
            ])
        ])], open=True),
        html.Br(),


        dbc.Navbar(
            html.Details([html.Summary('Collapse/Expand Averages'),
            html.Br(),
            html.Div(id='avg-table')
            ]),
            sticky='top',
            color='white'
        ),
        
        html.Br(),

        dbc.Row([
            # date filter
            # show one month of images as default
            dbc.Col([
                dcc.Input(id='start',placeholder='yyyy/mm/dd',debounce=True),
                html.Br(),
                'Earliest'
            ], width='auto'),

            dbc.Col('←—→', style={'margin-top':'10px'}, width='auto'),

            dbc.Col([
                dcc.Input(id='end',placeholder='yyyy/mm/dd',debounce=True),
                html.Br(),
                'Latest'
            ], width='auto'),


            # site filter
            dbc.Col(html.Div(dcc.Dropdown(id='site',placeholder='site',
                options=sites,
                value='')),
                width=2
            ),

            # password for site
            dbc.Col(html.Div(dcc.Input(id='passwd',placeholder='password',
                type='password',
                debounce=True)),
                width=1
            ),

            # technician filter
            dbc.Col(html.Div(dcc.Input(id='tech',placeholder='technician',debounce=True)),
                width=1
            ),

            # row order
            dbc.Col(html.Div([dcc.Dropdown(id='sort-order', className='ddown',
                options=['Latest first','Earliest first','Alphabetical'],
                value='Latest first'),
                'Sort order'
                ]),
                width=2
            ),

            # QC score filter
            dbc.Col(html.Div(dcc.Dropdown(id='score', className='ddown', placeholder='score',
                options=score_options)),
                width=1
            )
        ]),

        dbc.Row([
            # column filter
            dbc.Col(html.Div(dcc.Dropdown(id='qcimg', className='ddown',
                # options=list(suffixes.keys()),
                # value=[s for s,d in suffixes.items() if d],
                multi=True)),
                width=8
            ),

            # filter button
            dbc.Col(html.Button('Filter', id='global-filter', n_clicks=0))
            
        ]),

        dbc.Row(dcc.ConfirmDialog(id='verify', message='Invalid password for the site, try again')),
        
        html.Br(),
        dcc.Loading(html.Div(id='loading'),type='cube'),
        html.Br(),


        # html.Br(),
        # html.Br(),

        html.Div(id='table'),
        html.Br(),

        dcc.Store(id='properties'),
        # 30 seconds interval for autosave
        dcc.Interval(id='interval',interval=30000),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),

        dbc.Navbar([html.Button('Save', id='save', n_clicks=0),
            html.Div(id='last-saved'),
            html.Div(id='last-saved-auto')],
            fixed='bottom',
            color='white'
        )


    ]

)


props_file= pjoin(ROOTDIR,'.scores.pkl')
_passwd=pd.read_csv('.passwd')
_passwd.set_index('site',inplace=True)


# verify password
@app.callback(Output('verify','displayed'),
       [Input('site','value'),
       Input('passwd','value')])
def verify_passwd(site,passwd):

    if site and passwd:
        if passwd==_passwd.loc['dpacc','passwd']:
            pass
        elif passwd==_passwd.loc[site,'passwd']:
            pass
        else:
            # return f'Invalid password for site {site}, try again'
            return True

    elif not site and passwd:
        if passwd==_passwd.loc['dpacc','passwd']:
            pass
        else:
            # return f'Invalid password for site {site}, try again'
            return True

    else:
        raise PreventUpdate
        

    return False


# set default dates only at initial callback
@app.callback([Output('start','value'),
    Output('end','value'),
    Output('qcimg', 'options'),
    Output('qcimg', 'value')],
    Input('global-filter', 'n_clicks'))
def set_dates(click):

    if not click:
        start=(datetime.now()-timedelta(days=30)).strftime("%Y/%m/%d")
        end=datetime.now().strftime("%Y/%m/%d")
        
        # qcimg dropdown menu
        df= pd.read_csv(pjoin(ROOTDIR,'eeg_qc_images.csv'),on_bad_lines='skip',engine='python')
        options=df['img'].values
        value=df[df['default']==1]['img'].values
        
        # return start,end,options,value
        return '','',options,value
    
    raise PreventUpdate


@app.callback([Output('table','children'),
    Output('properties','data'),
    Output('avg-table','children'),
    Output('loading','children')],
    [Input('start','value'), Input('end','value'),
    Input('site','value'),
    Input('qcimg','value'),
    Input('score','value'),
    Input('tech','value'),
    Input('sort-order','value'),
    Input('global-filter', 'n_clicks'),
    Input('passwd','value')])
def render_table(start, end, site, qcimg, score, tech, order, click, passwd):
    
    changed = [p['prop_id'] for p in callback_context.triggered][0]
    if not ('global-filter' in changed and qcimg and passwd):
        raise PreventUpdate

    # verify password
    if passwd==_passwd.loc['dpacc','passwd']:
        pass
    elif passwd==_passwd.loc[site,'passwd']:
        pass
    else:
        raise PreventUpdate


    print('executing render_table')
    # strict glob pattern to avoid https://github.com/AMP-SCZ/eeg-qc-dash/issues/17
    dirs= glob(pjoin(ROOTDIR,'*/PHOENIX/PROTECTED/*/processed/*/eeg/*/Figures'))
    dirs_all= dirs.copy()
    keys=[]
    for d in dirs:
        if order=='Alphabetical':
            # sort dirs by sub_ses
            keys.append('_'.join(d.split('/')[-4:-1]))
            # example key: LA00012_eeg_ses-20211118
        else:
            # sort dirs by ses
            keys.append(d.split('/')[-2])
            # example key: ses-20211118

    dirs=[dirs[i] for i in np.argsort(keys)]
    if order=='Latest first':
        # reverse chronological sort
        dirs=dirs[::-1]
    

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


    # filter by technician
    if tech:

        dirs2=[]
        for d in dirs:
            ses= re.search('ses-(.+?)/', d).group(1)
            # one try-except deals with
            # run_sheet absence and eeg_tech code absence
            try:
                run_sheet_dir= dirname(dirname(d.replace('processed','raw')))
                sheets= glob(run_sheet_dir+ '/*.Run_sheet_eeg_?.csv')

                eeg_tech=''
                for r in sheets:
                    print('reading', basename(r))
                    run_sheet_df= pd.read_csv(r, on_bad_lines='skip', engine='python')
                    
                    if run_sheet_df.shape[0]>1:
                        # ProNET
                        for _,row in run_sheet_df.iterrows():
                            if row['field_name']=='chreeg_interview_date':
                                tmp_date=row['field_value'].replace('-','')
                            elif row['field_name']=='chreeg_primaryperson':
                                tmp_tech=row['field_value']
                        if ses==tmp_date:
                            eeg_tech=tmp_tech
                            break

                    else:
                        # PRESCIENT
                        # convert date to YMD
                        tmp_date=datetime.strptime(run_sheet_df.loc[0,'interview_date'],
                            '%m/%d/%Y').strftime('%Y%m%d')
                        if ses==tmp_date:
                            eeg_tech= run_sheet_df.loc[0,'chreeg_primaryperson']
                            break
                
                # print(eeg_tech)
                if tech.lower() == eeg_tech.lower():
                    dirs2.append(d)
            except:
                pass
                print(f'no/problematic: {run_sheet_dir}/*.Run_sheet_eeg_?.csv\n')

        dirs= dirs2.copy()


    if not isfile(props_file):
        # initialize scores
        props={}
    else:
        # load scores
        with open(props_file,'rb') as f:
            props= pickle.load(f)

    
    qcimg2={}
    for group in qcimg:
        for q in group.split('|'):
            qcimg2[q]=''
    qcimg=list(qcimg2.keys())

    headers= ['Index','Subject','Session','QC Score']+ qcimg
    head= [html.Tr([html.Th(h) for h in headers])]
    body=[]
    i=1
    for d in dirs:
        
        parts= d.split('/')
        sub= parts[-4]
        ses= parts[-2].split('-')[1]
        sub_ses= f'{sub}_{ses}'
       
        # initialize scores 
        if f'{sub}_{ses}' not in props:
            # score
            props[sub_ses]=-9
            # comment
            props[sub_ses+'-1']=''

        # do not show averages in main table
        # this check is placed here to allow
        # initialization of all scores in the above block
        if 'avg' in d:
            continue


        imgs= glob(f'{d}/*[!QC].png')
        # filter by columns
        imgs2=[]
        for q in qcimg:
            found=0
            for img in imgs:
                if img.endswith(f'{q}.png'):
                    imgs2.append(img)
                    found=1
                    break

            # render empty column for nonexistent images
            if not found:
                imgs2.append(ALT_IMG)

        imgs= imgs2.copy()
 
        # print(imgs)
        
        # filter by QC score
        # although this filter is similar to by date and by site
        # it is placed inside the for loop to take advantage of sub_ses
        if score is not None and props[f'{sub}_{ses}']!=score:
            continue

        # example run sheet:
        # PHOENIX/PROTECTED/PronetWU/processed/WU01590/eeg/ses-20220921/Figures/WU01590_20220921_runSheet.txt
        body.append(
            html.Tr(
                [html.Td(i), html.Td(sub), html.Td([
                    html.A(ses,
                        href=d.replace(ROOTDIR,URL_PREFIX)+f'/{sub}_{ses}_runSheet.txt',
                        target='_blank'),
                    html.Br(),
                    html.Br(),
                    html.A('PDF',
                        href=d.replace(ROOTDIR,URL_PREFIX)+f'/{sub}_{ses}_runSheet.pdf',
                        target='_blank')
                ])]+ \
                [html.Td([
                    dcc.Dropdown(value=props[sub_ses],
                        id= {'sub_ses':sub_ses},
                        options= score_options),
                    dcc.Textarea(value=props[sub_ses+'-1'],
                        id= {'sub_ses-1':sub_ses},
                        placeholder='comment',
                        rows=30,cols=20)
                    ])]+ \
                [html.Td(
                    html.A(
                        html.Img(src=img.replace(ROOTDIR,URL_PREFIX),
                            width='100%',height='auto'
                        ),
                        href=img.replace(ROOTDIR,URL_PREFIX),
                        target='_blank'
                    )
                ) for img in imgs]
            )
        )
        
        i+=1
 

    table=dbc.Table([html.Thead(head),html.Tbody(body)],
        bordered=True,
        hover=True)


    # populate avg-table
    # reset dirs
    dirs= dirs_all.copy()
    # we need only these rows, so filter now to preserve order
    subjects=['GRANavg']
    if site:
        subjects.append(f'{site}avg')

    dirs2=[]
    for s in subjects:
        for d in dirs:
            if s in d:
                dirs2.append(d)
                break
    
    dirs= dirs2.copy()
    

    # sticky-top table
    headers= ['Index','Subject','Session','QC Score']+ qcimg
    head= [html.Tr([html.Th(h) for h in headers])]
    body=[]
    i=1
    for d in dirs:
        parts= d.split('/')
        sub= parts[-4]
        ses= parts[-2].split('-')[1]
        sub_ses= f'{sub}_{ses}'
        imgs= glob(f'{d}/*[!QC].png')
                
        # filter by columns
        imgs2=[]
        for q in qcimg:
            found=0
            for img in imgs:
                if img.endswith(f'{q}.png'):
                    imgs2.append(img)
                    found=1
                    break

            # render empty column for nonexistent images
            if not found:
                imgs2.append(ALT_IMG)

        imgs= imgs2.copy()
        
        # print(imgs)

        body.append(
            html.Tr(
                [html.Td(i), html.Td(sub), html.Td(ses)]+ \
                [html.Td([
                    dcc.Dropdown(
                        value=props[sub_ses],
                        id= {'sub_ses':sub_ses},
                        options= score_options),
                    dcc.Textarea(
                        value=props[sub_ses+'-1'],
                        id= {'sub_ses-1':sub_ses},
                        placeholder='comment',
                        rows=30,cols=20)
                    ])]+ \
                [html.Td(
                    html.A(
                        html.Img(src=img.replace(ROOTDIR,URL_PREFIX),
                            width='100%',height='auto'
                        ),
                        href=img.replace(ROOTDIR,URL_PREFIX),
                        target='_blank'
                    )
                ) for img in imgs]
            )
        )

        i+=1


    avg_table=dbc.Table([html.Thead(head),html.Tbody(body)],
        bordered=True,
        hover=True)

    # I cannot think of a reason why saving scores at each click of Filter is useful!
    # Because of how app.py has evolved to the current state,
    # here we save the same scores that we loaded up there.
    # with open(props_file,'wb') as f:
    #     pickle.dump(props,f)

    return table,props,avg_table,True


@app.callback(Output('last-saved','children'),
    [Input('save','n_clicks'),
    Input({'sub_ses':ALL},'value'),
    Input({'sub_ses-1':ALL},'value'),
    Input({'sub_ses':ALL},'id'),
    Input('properties','data'),
    Input('passwd','value')])
def save_data(click,scores,comments,ids,props,passwd):

    changed = [p['prop_id'] for p in callback_context.triggered][0]
    if not ('save' in changed and props):
        raise PreventUpdate


    return _save_data(ids,scores,comments,props,passwd)


@app.callback(Output('last-saved-auto','children'),
    [Input('interval','n_intervals'),
    Input({'sub_ses':ALL},'value'),
    Input({'sub_ses-1':ALL},'value'),
    Input({'sub_ses':ALL},'id'),
    Input('properties','data'),
    Input('passwd','value')])
def auto_save_data(interval,scores,comments,ids,props,passwd):
    
    if interval and props:
        return _save_data(ids,scores,comments,props,passwd)
    
    raise PreventUpdate
    

def _save_data(ids,scores,comments,props,passwd):

    print('executing save_data')
    
    # update changed scores
    for n,s,c in zip(ids,scores,comments):
        sub_ses= n['sub_ses']
        props[sub_ses]=s
        props[sub_ses+'-1']=c

    # print(props)

    # only let DPACC save scores
    if passwd==_passwd.loc['dpacc','passwd']:
        with open(props_file,'wb') as f:
            pickle.dump(props,f)

        return 'Last saved on '+ datetime.now().ctime()
    else:
        return('Only DPACC users can save scores!')


if __name__=='__main__':
    # debug=None allows control via DASH_DEBUG variable
    app.run_server(debug=None, host='localhost')

