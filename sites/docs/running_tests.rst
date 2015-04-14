======================
Running Fabric's Tests
======================

Fabric is maintained with 100% passing tests. Where possible, patches should
include tests covering the changes, making things far easier to verify & merge.

When developing on Fabric, it works best to establish a `virtualenv`_ to install
the dependencies in isolation for running tests.

.. _`virtualenv`: https://virtualenv.pypa.io/en/latest/

.. _first-time-setup:

First-time Setup
================

* Fork the `repository`_ on GitHub
* Clone your new fork (e.g.
  ``git clone git@github.com:<your_username>/fabric.git``)
* ``cd fabric``
* ``virtualenv env``
* ``. env/bin/activate``
* ``pip install -r requirements.txt``
* ``python setup.py develop``

.. _`repository`: https://github.com/fabric/fabric

.. _running-tests:

Running Tests
=============

Once your virtualenv is activated (``. env/bin/activate``) & you have the latest
requirements, running tests is just::

    nosetests tests/

You should **always** run tests on ``master`` (or the release branch you're
working with) to ensure they're passing before working on your own
changes/tests.

Alternatively, if you've run ``python setup.py develop`` on your Fabric clone,
you can also run::

    fab test

This adds additional flags which enable running doctests & adds nice coloration.


Testing against multiple versions of Python
===========================================

In order to make testing against multiple versions of Python easier, the
testsuite can also be executed using tox_ (outside the virtualenv you created
above).  Tox will handle all the virtual environments for you out of the box.

To execute the whole test suite against Python 2.5 - 2.7 you can simply run::

    tox

If you just want to run the tests specified in, for instance,
``tests/test_parallel.py`` against Python 2.7 run::

    tox -e py27 -- tests/test_parallel.py

Note that tox won't install the various Python versions for you. So if you want
to test against Python 2.5 you have to have that installed prior to running
tests against it.

.. _tox: https://tox.readthedocs.org/
