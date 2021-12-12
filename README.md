# Project `seutil`

![PyPI](https://img.shields.io/pypi/v/seutil)
![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/pengyunie/seutil?include_prereleases)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/pengyunie/seutil/Python%20package)

Python utilities for SE(+ML) research.  This library stays reasonably up-to-date with latest Python 3, currently 3.8.

Mature functions:
- io: loading/dumping files with serailization support, managing files;
- bash: running Bash command;

Incubating functions:
- LoggingUtils: for logging;
- GitHubUtils: for mining GitHub, using `PyGitHub` package;
- MiscUtils: for whatever functions that may not belong to other classes;
- Stream: similar to java.utils.Stream;
- TimeUtils: for adding time constrain on an operation;
- latex.*: for writing macros and tables for latex documents;
- project.*: for batch processing of repositories;

Deprecated functions:
- BashUtils: the previous version of bash;
- IOUtils: the previous version of io;
- CliUtils: for command line argument parsing without the need to declare each argument, recommended to use jsonargparse library;
