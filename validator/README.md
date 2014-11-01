# IIIF Validator

Temporary inclusion of IIIF Image API validation code from
<https://github.com/IIIF/iiif.io/tree/master/source/api/image/validator>.
The script `validate.py` allows this to be run from the command line
for local testing. Ideally we should package this script and the 
rest of the validation code on pypi for easy installation and use
with TravisCI.

## Running the validator locally

Dependencies:

  * bottle
  * python-magic (which requires libmagic)

On a mac one can do:

```
pip install bottle python-magic
brew install libmagic
```

and then:

```
./validate.py -s localhost:8000 -p prefix -i 67352ccc-d1b0-11e1-89ae-279075081939.png --version=1.0
```

or similar to validate server with the test image. Use `./validate -h` for 
parameter details.
