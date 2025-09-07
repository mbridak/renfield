#!/bin/bash
pip uninstall -y renfield
rm dist/*
python3 -m build
pip install -e .

