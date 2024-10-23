#!/bin/bash

export PYTHONHOME=/opt/Python-3.9.11
export PATH=/opt/uwsgi-2.0.20/:$PYTHONHOME/bin/:$PATH

# real data
export DASH_DEBUG=False
export DASH_URL_BASE_PATHNAME=/eegqc/
export EEG_QC_PHOENIX=/path/to/eegqc/
export AUTOSAVE=0
cd /opt/eeg-qc-dash/

LOG=/opt/uwsgi.log
rm -f $LOG*
uwsgi --socket /path/to/uwsgi-eeg.sock --wsgi-file uwsgi.py --master --processes 4 --chmod-socket=666 \
--buffer-size 8192 --logto=$LOG --log-maxsize=10000000 \
--logformat "%(addr) [%(ctime)] %(method) %(uri) (%(status))" &

