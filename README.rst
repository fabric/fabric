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

Welcome to Fabric!
==================

Fabric is a high level Python (2.7, 3.4+) library designed to execute shell
commands remotely over SSH, yielding useful Python objects in return. It builds
on top of `Invoke <https://pyinvoke.org>`_ (subprocess command execution and
command-line features) and `Paramiko <https://paramiko.org>`_ (SSH protocol
implementation), extending their APIs to complement one another and provide
additional functionality.

Installation
============
Fabric requires Python 2.7 or 3.4+. 
You can install via "pip install fabric" if you have Python 2.7. 
If you have Python3, install via "pip3 install fabric" 

Common Use Cases
================ 
Fabric is built on top of Invoke and Paramiko. Paramiko handles the SSH 
protocol implementation, while Invoke provides tools for running 
subprocesses on the local machine. 
- File Transfer: Upload and download files to and from remote machines 
easily 
- Using Fabric with command line tasks 
- Running Python code blocks on a single host
- Running commands across multiple hosts 
- Running Python code blocks on multiple hosts 
- Running a single command on an individual host   

Contributing
============
We welcome any contributions! It can be:
 1. Report bugs: If you see any bugs, please let us know. 
 2. Suggestions: You can open up an issue explaining some updates 
or improvements that you would like to see if you don't want to code. 
 3. Documentation: Feel free to add some additional documentation. 

Instructions
============
 1. Fork the repository  
 2. Clone the forked repository to your local machine
 3. Create a branch for you changes
 4. Add your changes 
 5. Commit and push 
 6. Submit a pull request 

To find out what's new in this version of Fabric, please see `the changelog
<https://fabfile.org/changelog.html#{}>`_.

The project maintainer keeps a `roadmap
<https://bitprophet.org/projects#roadmap>`_ on his website.
