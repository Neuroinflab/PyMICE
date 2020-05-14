# !!! IMPORTANT !!!
# run with `source`
for python_version in "3.5" "3.6" "3.7" "3.8"
do
  name=pymice${python_version/./}
  conda create --name $name --no-default-packages --file requirements.txt --yes python=$python_version cython ipython
  conda activate $name
  pip install minimock
  python setup.py develop
  conda deactivate
done

