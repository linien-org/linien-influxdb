#!/bin/bash
SCRIPT=`realpath $0`
SCRIPTPATH=`dirname $SCRIPT`
cd $SCRIPTPATH/../

rm -R build
rm -R dist

python3 setup.py sdist bdist_wheel
echo 'enter pypi password'
# python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/* -u hermitdemschoenenleben
python3 -m twine upload dist/* -u hermitdemschoenenleben
