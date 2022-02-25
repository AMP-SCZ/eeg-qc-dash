#!/usr/bin/env python

import base64, io
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
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
print(dirs)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True,
                title='EEG Qc Tool')
log= logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app.layout= html.Div(
    children= [
        html.H1("Hello world"), html.Br()]+ [html.H5(d) for d in dirs]
)

if __name__=='__main__':
    app.run_server(debug=True, host='localhost')

