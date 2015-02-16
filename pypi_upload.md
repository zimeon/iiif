=====================
Updating iiif on pypi
=====================

Notes to remind @zimeon...

iiif is at <https://pypi.python.org/pypi/iiif>

Putting up a new version
------------------------

  0. Bump version number working branch in iiif/_version.py and check CHANGES.md is up to date
  1. Check all tests good (python setup.py test; py.test)
  2. Check code is up-to-date with github version
  3. Check out master and merge in working branch
  4. Check all tests good (python setup.py test; py.test)
  5. Make sure master README has correct travis-ci icon link for master branch
  6. Check branches are as expected (git branch -a)
  7. Check local build and version reported OK (python setup.py build; sudo python setup.py install)
  8. Check iiif-testserver.py correctly starts server and is accessible from <http://localhost:8000>
  9. If all checks out OK, tag and push the new version to github with something like:

    ```
    git tag -n1
    #...current tags
    git tag -a -m "IIIF API v2.0 and v1.1 at level 2" v0.5.1
    git push --tags

    python setup.py sdist upload
    ```

  10. Then check on PyPI at <https://pypi.python.org/pypi/iiif>
  11. Finally, back on working branch start new version number by editing `iiif/_version.py` and `CHANGES.md`

