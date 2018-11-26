#!/bin/sh
#export JUPYTER_TOKEN='letmein'
if [ -n "$1" ]; then
    mkdir -p ./tmp
    cp -r *.ipynb *.csv *.png ./tmp/
    chmod 444 ./tmp/*
    cd ./tmp
    /usr/local/bin/jupyter-notebook  --NotebookApp.token='' \
               --ip=0.0.0.0 fio-beegfs.ipynb
else
    /usr/local/bin/jupyter-notebook fio-beegfs.ipynb
fi