|version| |python| |license| |ci| |coverage|

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

======
Fabric
======

Overview
========

Fabric is a high level Python (2.7, 3.4+) library designed to execute shell
commands remotely over SSH, yielding useful Python objects in return. It builds
on top of `Invoke <https://pyinvoke.org>`_ (subprocess command execution and
command-line features) and `Paramiko <https://paramiko.org>`_ (SSH protocol
implementation), extending their APIs to complement one another and provide
additional functionality.

Features
========

- Execute local and remote shell commands
- Streamlined file transfer operations
- Parallel execution of tasks across multiple hosts
- Prompt handling for interactive scripts
- Integration with local and remote Python environments

Installation
============

You can install Fabric using pip:

.. code-block:: bash

    pip install fabric

Quickstart
=================

Installation
------------

.. code-block:: bash

   pip install fabric

Basic Usage
-----------

.. code-block:: python

   from fabric import Connection

   c = Connection('webserver')
   result = c.run('uname -s')
   print(result.stdout)

Key Concepts
------------

- ``Connection``: Represents an SSH connection
- ``run()``: Execute commands remotely
- ``put()`/``get()``: Transfer files

Sudo Commands
-------------

.. code-block:: python

   c.sudo('apt-get update', password='mypassword')

Multiple Servers
----------------

.. code-block:: python

   from fabric import SerialGroup

   results = SerialGroup('web1', 'web2', 'web3').run('uname -s')
   for conn, result in results.items():
       print(f"{conn.host}: {result.stdout.strip()}")

Fabric CLI
----------

Create ``fabfile.py``:

.. code-block:: python

   from fabric import task

   @task
   def deploy(c):
       c.run('git pull')
       c.run('touch app.wsgi')

Run tasks:

.. code-block:: bash

   fab -H webserver deploy

For more details, see the full Fabric documentation.

Documentation
=============

For more detailed information, check out the `official Fabric documentation <http://docs.fabfile.org/>`_.

Use Cases
=========

- Automating deployment processes
- Executing maintenance tasks on remote servers
- Configuring multiple servers simultaneously
- Running database migrations
- Restarting services across multiple hosts

To find out what's new in this version of Fabric, please see `the changelog
<https://fabfile.org/changelog.html#{}>`_.

The project maintainer keeps a `roadmap
<https://bitprophet.org/projects#roadmap>`_ on his website.

Support
=======

If you encounter any issues or have questions, please file an issue on the `GitHub issue tracker <https://github.com/fabric/fabric/issues>`_.
