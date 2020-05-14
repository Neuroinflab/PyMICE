#!/bin/bash
source activate py35
python -m unittest discover
source deactivate
source activate py36
python -m unittest discover
source deactivate
source activate py37
python -m unittest discover
source deactivate
source activate py38
python -m unittest discover
source deactivate
