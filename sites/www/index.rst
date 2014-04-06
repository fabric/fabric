Welcome to Paramiko!
====================

Paramiko is a Python (2.6+, 3.3+) implementation of the SSHv2 protocol [#]_,
providing both client and server functionality. While it leverages a Python C
extension for low level cryptography (`PyCrypto <http://pycrypto.org>`_),
Paramiko itself is a pure Python interface around SSH networking concepts.

This website covers project information for Paramiko such as the changelog,
contribution guidelines, development roadmap, news/blog, and so forth. Detailed
usage and API documentation can be found at our code documentation site,
`docs.paramiko.org <http://docs.paramiko.org>`_.

.. toctree::
    changelog
    FAQs <faq>
    installing
    contributing
    contact

.. Hide blog in hidden toctree for now (to avoid warnings.)

.. toctree::
    :hidden:

    blog


.. rubric:: Footnotes

.. [#]
    SSH is defined in RFCs
    `4251 <http://www.rfc-editor.org/rfc/rfc4251.txt>`_,
    `4252 <http://www.rfc-editor.org/rfc/rfc4252.txt>`_,
    `4253 <http://www.rfc-editor.org/rfc/rfc4253.txt>`_, and 
    `4254 <http://www.rfc-editor.org/rfc/rfc4254.txt>`_;
    the primary working implementation of the protocol is the `OpenSSH project
    <http://openssh.org>`_.  Paramiko implements a large portion of the SSH
    feature set, but there are occasional gaps.
