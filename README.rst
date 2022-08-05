Project ``seutil``
==================

|PyPI| |GitHub release (latest by date including pre-releases)| |GitHub
Workflow Status|

Python utilities for SE(+ML) research. This library stays reasonably
up-to-date with the latest Python 3, currently 3.8.

**Mature functions:**

* bash: running Bash command; 
* io: loading/dumping files with serialization support, managing files; 
* log: for easy setup logging;
* project: for batch processing of repositories;

**Incubating functions:**

* pbar: improve tqdm's output in emacs-shell like terminals; 
* GitHubUtils: for mining GitHub, using ``PyGitHub`` package;
* MiscUtils: for whatever functions that may not belong to other classes; 
* Stream: similar to java.utils.Stream; 
* TimeUtils: for adding time constrain on an operation; 
* latex.*: for writing macros and tables for latex documents; 

**Deprecated functions:**

* BashUtils: the previous version of bash; 
* IOUtils: the previous version of io; 
* CliUtils: for command line argument parsing without the need to declare each argument, recommended to use jsonargparse library; 
* LoggingUtils: the previous version of log;

Full documentation can be found at `readthedocs`_.

.. |PyPI| image:: https://img.shields.io/pypi/v/seutil
.. |GitHub release (latest by date including pre-releases)| image:: https://img.shields.io/github/v/release/pengyunie/seutil?include_prereleases
.. |GitHub Workflow Status| image:: https://img.shields.io/github/workflow/status/pengyunie/seutil/Python%20package
.. _readthedocs: https://seutil.readthedocs.io/en/latest/
