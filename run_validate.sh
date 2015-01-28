#!/bin/bash
#
# Designed to be run by Travis CI and so accumulates any error responses
# in $errors which is then used as the exit code. Exit code will be 
# zero for no errors.
#
# -v to be more verbose
# -d for debugging info
#
# See http://tldp.org/LDP/abs/html/arithexp.html for bash arithmetic

verbosity='--quiet'
while getopts ":v:d" opt; do
  case $opt in
    v)
      verbosity=''
      ;;
    d)
      verbosity='--verbose'
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# Set up test server
./iiif_testserver.py --quiet 2>&1 > /dev/null &

# Run validations against test server
errors=0
iiif-validate.py -s localhost:8000 -p 1.1_pil_none -i 67352ccc-d1b0-11e1-89ae-279075081939.png --version=1.1 --level 1 $verbosity
((errors+=$?))
iiif-validate.py -s localhost:8000 -p 2.0_pil_none -i 67352ccc-d1b0-11e1-89ae-279075081939.png --version=2.0 --level 1 $verbosity
((errors+=$?))

# Kill test server
kill `cat iiif_testserver.pid`

echo "$0 finished (total of $errors errors)"
exit $errors
