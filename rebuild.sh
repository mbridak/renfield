#!/bin/bash
uv pip uninstall renfield
rm dist/*
uv build
uv pip install -e .

