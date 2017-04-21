.. highlight:: shell

Getting Started
===============

Prerequisites
-------------

* Git
* Python 3.5


Get the code
------------
Given you have privileges to access the codebase on GitHub, execute the following command on
a shell prompt::

  $ git clone git@github.com:BriefyHQ/briefy.ws.git

Local Install
--------------
Access the directory containing *briefy.ws* codebase::

  $ cd briefy.ws

Create a virtual environment::

  $ python3 -m venv .
  $ source env/bin/activate

Install package & dependencies
++++++++++++++++++++++++++++++

For development::

    (env)$ pip install -r requirements/dev.txt

For staging / production::

    (env)$ pip install -r requirements.txt


Running tests
-------------

To run all tests, first, it is needed to setup a mock server for AWS SQS::

    (env)$ make run_dockers

Run all tests::

    (env)$ make test

Check style::

    (env)$ make lint

To run just a subset of the tests::

    (env)$ py.test tests/queue


Reporting Bugs
--------------

Report bugs at https://github.com/BriefyHQ/briefy.ws/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Generating the documentation
----------------------------

Install this package and its dependencies::

    (env)$ pip install -r requirements/dev.txt

Generate the HTML documentation::

    (env)$ make docs_server

Open the your browser at http://localhost:8000
