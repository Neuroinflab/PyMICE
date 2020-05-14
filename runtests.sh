#!/bin/bash
conda activate py35
python -m unittest discover
conda deactivate
conda activate py36
python -m unittest discover
conda deactivate
conda activate py37
python -m unittest discover
conda deactivate
conda activate py38
python -m unittest discover
conda deactivate
