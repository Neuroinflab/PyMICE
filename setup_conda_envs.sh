# !!! IMPORTANT !!!
# run with `source`
for python_version in "2.7" "3.3" "3.4" "3.5" "3.6" "3.7" "3.8"
do
  name=pymice${python_version/./}
  conda create --name $name --no-default-packages --file requirements.txt --yes python=$python_version cython ipython
  conda activate $name
  python setup.py develop
  conda deactivate
done
