=====================
Updating iiif on pypi
=====================

  Notes to remind @zimeon...

    * main copy of code is https://github.com/zimeon/iiif
    * on PyPi iiif is at <https://pypi.org/project/iiif>

Putting up a new version
------------------------

    0. Check version number working branch in `iiif/_version.py`
    1. Check all tests good (`python setup.py test; ./run_validate.sh -n`)
    2. Check code is up-to-date with main github version
    3. Check out `main` and merge in working branch
    4. Check all tests good (`python setup.py test; ./run_validate.sh -n`)
    5. Check branches are as expected (`git branch -a`)
    6. Check local build and version reported OK (`python setup.py build; python setup.py install`)
    7. Check iiif_testserver.py correctly starts server and is accessible from <http://localhost:8000>
    8. Tag and then upload new version to pypi using Python 3.x:

      ```
      git tag -n1
      #...current tags
      git tag -a -m "IIIF Image API reference implementation, 2019-11-09" v1.0.8
      git push --tags

      pip install --upgrade setuptools wheel twine
      python setup.py sdist bdist_wheel
      ls dist
      twine upload dist/*
      ```

    9. Check on PyPI at <https://pypi.org/project/iiif>
    10. Finally, back on `develop branch start new version number by editing `iiif/_version.py` and `CHANGES.md`
