Overview
========

A module for determining Windows version

Usage
-----

```python
from infi.winver import Windows
win = Windows()
win.is_windows_2003() and win.is_x64() 
```

Checking out the code
=====================

This project uses buildout, and git to generate setup.py and __version__.py.
In order to generate these, run:

    python -S bootstrap.py -d -t
    bin/buildout -c buildout-version.cfg
    python setup.py develop

In our development environment, we use isolated python builds, by running the following instead of the last command:

    bin/buildout install development-scripts

