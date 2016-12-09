#!/bin/bash
source activate py27
python -m unittest discover
source deactivate
source activate py33
python -m unittest discover
source deactivate
source activate py34
python -m unittest discover
source deactivate
source activate py35
python -m unittest discover
source deactivate
