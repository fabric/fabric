Patch submission guidelines
---------------------------

* **Create a new Git branch specific to your change(s).** For example, if
  you're adding a new feature to foo the bars, do something like the
  following::

    $ git checkout master # or the latest release branch -- see below
    $ git pull
    $ git checkout -b foo-the-bars
    <hack hack hack>
    $ git push origin HEAD
    <submit pull request based on your new 'foo-the-bars' branch>

  This makes life much easier for maintainers if you have (or ever plan to
  have) additional changes in your own ``master`` branch.

    * A corollary: please **don't put multiple fixes/features in the same
      branch/pull request**! In other words, if you're hacking on new feature X
      and find a bugfix that doesn't *require* new feature X, **make a new
      distinct branch and PR** for the bugfix.

* Base **bugfixes** off the **latest release branch** (e.g. ``1.4``, ``1.5`` or
  whatever's newest) and **new features** off of **master**. If you're unsure
  which category your change falls in, just ask on IRC or the mailing list --
  it's often a judgement call.
* **Make sure documentation is updated** -- at the very least, keep docstrings
  current, and if necessary, update the ReST documentation in ``docs/``.  For
  example, new ``env.*`` settings should be added to ``docs/usage/env.rst``.
* **Add a changelog entry** at the top of ``docs/changelog.rst`` following
  existing entries' styles. Don't forget to attribute yourself if you'd like
  credit!
* **Try writing some tests** if possible -- again, following existing tests is
  often easiest, and a good way to tell whether the feature you're modifying is
  easily testable.
* **Use** ``hub pull-request`` when writing a patch for a **pre-existing Github
  Issue**. This isn't an absolute requirement, but makes the maintainers' lives
  much easier! Specifically: `install hub
  <https://github.com/defunkt/hub/#installation>`_ and then run `hub
  pull-request <https://github.com/defunkt/hub/#git-pull-request>`_ to turn the
  issue into a pull request containing your code.
