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

This project uses buildout and infi-projector, and git to generate setup.py and __version__.py.
In order to generate these, first get infi-projector:

    easy_install infi.projector

    and then run in the project directory:

        projector devenv build
