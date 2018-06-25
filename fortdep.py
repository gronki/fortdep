#!/usr/bin/env python
# coding: utf-8

from sys import stdout, stderr, argv
from os import listdir, path, getcwd, walk
from re import match, compile as re_compile, split as re_split


re_fort = re_compile(r'(.*)\.[fF](90|95|03|08|)$')
re_module = re_compile(r'^\s*(module|program|submodule\s*\(\s*([a-zA-Z0-9_]+)\s*\))\s+([a-zA-Z0-9_]+)')
re_submodule = re_compile(r'submodule\s*\(\s*([a-zA-Z0-9_]+)\s*\)')
re_use = re_compile(r'^\s*use\s+([a-zA-Z0-9_]+)')
re_vpathsep = re_compile(r'[:\s]')

modules_standard = set([
    'iso_fortran_env',
    'iso_c_binding',
    'ieee_arithmetic',
])

verbose = False

VPATH = set()
modules_obj = dict()
modules_uses = dict()

def log(s, priority = 0):
    if verbose or priority > 0:
        for s0 in s.split('\n'):
            stderr.write(" * {}\n".format(s0))

def parse_fortran_module(f):
    # when module name is found, it will be set here
    module_name = None
    # module dependencies will be listed here
    module_uses = set()
    for line in f:
        line = line.lower()
        # module definition not encountered yet
        if not module_name:
            # try to match "MODULE name" formula
            m = match(re_module,line)
            if m:
                module_type, module_parent, name = m.groups()
                if module_type == 'module':
                    module_name = "{n}".format(n = name)
                elif module_type == 'program':
                    module_name = "program {n}".format(n = name)
                elif module_parent != None:
                    module_name = "{p}.{n}".format(n = name,
                        p = module_parent)
                    module_uses.add(module_parent)
                else: raise Exception('something went wrong while ' \
                        'recognizing module type')

                log("encountered {}".format(module_name))
            # end if
        else:
            # module name found already, we are inside the module
            # trying to match "USE name" statement
            m2 = match(re_use,line)
            if m2:
                # if matched, add to dependency list
                dep = m2.group(1)
                # if this is an intrinsic Fortran module, skip
                if dep in modules_standard: continue
                log(u"  -> uses module {}".format(dep))
                # add to dependency list
                module_uses.add(dep)
            # end if
        # end if
    # end for
    return module_name, module_uses


class Dependency(object):
    def __init__(self, targets, prerequisites):
        self.prerequisites = set(prerequisites)
        self.targets = set(targets)

    def __getattr__(self,attr):
        if attr in ['R','D','P']: return self.prerequisites
        if attr in ['L','T']: return self.targets

    def __str__(self):
        return "{:16s}: {}".format(
            " ".join([modules_obj[m] for m in self.targets]),
            " ".join([modules_obj[m] for m in self.prerequisites]),
        )

def find_optimizations(D):
    optimizations = list()
    for i0 in range(len(D)):
        for i1 in range(i0+1, len(D)):
            if D[i0].L == D[i1].L:
                # remove 1, merge into 2
                optimizations.append(( 'L', i0, i1, len(D[i0].L) ))
            elif D[i0].L >= D[i1].L:
                # merge 1 into 2 (move L, merge R)
                b = len(D[i1].L) - len(D[i0].R)
                if b > 0: optimizations.append(( 'L', i0, i1, b ))
            elif D[i0].L <= D[i1].L:
                # merge 2 into 1 (move L, merge R)
                b = len(D[i0].L) - len(D[i1].R)
                if b > 0: optimizations.append(( 'L', i1, i0, b ))
            elif D[i0].R == D[i1].R:
                # merge 1 into 2 (merge L, move R)
                b = len(D[i0].R)
                if b > 0: optimizations.append(( 'R', i0, i1, b ))
            elif D[i0].R >= D[i1].R:
                # merge 1 into 2 (merge L, move R)
                b = len(D[i1].R) - len(D[i0].L)
                if b > 0: optimizations.append(( 'R', i0, i1, b ))
            elif D[i0].R <= D[i1].R:
                # merge 2 into 1 (merge L, move R)
                b = len(D[i0].R) - len(D[i1].L)
                if b > 0: optimizations.append(( 'R', i1, i0, b ))
            # end if
        # end for
    # end for
    return optimizations


def optimize_dependencies(D0, iter = 8):
    D = list(D0)
    for it in range(iter):
        opt = find_optimizations(D)
        if len(opt) == 0:
            log("cannot optimize further: " \
                "stopped after {} iterations".format(it+1), 5)
            break
        opt.sort(cmp = lambda x,y: 1 if x[3] < y[3] else (-1 if x[3] > y[3] else 0))
        optimized = set()
        to_del = list()

        for op,i0,i1,benefit in opt:
            if i0 in optimized or i1 in optimized: continue
            if op == 'L':
                if not D[i0].L >= D[i1].L: raise Exception('corrupted dependency list')
                d0 = Dependency(D[i0].L - D[i1].L, D[i0].R)
                d1 = Dependency(D[i1].L, D[i1].R | D[i0].R)
                if len(d0.L) == 0: to_del.append(i0)
            elif op == 'R':
                if not D[i0].R >= D[i1].R: raise Exception('corrupted dependency list')
                d0 = Dependency(D[i0].L, D[i0].R - D[i1].R)
                d1 = Dependency(D[i1].L | D[i0].L, D[i1].R)
                if len(d0.R) == 0: to_del.append(i0)
            else:
                raise Exception('wrong operation')
            # end if
            log("Optimized {} (benefit = {})\n{}\n{}\n      replaced with\n{}\n{}\n".format(op, benefit,
                str(D[i0]), str(D[i1]), str(d0), str(d1)))
            D[i0], D[i1] = d0, d1
            optimized.add(i0)
            optimized.add(i1)

        to_del.sort(reverse = True)
        for i in to_del:
            log("DELETING\n{}".format(str(D[i])))
            del D[i]
    # end for
    return D


