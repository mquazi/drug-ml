#!/bin/bash

if [ ! -d "models" ]; then
  echo "Downloading models..."
  curl -L $MODELS_URL --output models.tar.gz
  echo "Extracting models..."
  tar -xf models.tar.gz
  rm models.tar.gz
fi

if [ ! -d "ddt" ]; then
  echo "Downloading ddt..."
  curl -L $DDT_URL --output ddt.tar.gz
  echo "Extracting ddt..."
  tar -xf ddt.tar.gz
  rm ddt.tar.gz
fi