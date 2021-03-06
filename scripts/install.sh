#!/usr/bin/env bash

echo "Formatting Code..."
pip install autoflake yapf isort black autopep8 &> /dev/null
autopep8 --verbose --in-place --recursive --aggressive --aggressive --ignore=W605 . &> /dev/null
autoflake --in-place --recursive --remove-all-unused-imports --remove-unused-variables --ignore-init-module-imports --expand-star-imports . &> /dev/null
black . &> /dev/null
isort . &> /dev/null
echo "Building..."
rm -rf dist
pip uninstall iytdl -y
poetry build > /dev/null
iytdl_wheel=$(echo $(ls dist/*.whl) | xargs)
pip install $iytdl_wheel &> /dev/null
echo "Installed 'iytdl' Sucessfully"
