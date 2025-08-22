#!/bin/bash

if [ -z $1 ] || [ ! -d $2 ]
then
    echo """./down_eeg_pdf_rsheet.sh TOKEN /path/to/nda_root/network/
Provide REDCap token and /path/to/nda_root/network folder"""
    exit
fi

export PATH=/data/predict1/miniconda3/bin:$PATH

TOKEN=$1
# NETWORK_PHOENIX=/data/predict/data_from_nda/Pronet
NETWORK_PHOENIX=$2/PHOENIX/PROTECTED/
cd $NETWORK_PHOENIX
CURL=`which curl`

# obtain ${sub}_{ses} values   
for d in `ls -d */processed/*/eeg/*/Figures`
do
    IFS='/' read -ra parts <<< $d
    sub=${parts[2]}
    _ses=${parts[4]}
    ses=${_ses#ses-}
    # echo ${sub}_${ses}
    outfile=${d}/${sub}_${ses}_runSheet.pdf

    # there is no run sheet for GRANavg, LAavg, etc. subjects
    if [[ $sub == *avg ]]
    then
        continue 1
    fi

    
    # find arm
    # _find_eeg_event.py network_directory figures_directory subject session(date)
    arm=`/data/predict1/eeg-qc-dash/_find_eeg_event.py $2 $d $sub $ses`

    if [ -z $arm ]
    then
        echo No run sheet for $sub $ses
        continue 1
    fi


    # no need to download one run sheet twice
    if [ -f $outfile ]
    then
        continue 1
    fi

    echo Downloading $arm $outfile

    DATA="token=${TOKEN}&content=pdf&record=${sub}&event=${arm}&instrument=eeg_run_sheet&returnFormat=json"

    $CURL -H "Content-Type: application/x-www-form-urlencoded" \
          -H "Accept: application/json" \
          -X POST \
          -d $DATA \
          -o $outfile \
          https://redcap.partners.org/redcap/api/

    echo

done

