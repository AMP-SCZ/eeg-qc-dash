#!/usr/bin/env python

import pandas as pd
import pickle
from os import getcwd, chdir
import sys

if len(sys.argv)>1:
    print(f'''This script inserts EEG auto QC scores in .scores.pkl file
Usage: {__file__}
No argument is needed.''')
    exit()


def count(_props):

    freq={}
    for k,v in _props.items():
        if k.endswith('-1'):
            pass
        else:
            if v in freq:
                freq[v]+=1
            else:
                freq[v]=0

    print(freq)
    print('Total',sum(freq.values()))


dir_bak=getcwd()
chdir('/data/predict1/data_from_nda/')

df=pd.read_csv('EEGqc_features/autoScore/combined-AMPSCZ-EEGautoQC-day1to1.csv')

props_file='.scores.pkl'
with open(props_file,'rb') as f:
    props= pickle.load(f)

print('Before modification count:')
count(props)

props2=props.copy()

for i,row in df.iterrows():
    key='{}_{}'.format(row['subject'],row['session'])
    if key in props:
        if props[key]==-9:
            if not pd.isna(row['score']):
                props2[key]=row['score']

print('\nAfter modification count:')
count(props2)

with open(props_file,'wb') as f:
    pickle.dump(props2,f)

chdir(dir_bak)

