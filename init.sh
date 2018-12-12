#!/bin/bash

# this script will replace all occurences of 'ADSWorker' in the current
# folder with the new name

function search_replace() {
    folder=${3:-`pwd`}
    echo "find $folder -type f -print0 | xargs -0 sed -i \"s@$1@$2@g\""
    find $folder -type f -print0 | xargs -0 sed -i "s@$1@$2@g"
}

newname=`basename $1`

read -p "Replace ADSWorker with '$newname'? [y]:" answer
if [ "${answer:-y}" == "y" ]; then
     search_replace 'ADSWorker' $newname './ADSWorker'
     search_replace 'ADSWorker' $newname './alembic'
     search_replace 'ADSWorker' $newname './*.ini'
     search_replace 'ADSWorker' $newname './*.md'
     search_replace 'ADSWorker' $newname './*.txt'
     search_replace 'ADSWorker' $newname './*.py'

     mv ADSWorker $newname
fi


if [ "`command -v virtualenv`" == "" ]; then
     read -p "You need virtualenv, can we install it for you via sudo?:" answer
     if [ "${answer:-y}" == "y" ]; then 
          echo "sudo pip install virtualenv"
          sudo pip install virtualenv
     else
          echo "Cannot continue if you do not install virtualenv, aborting"
          exit 1
     fi
fi

if [ ! -e python/bin/activate ]; then         
	virtualenv python
fi

source python/bin/activate
pip install -r requirements.txt
pip install -r dev-requirements.txt
