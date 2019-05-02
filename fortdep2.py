#!/usr/bin/env python3
# coding: utf-8

from sys import stdout, stderr
from os import listdir, path, getcwd, walk
import re

#------------------------------------------------------------------------------#
#------------------------------------------------------------------------------#

re_fortext = re.compile(r'\.[fF](90|95|03|08|15|18|)$')

#------------------------------------------------------------------------------#

class SourceFile(object):
    def __init__(self, fnsrc):
        self.fnsrc = fnsrc
        self.fnobj = re.sub(re_fortext, '.o', fnsrc)
        self.fnexe = re.sub(re_fortext, '', fnsrc)
    def __repr__(self):
        return self.fnobj

#------------------------------------------------------------------------------#

# class Dependency(object):
#     def __init__(self, L, R):
#         self._L = L
#         self._R = R
#     def __repr__(self):
#         return u'<{} depends on {}>'.format(self._L, self._R)

#------------------------------------------------------------------------------#

class Unit(object):
    def __init__(self, name, objfile = None):
        self.objfile = objfile
        self.name = name.lower()
        self.deps = set()
    def add_dependency(self, u):
        self.deps.add(u)
    def assign_object_file(self, objfile):
        if self.objfile: raise Exception(u'Module {} is already assigned'
            ' to {}'.format(self.name, self.objfile))
        self.objfile = objfile
    def _reprbase(self, s):
        return u"<{} in {}>".format(s, self.objfile) if self.objfile else u"<{}>".format(s)
    def __repr__(self):
        return u"unit {}".format(self.name)

#------------------------------------------------------------------------------#

class Program(Unit):
    def __init__(self, name, objfile):
        Unit.__init__(self, name, objfile)
    def __repr__(self):
        return self._reprbase(u"program {}".format(self.name))

#------------------------------------------------------------------------------#

class Module(Unit):
    def __init__(self, name, objfile = None):
        Unit.__init__(self, name, objfile)
    def __repr__(self):
        return self._reprbase(u"module {}".format(self.name))

#------------------------------------------------------------------------------#

# class Submodule(Module):
#     def __init__(self, name, module, objfile):
#         Unit.__init__(self, name, objfile)
#         self.module = module
#         self.deps.add(module)
#     def __repr__(self):
#         return self._reprbase(u'submodule {s} of {m}'.format(s = self.name, m = self.module.name))

#------------------------------------------------------------------------------#
#------------------------------------------------------------------------------#

universe = set()
objfiles = set()

#------------------------------------------------------------------------------#

def query_modules(name):
    return next(filter(lambda u: (type(u) == Module) \
        and (u.name == name.lower()), universe), None)

#------------------------------------------------------------------------------#

def query_modules_or_new(name):
    global universe
    m = query_modules(name)
    if m == None:
        m = Module(name)
        universe.add(m)
    return m

#------------------------------------------------------------------------------#
#------------------------------------------------------------------------------#

loglevel = 0

#------------------------------------------------------------------------------#

def log(s, ll = 0):
    sr = '' if ll <= 0 else (' + ' if ll == 1 else ' -- ')
    if ll <= loglevel:
        for si in s.split('\n'): stderr.write(sr + si + '\n')

#------------------------------------------------------------------------------#
#------------------------------------------------------------------------------#

# compile regexp
re_module = re.compile(r'\s*(module|program|submodule\s*\(\s*([a-z0-9_]+)\s*\))\s+([a-z0-9_]+)', re.IGNORECASE)
re_module_end = re.compile(r'^\s*end\s+(module|submodule|program)', re.IGNORECASE)
re_submodule = re.compile(r'submodule\s*\(\s*([a-z0-9_]+)\s*\)', re.IGNORECASE)
re_use = re.compile(r'^\s*use\s+([a-z0-9_]+)', re.IGNORECASE)
re_include = re.compile(r'^\s*include\s+["\'](.+)["\']', re.IGNORECASE)

#------------------------------------------------------------------------------#

