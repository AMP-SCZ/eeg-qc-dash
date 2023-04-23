#!/usr/bin/env python

import json
import sys
from os.path import basename

def get_value(var,event):

    for d in dict1:
        if d['redcap_event_name']==event:
            try:
                return d[var]
            except KeyError:
                return ''
                
    # the subject has not reached the event yet
    return ''


network=basename(sys.argv[1])
_path=sys.argv[1]+'/PHOENIX/PROTECTED/'+sys.argv[2]
sub=sys.argv[3]
_date=sys.argv[4]
date=_date[0:4]+'-'+_date[4:6]+'-'+_date[6:8]


# provided path:
# /data/predict1/data_from_nda/Pronet/PHOENIX/PROTECTED/PronetYA/processed/YA12345/eeg/ses-20230104/Figures
# we need:
# /data/predict1/data_from_nda/Pronet/PHOENIX/PROTECTED/PronetYA/raw/YA12345/surveys/YA12345.Pronet.json

_path=_path.replace('processed','raw')
_path=_path.split('eeg/ses-')[0]
_path+=f'surveys/{sub}.{network}.json'

with open(_path) as f:
    dict1=json.load(f)
    

for e in 'baseline_arm_1,month_2_arm_1,baseline_arm_2,month_2_arm_2'.split(','):
    chreeg_interview_date=get_value('chreeg_interview_date',e)
    if chreeg_interview_date==date:
        print(e)
        break

