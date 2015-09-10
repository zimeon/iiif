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

# Abort with exit code 0 if we have python3 because iiif_validate.py will
# not run with python3.
major_version=`/usr/bin/env python -c 'import sys; print(sys.version_info[0])'`
if test $major_version -ne 2; then
  echo "Python major version is $major_version, validator works only with python2, exiting"
  exit 0
fi

verbosity='--quiet'
test_netpbm=true
show_test_name=false
while getopts "nvd" opt; do
  case $opt in
    n)
      test_netpbm=false
      ;;
    v)
      verbosity=''
      show_test_name=true
      ;;
    d)
      verbosity='--verbose'
      show_test_name=true
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# Set up test server
if $show_test_name; then
  echo "Starting test server..."
fi
./iiif_testserver.py --quiet --manipulators=netpbm,pil 2>&1 > /dev/null &
sleep 2

# Run validations against test server
errors=0
if $show_test_name; then
  echo "Testing PIL manipulator, API version 1.1"
fi
iiif-validate.py -s localhost:8000 -p 1.1_pil -i 67352ccc-d1b0-11e1-89ae-279075081939.png --version=1.1 --level 2 $verbosity
((errors+=$?))
if $show_test_name; then
  echo "Testing PIL manipulator, API version 2.0"
fi
iiif-validate.py -s localhost:8000 -p 2.0_pil -i 67352ccc-d1b0-11e1-89ae-279075081939.png --version=2.0 --level 2 $verbosity
((errors+=$?))
if $test_netpbm; then
  if $show_test_name; then
    echo "Testing netpbm manipulator, API version 1.1"
  fi
  iiif-validate.py -s localhost:8000 -p 1.1_netpbm -i 67352ccc-d1b0-11e1-89ae-279075081939.png --version=1.1 --level 2 $verbosity
  ((errors+=$?))
  if $show_test_name; then
    echo "Testing netpbm manipulator, API version 2.0"
  fi
  iiif-validate.py -s localhost:8000 -p 2.0_netpbm -i 67352ccc-d1b0-11e1-89ae-279075081939.png --version=2.0 --level 2 $verbosity
  ((errors+=$?))
fi

# Kill test server
kill `cat iiif_testserver.pid`

if test $errors -eq 0; then
  msg="no errors"
else
  msg="$errors errors, use -v or -d for details"
fi
echo "$0 finished ($msg)"
exit $errors
