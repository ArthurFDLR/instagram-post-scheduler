#!/bin/sh

APP_VERSION=`cat version.txt | tr . _`

python3 -m pip install --target ./lib requests
mkdir -p dist
(cd ./lib && zip -r ../dist/$APP_VERSION.zip .)
(cd ./src && zip -r -g ../dist/$APP_VERSION.zip ./*)
