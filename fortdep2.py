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
        self.includes = set()
    def assign_object_file(self, objfile):
        assert type(objfile) == SourceFile
        if self.objfile: raise Exception(u'Module {} is already assigned'
            ' to {}'.format(self.name, self.objfile))
        self.objfile = objfile
    def __repr__(self):
        return  ('program ' if type(self) == Program else '') \
            + self.name + (' /' + self.objfile.fnsrc + '/' if self.objfile else '')
    def summ(self):
        return str(self) \
            + ('\n  depends on ' + str(self.deps) if len(self.deps) > 0 else '') \
            + ('\n  includes   ' + str(self.includes) if len(self.includes) > 0 else '') \
            + ('\n  has submds ' + str(self.submodules) if hasattr(self, 'submodules') and  len(self.submodules) > 0 else '')

#------------------------------------------------------------------------------#

class Program(Unit):
    def __init__(self, name, objfile):
        Unit.__init__(self, name, objfile)

#------------------------------------------------------------------------------#

class Module(Unit):
    def __init__(self, name, objfile = None):
        Unit.__init__(self, name, objfile)
        self.submodules = set()

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

def walktree(u, bag = set()):
    harvest = set((u,))

    deps = set(filter(lambda x: x.objfile != None, u.deps))
    if hasattr(u, 'submodules'):
        deps |= set(filter(lambda x: x.objfile != None, u.submodules))

    new_bag = bag | deps | set((u,))

    for d in deps:
        if not d in bag:
            harvest |= walktree(d, new_bag)
    return harvest

#------------------------------------------------------------------------------#
#------------------------------------------------------------------------------#

# compile regexp
re_module = re.compile(r'\s*(module|program|submodule\s*\(\s*([a-z0-9_]+)\s*\))\s+([a-z0-9_]+)', re.IGNORECASE)
re_module_end = re.compile(r'^\s*end\s+(module|submodule|program)', re.IGNORECASE)
re_submodule = re.compile(r'submodule\s*\(\s*([a-z0-9_]+)\s*\)', re.IGNORECASE)
re_use = re.compile(r'^\s*use\s+([a-z0-9_]+)', re.IGNORECASE)
re_include = re.compile(r'^\s*include\s+["\'](.+)["\']', re.IGNORECASE)

#------------------------------------------------------------------------------#

verbose = False

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
                if mtype.lower() == 'program':
                    current_module = Program(mname, objfil)
                    universe.add(current_module)
                    if verbose: stderr.write(u'+ program {}\n'.format(mname))
                elif mtype.lower() == 'module':
                    # search for blank modules in the universe before adding
                    current_module = query_modules_or_new(mname)
                    current_module.assign_object_file(objfil)
                    if verbose: stderr.write(u'+ module {}\n'.format(mname))
                elif mparent != None:
                    # for submodules, first search if parent is defined
                    parent_module = query_modules_or_new(mparent)
                    # search for blank modules in the universe before adding
                    current_module = query_modules_or_new(mname)
                    current_module.assign_object_file(objfil)
                    current_module.deps.add(parent_module)
                    parent_module.submodules.add(current_module)
                    if verbose: stderr.write(u'+ module {}, submodule of {}\n'.format(mname, mparent))
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
            #     current_module.deps.add(mdep)
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
                current_module.deps.add(mdep)
                if verbose: stderr.write('* {} uses {}\n'.format(current_module, mdep))
                continue

            # attempt to match "include"
            mtch = re.match(re_include, line)
            if mtch:
                current_module.includes.add(mtch.group(1))
                if verbose: stderr.write('* {} includes {}\n'.format(current_module, mtch.group(1)))
                continue

#------------------------------------------------------------------------------#
#------------------------------------------------------------------------------#

