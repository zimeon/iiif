=====================
Updating iiif on pypi
=====================

Notes to remind @zimeon...

iiif is at <https://pypi.python.org/pypi/iiif>

Putting up a new version
------------------------

  1. Bump version number working branch in iiif/_version.py and check CHANGES.md is up to date
  2. Check all tests good (python setup.py test; ./run_validate.sh -n)
  3. Check code is up-to-date with github version
  4. Check out master and merge in working branch
  5. Check all tests good (python setup.py test; ./run_validate.sh -n)
  6. Make sure master README has correct travis-ci and coveralls icon links for master branch (?branch=master)
  7. Check branches are as expected (git branch -a)
  8. Check local build and version reported OK (python setup.py install)
  9. Check iiif_testserver.py correctly starts server and is accessible from <http://localhost:8000>
  10. If all checks out OK, tag and push the new version to github with something like:

    ```
    git tag -n1
    #...current tags
    git tag -a -m "IIIF Image API reference implementation, 2018-03-05" v1.0.6
    git push --tags

    python setup.py sdist upload
    ```

  11. Check on PyPI at <https://pypi.org/project/iiif/>
  12. Finally, back on working branch start new version number by editing `iiif/_version.py` and `CHANGES.md`

