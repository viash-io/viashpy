# PyViash
Various tools and utilities to interact with [viash](https://viash.io/) using python.

# Installation
To install pyviash, you can do so from the python package index [PyPI](https://pypi.org/) using `pip`.

```bash
pip install viash
```

# Running the tests
To run the tests, clone the repository and install the development requirements by running the following command from the root of the repository:

```bash
pip install .[dev] # Do not forget to quote this if you are using zsh
```

By default, PyViash can tested against different python versions (more specifically 3.7 to 3.11) using `tox`. 
These versions of python must be made available to tox (by adding them to your `PATH` environment variable), for example by installing and enabling them using `pyenv`.

When these 
```bash
tox .
```

Alternatively, if you wish to test for the python version installed on your system only, you can choose to only test `-e` parameter.
```bash
# Uses python3.7
tox -e py37
```

# License
Copyright (C) 2020 Data Intuitive

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.