def parse_cmdline_args():
    from sys import argv
    from argparse import ArgumentParser

    parser = ArgumentParser('fortdep2')
    parser.add_argument('--programs', '-p', action = 'store_true',
            help = 'generate rules to link programs')
    parser.add_argument('--no-includes', '-i', action = 'store_true',
            help = 'don\'t generate dependencies from includes')
    parser.add_argument('--scaffold', '-s', action = 'store_true', dest = 'whole',
            help = 'generate entire makefile')
    parser.add_argument('--verbose', '-v', action = 'store_true',
            help = 'more info')
    parser.add_argument('--encoding', '-e', type = str, default = 'utf-8',
            dest = 'encoding', help = 'specify input encoding (default: utf-8)')
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
    global universe, objfiles, verbose

    #--------------------------------------------------------------------------#

    # main program starts here: parse command line args
    args = parse_cmdline_args()

    # if no output file given, write to stdout
    output = stdout if args.output == '--' else open(args.output, 'w')

    verbose = args.verbose

    #--------------------------------------------------------------------------#

    # scan for files, either from makefile VPATH or just recursively
    if len(args.path) == 0:
        make_vpath = check_makefile_vpath()
        if make_vpath:
            stderr.write('found Makefile, using directories: {}\n'.format(", ".join(make_vpath)))
            inp = [ (folder, [ f for f in listdir(folder)       \
                    if path.isfile(path.join(folder,f)) ])      \
                    for folder in make_vpath ]
        else:
            stderr.write(u'no directories given; scanning recursively...\n')
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

            with open(filepath, 'r', encoding = args.encoding) as f:
                obj = SourceFile(fn)
                objfiles.add(obj)
                parse_source(f, obj)

    #--------------------------------------------------------------------------#

    allprograms = set(filter(lambda x: type(x) == Program and x.objfile != None, universe))

    #--------------------------------------------------------------------------#

    if args.whole:
        output.write('# generated by fortdep\n\n')
        output.write('prefix = /usr/local\nFC = f95\nFFLAGS ?= -g -O2\n')
        output.write('programs = ' + ' '.join([x.objfile.fnexe for x in allprograms]) + '\n')
        output.write('\nall: $(programs)\n\n')

    #--------------------------------------------------------------------------#
    # model is complete, now we can generate the products

    for u in universe:
        if u.objfile == None:
            stderr.write('warning: module {} was not found in any file\n'.format(u))
            continue
        deps_fixed = set(x.objfile.fnobj for x in u.deps if x.objfile != None)
        if (not args.no_includes) or args.whole:
            deps_fixed |= u.includes
        deps_fixed -= set((u.objfile.fnobj,))
        if len(deps_fixed) == 0: continue
        output.write('{}: {}\n'.format(u.objfile.fnobj, ' '.join(deps_fixed)))

    if args.whole:
        output.write('\n%.o: %.f90\n\t$(FC) $(INCLUDE) $(FFLAGS) -c $< -o $@\n')
        output.write('%.o: %.F90\n\t$(FC) $(INCLUDE) $(CPPFLAGS) $(FFLAGS) -c $< -o $@\n')

    #--------------------------------------------------------------------------#

    if args.programs or args.whole:

        output.write('\n')

        for p in allprograms:
            d = set(x.objfile.fnobj for x in walktree(p) if x.objfile != None)
            output.write('{}: {}\n'.format(p.objfile.fnexe, ' '.join(d)))
            output.write('\t$(FC) $(INCLUDE) $(FFLAGS) $(LDFLAGS) $^ $(LDLIBS) -o $@\n')

    #--------------------------------------------------------------------------#

    if args.whole:
        output.write('\ninstall:\n\tinstall -d $(prefix)/bin\n'
            '\tinstall $(programs) $(prefix)/bin\n')
        output.write('clean:\n\t$(RM) *.o *.mod *.smod $(programs)\n')

    #--------------------------------------------------------------------------#
    if verbose:
        stderr.write('\n')
        for u in universe:
            stderr.write(u.summ() + '\n')

#------------------------------------------------------------------------------#

if __name__ == '__main__':
    main()
