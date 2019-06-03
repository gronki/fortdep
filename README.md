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
                [--encoding ENCODING] [--output OUTPUT]
                [path [path ...]]

positional arguments:
  path

optional arguments:
  -h, --help            show this help message and exit
  --programs, -p        generate rules to link programs
  --no-includes, -i     don't generate dependencies from includes
  --scaffold, -s        generate entire makefile
  --verbose, -v         more info
  --encoding ENCODING, -e ENCODING
                        specify input encoding (default: utf-8)
  --output OUTPUT, -o OUTPUT
                        write output to file
```

### Example 0

Just display the dependencies on screen:
```bash
fortdep2
```

### Example 1

Typical use is to generate dependencies and write them in a file
```bash
fortdep2 -o deps.inc
```

which is then included in Makefile:
```makefile
include deps.inc
```

### Example 2

Generate whole Makefile (it is assumed that all Fortran sources have .f90 extension):
```bash
fortdep2 -s -o Makefile
```

## Problems and bugs

### Encoding

Most contemporary Linux systems use utf-8 encoding. If you run across the error similar to below, please use ``-e`` option to specify input encoding.
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xbf in position 16: invalid start byte
```
