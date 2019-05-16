# fortdep

Tool to generate dependencies for Modern Fortran programs.

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
usage: fortdep2 [-h] [--programs] [--no-includes] [--verbose] [--output OUTPUT]
               [path [path ...]]

positional arguments:
  path

optional arguments:
  -h, --help            show this help message and exit
  --no-includes, -i     don't generate dependencies from includes
  --verbose, -v         more info
  --output OUTPUT, -o OUTPUT
                        write output to file
```
