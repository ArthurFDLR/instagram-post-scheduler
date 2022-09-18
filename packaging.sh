#!/bin/sh

APP_VERSION=`cat version.txt | tr . _`

python3 -m pip install \
    --platform manylinux2014_x86_64 \
    --target=./lib \
    --implementation cp \
    --python 3.9 \
    --only-binary=:all: --upgrade \
    -r requirements.txt
mkdir -p dist
(cd ./lib && zip -r ../dist/$APP_VERSION.zip .)
(cd ./src && zip -r -g ../dist/$APP_VERSION.zip ./*)
