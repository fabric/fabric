version| |python| |license| |ci| |coverage|

.. |version| image:: https://img.shields.io/pypi/v/fabric
    :target: https://pypi.org/project/fabric/
    :alt: PyPI - Package Version
.. |python| image:: https://img.shields.io/pypi/pyversions/fabric
    :target: https://pypi.org/project/fabric/
    :alt: PyPI - Python Version
.. |license| image:: https://img.shields.io/pypi/l/fabric
    :target: https://github.com/fabric/fabric/blob/main/LICENSE
    :alt: PyPI - License
.. |ci| image:: https://img.shields.io/circleci/build/github/fabric/fabric/main
    :target: https://app.circleci.com/pipelines/github/fabric/fabric
    :alt: CircleCI
.. |coverage| image:: https://img.shields.io/codecov/c/gh/fabric/fabric
    :target: https://app.codecov.io/gh/fabric/fabric
    :alt: Codecov

Fabric Python Library README
========================
Fabric is a high level Python (2.7, 3.4+) library designed to execute shell
commands remotely over SSH, yielding useful Python objects in return. It builds
on top of `Invoke <https://pyinvoke.org>`_ (subprocess command execution and
command-line features) and `Paramiko <https://paramiko.org>`_ (SSH protocol
implementation), extending their APIs to complement one another and provide
additional functionality.

Installation
------------

To install Fabric, you can use pip:

.. code-block:: bash

   pip install fabric

Usage
-----
You can run Fabric tasks from the command line using the ``fab`` command. Here's the basic syntax:

.. code-block:: bash

   fab [options] <task_name>

For example, to run a task named "deploy," you can use:

.. code-block:: bash

   fab deploy

You can list available tasks using:

.. code-block:: bash

   fab -l

Roadmap
-------

The project maintainer keeps a `roadmap
<https://bitprophet.org/projects#roadmap>`_ on his website.
