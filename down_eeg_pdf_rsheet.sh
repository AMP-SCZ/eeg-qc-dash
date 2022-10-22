#!/bin/bash

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

    # there is no run sheet for GRANavg, LAavg, etc. subjets
    if [[ $sub == *avg ]]
    then
        continue 1
    fi
    echo $outfile

    break 1

    DATA="token=${TOKEN}&content=pdf&record=${sub}&event=baseline_arm_1&instrument=eeg_run_sheet&returnFormat=json"

    $CURL -H "Content-Type: application/x-www-form-urlencoded" \
          -H "Accept: application/json" \
          -X POST \
          -d $DATA \
          -o $outfile \
          https://redcap.partners.org/redcap/api/
    
done