def parse_source(f, objfil):
    global universe
    # when module name is found, it will be set here
    current_module = None
    for line in f:
        # check if we are outside the module
        if current_module == None:
            # try to match the module line
            mtch = re.match(re_module, line)
            # is this a module line? (module, program, etc)
            if mtch:
                mtype, mparent, mname = mtch.groups()
                log(u'found {} {}'.format(mtype, mname), 1)
                if mtype.lower() == 'program':
                    current_module = Program(mname, objfil)
                    universe.add(current_module)
                elif mtype.lower() == 'module':
                    # search for blank modules in the universe before adding
                    current_module = query_modules_or_new(mname)
                    current_module.assign_object_file(objfil)
                elif mparent != None:
                    # for submodules, first search if parent is defined
                    parent_module = query_modules_or_new(mparent)
                    # search for blank modules in the universe before adding
                    current_module = query_modules_or_new(mname)
                    current_module.assign_object_file(objfil)
                    current_module.add_dependency(parent_module)
                else: raise Exception("wtf")
            # if not, try to match use statement. it could be anonymous program
            # mtch = re.match(re_use, line)
            # if mtch:
            #     log('anonymous program in ' + objfil.fnsrc, 2)
            #     # create program unit
            #     current_module = Program('program_' + objfil.fnexe, objfil)
            #     universe.add(current_module)
            #     # add the module as dependency
            #     mdep = query_modules_or_new(mtch.group(1))
            #     current_module.add_dependency(mdep)
        # we are inside the module
        else:
            # two things can happen: "use" statement, include or unit end

            # try to match unit end
            if re.match(re_module_end, line):
                # we are going out of the module
                current_module = None
                continue

            # attempt to match "use"
            mtch = re.match(re_use, line)
            if mtch:
                # use statement matched; add as dependency
                mdep = query_modules_or_new(mtch.group(1))
                log('{} uses {}'.format(current_module, mdep), 2)
                current_module.add_dependency(mdep)
                continue

            # attempt to match "include"
            mtch = re.match(re_include, line)
            if mtch:
                log('{} includes {}'.format(current_module, mtch.group(1)), 2)
                continue

#------------------------------------------------------------------------------#
#------------------------------------------------------------------------------#

def parse_cmdline_args():
    from sys import argv
    from argparse import ArgumentParser

    parser = ArgumentParser('fortdep')
    parser.add_argument('--verbose', '-v', action = 'store_true',
            help = 'be verbose')
    parser.add_argument('--output', '-o',
            type = str, default = '--',
            help = 'write output to file')
    parser.add_argument('path', nargs='*')

    return parser.parse_args(argv[1:])

#------------------------------------------------------------------------------#

def check_makefile_vpath():
    from subprocess import check_output
    mkoutp = check_output([
        'make',
        '--eval=print_vpath:\n\t@echo $(VPATH)',
        'print_vpath',
    ]).decode().replace('\n','')
    return re.split(r'[:\s]', mkoutp) if mkoutp else None

#------------------------------------------------------------------------------#
#------------------------------------------------------------------------------#

def main():
    global universe, objfiles, loglevel

    #--------------------------------------------------------------------------#

    # main program starts here: parse command line args
    args = parse_cmdline_args()

    # set the global verbose flag
    loglevel = 2 if args.verbose else 0

    # if no output file given, write to stdout
    output = stdout if args.output == '--' else open(args.output, 'w')

    #--------------------------------------------------------------------------#

    # scan for files, either from makefile VPATH or just recursively
    if len(args.path) == 0:
        make_vpath = check_makefile_vpath()
        if make_vpath:
            log('found Makefile, using directories: {}'.format(", ".join(make_vpath)))
            inp = [ (folder, [ f for f in listdir(folder)       \
                    if path.isfile(path.join(folder,f)) ])      \
                    for folder in make_vpath ]
        else:
            log(u'no directories given; scanning recursively...')
            cwd = getcwd()
            inp = [ (path.relpath(fd,cwd),fl) for fd,lf,fl in walk(cwd) ]
    else:
        inp = [ (folder, [ f for f in listdir(folder)       \
                if path.isfile(path.join(folder,f)) ])      \
                for arg in args.path for folder in arg.split(':')  ]

    #--------------------------------------------------------------------------#

    # scanning files complete, now analyze filenames and parse each foratran source
    for reldir, filelist in inp:
        for fn in filelist:
            if re.search(re_fortext, fn) == None: continue

            # relative directory + filename
            filepath = path.join(reldir,fn)

            with open(filepath,'r') as f:
                obj = SourceFile(fn)
                objfiles.add(obj)
                parse_source(f, obj)

    #--------------------------------------------------------------------------#

    nonblank = lambda S: filter(lambda x: x.objfile != None, S)

    # model is complete, now we can generate the products
    for u in nonblank(universe):
        deps_fixed = set(map(lambda x: x.objfile, nonblank(u.deps))) - set([u.objfile])
        if len(deps_fixed) == 0: continue
        output.write('{}: {}\n'.format(u.objfile, ' '.join([str(d) for d in deps_fixed])))

    #--------------------------------------------------------------------------#

    output.write('\n')

    for u in filter(lambda x: type(x) == Program, nonblank(universe)):
        deps = set(nonblank(u.deps)) | set([ u ])
        output.write('{}: {}\n'.format(u.objfile.fnexe, ' '.join([str(d.objfile) for d in deps])))
        output.write('\t$(FC) $(INCLUDE) $(FFLAGS) $(LDFLAGS) $< $(LDLIBS) -o $@\n\n')

#------------------------------------------------------------------------------#

if __name__ == '__main__':
    main()
