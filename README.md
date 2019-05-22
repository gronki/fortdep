# fortdep

Tool to generate dependencies for Modern Fortran programs.

### Version 1 and 2

Package comes with two scripts: ``fortdep`` which is the original version, kept
for compatibility, and ``fortdep2`` which is currently developed version.
Expect that in the future the latter will be renamed to ``fortdep``.

## Installation

In virtual environment:
```sh
python3 setup.py install
```

For current user:
```sh
python3 setup.py install --user
```

## Usage

```
usage: fortdep2 [-h] [--programs] [--no-includes] [--scaffold] [--verbose]
                [--output OUTPUT]
                [path [path ...]]

positional arguments:
  path

optional arguments:
  -h, --help            show this help message and exit
  --programs, -p        generate rules to link programs
  --no-includes, -i     don't generate dependencies from includes
  --scaffold, -s        generate entire makefile
  --verbose, -v         more info
  --output OUTPUT, -o OUTPUT
                        write output to file
```
