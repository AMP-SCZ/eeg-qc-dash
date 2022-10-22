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


    for arm in baseline_arm_1 baseline_arm_2 month_2_arm_1 month_2_arm_2
    do

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

        read -ra parts <<< `du $outfile`
        pdf_size=${parts[0]}

        # criterion for finding empty PDF run sheets
        if [[ $pdf_size == '84' ]]
        then
            # remove it so the valid arm can get downloaded
            rm $outfile
        fi
        
        echo ''

    done
    
done

