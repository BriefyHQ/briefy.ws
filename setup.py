"""Briefy microservices helpers."""
from setuptools import find_packages
from setuptools import setup

import os

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'HISTORY.rst')) as f:
    CHANGES = f.read()

requires = [
    'briefy.common',
    'colander',
    'colanderalchemy',
    'cornice==2.2.0',
    'prettyconf',
    'pyramid==1.7.3',
    'pyramid_jwt',
    'pyramid_tm',
    'requests',
    'setuptools',
    'waitress',
    'wheel'
]

test_requirements = [
    'flake8',
    'pytest'
]

setup(
    name='briefy.ws',
    version='1.1.2',
    description='Briefy microservice helpers.',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
    ],
    author='Briefy Developers',
    author_email='developers@briefy.co',
    url='https://github.com/BriefyHQ/briefy.ws',
    keywords='microservice briefy',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['briefy', ],
    include_package_data=True,
    zip_safe=False,
    test_suite='tests',
    tests_require=test_requirements,
    install_requires=requires,
    entry_points="""""",
)
