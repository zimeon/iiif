#!/usr/bin/env python
"""
Run validator code from command line

Wrapper around validator.py for use in local manual and continuous 
integration tests of IIIF servers. Command line options specify
parameters of the server, the API version to be tested and the 
expected compliance level. Exit code is zero for success, non-zero 
otherwise (number of failed tests).
"""

#kuldge to fix mode of validator.py
import os
os.environ['VALIDATOR_AS_MODULE']='1'
from validator import ValidationInfo,TestSuite,ImageAPI
import logging
import optparse
import sys

# Options and arguments
p = optparse.OptionParser(description='IIIF Command Line Validator',
                          usage='usage: %prog -s SERVER -p PREFIX -i IDENTIFIER [options]  (-h for help)')
p.add_option('--identifier','-i', action='store',
             help="identifier to run tests for")
p.add_option('--server','-s', action='store', default='localhost:8000',
             help="server name of IIIF service, including port if not port 80 (default localhost:8000)")
p.add_option('--prefix','-p', action='store', default='',
             help="prefix of IIIF service on server (default none)")
p.add_option('--scheme', action='store', default='http',
             help="scheme (http or https, default http)")
p.add_option('--auth','-a', action='store', default='',
             help="auth info for service (default none)")
p.add_option('--version', action='store', default='2.0',
             help="IIIF API version to test for (default 2.0)")
p.add_option('--level', action='store', type='int', default=1,
             help="compliance level to test (default 1)")
p.add_option('--verbose', '-v', action='store_true',
             help="be verbose")
p.add_option('--quiet','-q', action='store_true',
             help="minimal output only for errors")
(opt, args) = p.parse_args()

# Logging/output
level = (logging.INFO if opt.verbose else (logging.ERROR if opt.quiet else logging.WARNING))
logging.basicConfig(level=level,format='%(message)s')

# Sanity check
if (not opt.identifier):
    logging.error("No identifier specified, aborting (-h for help)") 
    exit(99)

# Run as one shot set of tests with output to stdout
info2 = ValidationInfo()
tests = TestSuite(info2).list_tests(opt.version)
n = 0
bad = 0
for testname in tests:
    if (tests[testname]['level']>opt.level):
        continue
    n += 1
    test_str = ("[%d] test %s" % (n,testname))
    try:
        info = ValidationInfo()
        testSuite = TestSuite(info) 
        result = ImageAPI(opt.identifier, opt.server, opt.prefix, opt.scheme, opt.auth, opt.version, 
                          debug=False)
        testSuite.run_test(testname, result)
        if result.exception:
            e = result.exception
            bad += 1
            logging.error("%s FAIL"%test_str)
            logging.error("  url: %s\n  got: %s\n  expected: %s\n  type: %s"%(result.urls,e.got,e.expected,e.type))
        else:
            logging.warning("%s PASS"%test_str)
            logging.info("  url: %s\n  tests: %s\n"%(result.urls,result.tests))
    except Exception as e:
        bad += 1
        logging.error("%s FAIL"%test_str)
        logging.error("  exception: %s\n"%(str(e)))
logging.warning("Done (%d tests, %d failures)" % (n,bad))
exit(bad)
