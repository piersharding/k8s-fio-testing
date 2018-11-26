#!/bin/sh

curl -sL https://deb.nodesource.com/setup_8.x | sudo bash -
sudo -H apt-get install -y nodejs
npm

sudo -H pip3 install plotly "notebook>=5.3" "ipywidgets>=7.2"
sudo -H jupyter nbextension enable --py widgetsnbextension
sudo -H pip3 uninstall -y jupyterlab && sudo -H pip3 install jupyterlab
sudo -H jupyter labextension install @jupyterlab/plotly-extension
sudo -H pip3 install jupyterlab
sudo -H jupyter labextension install @jupyterlab/plotly-extension