def fold(s, lc = '\\', lw = 80):
    o = list()
    buf_line = u""
    buf_word = u""
    for c in s + ' ':
        if c.isspace():
            if len(buf_line) + len(buf_word) + len(lc) >= lw:
                buf_line = buf_line + " " * (lw - len(buf_line) - len(lc)) + lc
                o.append(buf_line)
                buf_line = u"    "
            buf_line += buf_word
            buf_line += c
            buf_word = u""
        # end if c.isspace()
        else:
            buf_word += c
        #end else
    # end for
    o.append(buf_line + buf_word)
    return "\n".join(o)

def parse_cmdline_args(argv):
    from argparse import ArgumentParser

    parser = ArgumentParser('fortdep')
    parser.add_argument('--objects', action = 'store_true',
            help = 'add list of all objects')
    parser.add_argument('--vpath', action = 'store_true',
            help = 'add directories to vpath')
    parser.add_argument('--verbose', '-v', action = 'store_true',
            help = 'be verbose')
    parser.add_argument('--intermediate', '-i', action = 'store_true',
            help = 'mark all objects as intermediate')
    parser.add_argument('--optimize', '-O',
            type = int, choices = [0,1,2,3], default = 0,
            help = 'optimize (shorten) code')
    parser.add_argument('--output', '-o',
            type = str, default = '--',
            help = 'write output to file')
    parser.add_argument('path', nargs='*')

    return parser.parse_args(argv[1:])

from subprocess import check_output
def check_makefile_vpath():
    o = check_output([
        'make',
        '--eval=print_vpath:\n\t@echo $(VPATH)',
        'print_vpath',
    ]).replace('\n','')
    if o != '': return re_split(re_vpathsep, o)

def main():
    # main program starts here: parse command line args
    args = parse_cmdline_args(argv)

    # set the global verbose flag
    global verbose
    verbose = args.verbose

    # if no output file given, write to stdout
    output = stdout if args.output == '--' else open(args.output,'w')

    if len(args.path) == 0:
        make_vpath = check_makefile_vpath()
        if make_vpath:
            log('found Makefile, using directories: {}'.format(", ".join(make_vpath)), 2)
            inp = [ (folder, [ f for f in listdir(folder)       \
                    if path.isfile(path.join(folder,f)) ])      \
                    for folder in make_vpath ]
        else:
            log(u'no directories given; scanning recursively...', 2)
            cwd = getcwd()
            inp = [ (path.relpath(fd,cwd),fl) for fd,lf,fl in walk(cwd) ]
    else:
        inp = [ (folder, [ f for f in listdir(folder)       \
                if path.isfile(path.join(folder,f)) ])      \
                for arg in args.path for folder in arg.split(':')  ]


    for reldir, filelist in inp:
        for fn in filelist:
            m = match(re_fort,fn)
            if m == None: continue

            # name of the object file
            objname = "{}.o".format(m.group(1))
            # relative directory + filename
            filepath = path.join(reldir,fn)
            # write to log
            log(u"{obj} -> {fil}".format(obj = objname, fil = filepath))
            # add the directory to vpath
            VPATH.add(reldir)

            with open(filepath,'r') as f:
                module_name, module_uses = parse_fortran_module(f)

                # if module not found, it is old fortran: skip
                if not module_name: continue

                if module_name in modules_obj:
                    raise Exception("duplicate module {}".format(module_name))
                modules_obj[module_name] = objname
                modules_uses[module_name] = module_uses
                # end for
            # end with
        # end for
    #end for

    broken_deps = list()
    for tgt,deps in modules_uses.items():
        for dep in deps:
            if dep not in modules_obj:
                log(u"warning: object file for module {} not found.".format(dep), 10)
                broken_deps.append((tgt,dep))
    # broken deps elements are sets, so we need to do it in a separate loop
    for tgt,dep in broken_deps:
        modules_uses[tgt].remove(dep)

    deps_sort = modules_uses.items()
    deps_sort.sort(cmp = lambda hi,lo: 1 if hi[0] > lo[0] else ( -1 if hi[0] < lo[0] else 0 ))
    dependencies = [ Dependency([tgt], deps) for tgt,deps in deps_sort if len(deps) > 0 ]

    if args.optimize > 0:
        dependencies = optimize_dependencies(dependencies, args.optimize * 3)

    if args.objects:
        output.write(fold("OBJECTS = {}\n".format(" ".join(modules_obj.values()))) + "\n")
    if args.vpath:
        output.write("VPATH = {}\n".format(":".join(VPATH)))

    for d in dependencies:
        output.write(fold(str(d)) + "\n")

    if args.intermediate:
        output.write(fold(".INTERMEDIATE: {}".format(" ".join(modules_obj.values()))) + "\n")

if __name__ == '__main__':
    main()
