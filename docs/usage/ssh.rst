============
SSH behavior
============

Fabric currently makes use of the `Paramiko
<http://www.lag.net/paramiko/docs/>`_ SSH library for managing all connections,
meaning that there are occasionally spots where it is limited by Paramiko's
capabilities. Below are areas of note where Fabric will exhibit behavior that
isn't consistent with, or as flexible as, the behavior of the ``ssh``
command-line program.


Unknown hosts
=============

SSH's host key tracking mechanism keeps tabs on all the hosts you attempt to
connect to, and maintains a ``~/.ssh/known_hosts`` file with mappings between
identifiers (IP address, sometimes with a hostname as well) and SSH keys. (For
details on how this works, please see the `OpenSSH documentation
<http://openssh.org/manual.html>`_.)

Paramiko is capable of loading up your ``known_hosts`` file, and will then
compare any host it connects to, with that mapping. Settings are available to
determine what happens when an unknown host (a host whose username or IP is not
found in ``known_hosts``) is seen:

* **Reject**: the host key is rejected and the connection is not made. This
  results in a Python exception, which will terminate your Fabric session with a
  message that the host is unknown.
* **Add**: the new host key is added to the in-memory list of known hosts, the
  connection is made, and things continue normally. Note that this does **not**
  modify your on-disk ``known_hosts`` file!
* **Ask**: not yet implemented at the Fabric level, this is a Paramiko option
  which would result in the user being prompted about the unknown key and
  whether to accept it.

Whether to reject or add hosts, as above, is controlled in Fabric via the
:ref:`env.reject_unknown_hosts <reject-unknown-hosts>` option, which is False
by default for convenience's sake. We feel this is a valid tradeoff between
convenience and security; anyone who feels otherwise can easily modify their
fabfiles at module level to set ``env.reject_unknown_hosts = True``.


Known hosts with changed keys
=============================

The point of SSH's key/fingerprint tracking is so that man-in-the-middle
attacks can be detected: if an attacker redirects your SSH traffic to a
computer under his control, and pretends to be your original destination
server, the host keys will not match. Thus, the default behavior of SSH -- and
Paramiko -- is to immediately abort the connection when a host previously
recorded in ``known_hosts`` suddenly starts sending us a different host key.

In some edge cases such as some EC2 deployments, you may want to ignore this
potential problem. Paramiko, at the time of writing, doesn't give us control
over this exact behavior, but we can sidestep it by simply skipping the loading
of ``known_hosts`` -- if the host list being compared to is empty, then there's
no problem. Set :ref:`env.disable_known_hosts <disable-known-hosts>` to True
when you want this behavior; it is False by default, in order to preserve
default SSH behavior.

.. warning::
    Enabling :ref:`env.disable_known_hosts <disable-known-hosts>` will leave
    you wide open to man-in-the-middle attacks! Please use with caution.
