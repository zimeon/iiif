#!/bin/bash
#
# Run unit and formatting tests
#
python setup.py test
pep8 --ignore=E501 *.py iiif/*.py iiif/generators/*.py tests/*.py tests/testlib/*.py
pep257 *.py iiif/*.py iiif/generators/*.py tests/*.py tests/testlib/*.py
rst-lint README
