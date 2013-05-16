from distutils.core import setup

# Extract version number from resync/_version.py. Here we are very strict
# about the format of the version string as an extra sanity check.
# (thanks for comments in 
# http://stackoverflow.com/questions/458550/standard-way-to-embed-version-into-python-package )
import re
VERSIONFILE="i3f/_version.py"
verfilestr = open(VERSIONFILE, "rt").read()
match = re.search(r"^__version__ = '(\d\.\d.\d+(\.\d+)?)'", verfilestr, re.MULTILINE)
if match:
    version = match.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE))

setup(
    name='I3f',
    version='0.1.0',
    author='Simeon Warner',
    packages=['i3f'],
    scripts=[],
    url='https://github.com/zimeon/i3f',
    license='LICENSE.txt',
    description='Code to share for I3F',
    long_description=open('README.txt').read(),
)
