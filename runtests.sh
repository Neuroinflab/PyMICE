#!/bin/bash
conda activate pymice35
python -m unittest discover
conda deactivate
conda activate pymice36
python -m unittest discover
conda deactivate
conda activate pymice37
python -m unittest discover
conda deactivate
conda activate pymice38
python -m unittest discover
conda deactivate
