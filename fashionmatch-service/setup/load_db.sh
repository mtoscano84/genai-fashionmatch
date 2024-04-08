#!/bin/bash

python3 -m venv local_test_env
source local_test_env/bin/activate
pip3 install -r requirements.txt
python3 load_catalog.py
deactivate