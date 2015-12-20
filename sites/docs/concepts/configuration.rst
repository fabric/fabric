=============
Configuration
=============

Basics
======

The heart of Fabric's configuration system (as with much of the rest of Fabric)
relies on Invoke functionality, namely `invoke.config.Config` (technically, a
lightweight subclass, `fabric.connection.Config`). For practical details on
what this means re: configuring Fabric's behavior, please see :ref:`Invoke's
configuration documentation <invoke:configuration>`.

The primary differences from that document are as follows:

* The configuration file paths sought are all named ``fabric.*`` instead of
  ``invoke.*`` - e.g. ``/etc/fabric.yml`` instead of ``/etc/invoke.yml``,
  ``~/.fabric.py`` instead of ``~/.invoke.py``, etc.
* In addition to :ref:`Invoke's own default configuration values
  <invoke:default-values>`, Fabric merges in some of its own, such as the fact
  that SSH's default port number is 22. See :ref:`default-values` for details.
* Fabric offers a framework for managing per-host and per-host-collection
  configuration details and overrides, which lives under the top-level
  ``hosts`` and ``groups`` config keys; see :ref:`host-configuration`. This
  functionality also includes loading your local SSH config files.


.. _default-values:

Default configuration values
============================

TK


.. _host-configuration:

Per-host configuration settings
===============================

TK


----

.. warning:: TODO: EXPANDME

* Fabric simply seeks for specific configuration settings in an Invoke config
  object, either one handed explicitly into its own API objects like Connection
  or Group, or a default one; describe its defaults as we do for Invoke (user,
  port etc).
* Fabric's CLI driver generates Connections and Groups for you and hands in that
  default config (initializing it with CLI options and so forth, just like
  Invoke does)

    * TODO: actually, this means that Invoke's CLI/Executor stuff needs
      further override capability which Fabric's CLI module uses? to wit:

        * additional (or different?) CLI flags like port, user, connection
          related opts
        * different file prefixes, e.g. ~/.fabric.yaml and /etc/fabric.yaml

            * should it ALSO honor invoke files? i.e. find both? What would
              users leveraging both tools expect?

        * intersect of those two, like -f finding a fabfile instead of an
          invoke task file?

* Users who have a nontrivial, non-CLI-based setup (eg celery workers or some
  such) should manage their own 'base' Config file as well as their own
  Connection/Group generation?

    * What would this look like? If I have, say, a 5 module codebase not using
      CLI tasks, where would I store my in-code config settings (or my
      initialization of a Config object which loads conf files - i.e. replacing
      what the CLI module does), and how would I be setting up explicit
      Connections and Groups?

        * E.g. write some sample Jenkins/Celery esque background worker code -
          how does this work, how does it feel?

    * Feels strongly tied to #186 - regardless of whether one has real CLI
      tasks where shared state is in a Context, or if it's non-CLI oriented and
      shared state is "only" in the Config, it is the same problem:

        * What's your code/session entry point?
        * How do you share state throughout a session?

* How should ssh_config (from paramiko) figure into this?

    * Best is probably to just bridge it with our own stuff instead of slapping
      the entire thing in some subset of our config?

        * E.g. top level ``Port`` and ``User`` override our values
        * Host configs should generate new semi-implicit host configs in the
          Fabric level (however we do that...?) when none exist elsewhere in
          the places we source from; and merge otherwise.

            * Which brings us to how we DO load hosts from config files exactly
              presumably as part of the same general config loading setup, with
              option for loading 1+ on top of the "core" one?
            * How to hook into config management DBs like Clusto, Chef Server?
            * How to handle people who want their own Ansible-like setup of a
              bunch of host, collection of host, or role config files to all
              load in? Don't necessarily expect their setup, but make it easy
              for them to use our API to load one...

        * So say a user has some random arse yaml files they load configs from;
          and they also have ~/.ssh/config; how do we merge these, which one
          wins?

            * Actual merging should almost definitely still use regular Config
              merge stuff - allow arbitrary levels to be defined in between the
              regular ones and use the same merging behavior?
            * Then all we need to do is figure out which source comes
              above/below which other sources. Probably ~/.ssh/config
              below/overridden by anything more explicitly loaded?
