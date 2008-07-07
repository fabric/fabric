Hacking Fabric: Modus Operandi
==============================

So you want to hack on Fabric? And there's a chance you might want to share
your changes? Then read on; this document is written specifically for you.

This document is not about where which parts are located in the code. Rather,
this document is about process and conventions.

There are essentially five things (besides python programming) you need to
know, in order to work on, and make changes to, Fabric:

1. Where to get the source code
2. Where to put your changes
3. How we prefer to structure and style code
4. How we prefer to organize SCM history
5. Where the community's at

Apart from that, don't be afraid to ask the mailing list if you are ever in
doubt or confused by any of this.


Where to get and put code
-------------------------

Assuming you want to make changes to it and have them possibly merged upstream,
then the *best* way to get started, is to get an account on [github][] and make
a fork of [the Fabric repository][gh-repo]. Although any online git repository
would technically work, it is generally advisable to use one with a good web
interface, and github is particularly preferred.

After that, you just make a local clone of your repository. You will be able to
commit and work on your local repository, and push to your own fork. Once you
think you have something interesting to share, notify the mailing list.

If the patch is really small and/or you did not want to create a forked
repository, then you can the patch files to the mailing list.


Structure and style in code
---------------------------

Whenever possible, follow [PEP-8][]. In summery:

* Keep lines under 80 characters - also in documentation.
* Indents are 4 spaces.
* Class names are CamelCased.
* all other names use lowercased underscore_separation.

Don't be afraid to fix PEP-8 inconsistencies, spelling mistakes and grammar.
It might be nit-picking, but that's alright. It helps keep the code clean.


SCM history and commit policy
-----------------------------

In general, try to split things up in sensible chunks. We don't want big
commits that changes a dozen unrelated things; CVS just called and it want its
monolithic commits back.

Following is a list of commit themes that can be used as guiding boundaries
for how to split things up, but these are not set in stone. Common sense is
important.

* PEP-8, styling, indentation, spelling and grammar.
* New features.
* Bug fixes.
* Renaming, moving and adding files, or moving existing code chunks into their
own files.
* Refactoring or clean-up of cohesive code chunks.

If you happen to mix these changes in the same file, then you can use the
interactive adding feature of Git (`git add -i`) to split up the chunks of
your changes and put them in different commits. For instance, I often correct
PEP-8 violations on sight and often while doing something else with the file,
and then break up the changes afterwards with interactive adding.

If you are certain that you will get a better history by bending or break these
rules in a given instance, then do so. A clean and sensible commit history is
more important than adhering to these rules. They are just here for guidance.

Just don't put the repository in a half-broken state.

[github]: http://github.com/
[gh-repo]: http://github.com/karmazilla/fabric/tree/master
[pep-8]: http://www.python.org/dev/peps/pep-0008/
