#!/bin/bash
REV=$1
for file in dist/PyMICE-$REV*; do gpg -ab "$file"; done
for file in dist/PyMICE-$REV*.asc; do gpg --verify "$file" "${file%.asc}" ; done
for file in dist/PyMICE-$REV*.asc; do gpg -v --verify "$file" "${file%.asc}" ; done
echo "twine upload -p 'hunter2' dist/PyMICE-$REV*"
