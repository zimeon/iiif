# IIIF Validator

Temporary inclusion of IIIF Image API validation code from
<https://github.com/IIIF/image-api/tree/master/implementations/validator>.
The script `validate.py` allows validations to be run from the command 
line for local testing. Ideally we should package this script and the 
rest of the validation code on pypi for easy installation and use
with Travis CI...

This validator supports the same validations that are available on the 
[IIIF](http://iiif.io/) website at <http://iiif.io/api/image/validator/>.

## Running the validator locally

Dependencies:

  * lxml
  * bottle
  * python-magic (which requires libmagic)
  * PIL (via Pillow)

On a mac one can do:

```
brew install libmagic
pip install lxml bottle python-magic pillow
```

Then for an image served at `http://localhost:8000/prefix/image_id`
tha validator can be run with:

```
./validate.py -s localhost:8000 -p prefix -i image_id --version=2.0 -v
```
 
or similar to validate server with the test image. Use `./validate -h` for 
parameter details.

## Using `validate.sh` with Travis CI

To install dependencies for this code the following lines must 
be present in the `install:` section of `.travis.yml`:

```
install:
  ...
  - pip install Pillow
  - sudo apt-get update
  - sudo apt-get install libmagic-dev
  - pip install bottle python-magic lxml
```

and then a single validation can be added to the commands under
the `script:` section of     `.travis.yml`:

```
script:
  ...
  - ./validate.py -s localhost:8000 -p prefix -i image_id1 --version=1.1 --level 1 --quiet
```

The `validate.py` script returns 0 exit code on success, non-zero on failure,
in order to work easily with Travis CI.