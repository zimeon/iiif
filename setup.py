"""Setup for IIIF Image Library implementation."""
from setuptools import setup, Command
import os
# setuptools used instead of distutils.core so that
# dependencies can be handled automatically

# Extract version number from iiif/_version.py. Here we are very strict
# about the format of the version string as an extra sanity check.
# (thanks for comments in
# http://stackoverflow.com/questions/458550/standard-way-to-embed-version-into-python-package
# )
import re
VERSIONFILE = "iiif/_version.py"
verfilestr = open(VERSIONFILE, "rt").read()
match = re.search(r"^__version__ = '(\d\.\d.\d+(\.\d+)?)'",
                  verfilestr, re.MULTILINE)
if match:
    version = match.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE))


class Coverage(Command):
    """Class to allow coverage run from setup."""

    description = "run coverage"
    user_options = []

    def initialize_options(self):
        """Empty initialize_options."""
        pass

    def finalize_options(self):
        """Empty finalize_options."""
        pass

    def run(self):
        """Run coverage program."""
        os.system("coverage run --source=iiif "
                  "--omit=iiif/manipulator_netpbm.py setup.py test")
        os.system("coverage report")
        os.system("coverage html")
        print("See htmlcov/index.html for details.")

setup(
    name='iiif',
    version=version,
    author='Simeon Warner',
    author_email='simeon.warner@cornell.edu',
    packages=['iiif'],
    package_data={'iiif': ['templates/*',
                           'third_party/jquery-1.11.1.min.js',
                           'third_party/openseadragon121/*.js',
                           'third_party/openseadragon121/images/*',
                           'third_party/openseadragon100/*.js',
                           'third_party/openseadragon100/images/*',
                           'third_party/openseadragon200/*.js',
                           'third_party/openseadragon200/images/*']},
    scripts=['iiif_static.py', 'iiif_testserver.py'],
    classifiers=["Development Status :: 4 - Beta",
                 "Intended Audience :: Developers",
                 "License :: OSI Approved :: "
                 "GNU General Public License v3 (GPLv3)",
                 "Operating System :: OS Independent",
                 "Programming Language :: Python",
                 "Programming Language :: Python :: 2",
                 "Programming Language :: Python :: 2.7",
                 "Programming Language :: Python :: 3",
                 "Programming Language :: Python :: 3.4",
                 "Programming Language :: Python :: 3.5",
                 "Programming Language :: Python :: 3.6",
                 "Topic :: Internet :: WWW/HTTP",
                 "Topic :: Multimedia :: Graphics :: Graphics Conversion",
                 "Topic :: Software Development :: "
                 "Libraries :: Python Modules",
                 "Environment :: Web Environment"],
    url='https://github.com/zimeon/iiif',
    license='LICENSE.txt',
    description='IIIF Image API reference implementation',
    long_description=open('README').read(),
    install_requires=[
        "Pillow",
        "python-magic",
        "Flask",
        "ConfigArgParse>=0.13.0"
    ],
    test_suite="tests",
    tests_require=[
        "testfixtures",
        "mock"
    ],
    cmdclass={
        'coverage': Coverage,
    },
)
