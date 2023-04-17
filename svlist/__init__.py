#!/usr/bin/env python3

import argparse
import pyslang
import os
import queue


def get_parser():
    parser = argparse.ArgumentParser("svlist")
    parser.add_argument("-d", type=str, help="SystemVerilog source file directores", dest="dirs", nargs="+",
                        required=True)
    parser.add_argument("-I", type=str, help="SystemVerilog include directory", dest="include", nargs="+", default=[])
    parser.add_argument("-t", "--top", type=str, help="Top module name", dest="top")
    parser.add_argument("--ext", type=str, help="SystemVerilog file extension, default is `.sv;.v`", dest="ext",
                        default=".sv;.v")
    parser.add_argument("-o", type=str, help="File list output", default="-", dest="output")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    exts = args.ext.split(";")
    # search all files
    files = []
    for d in args.dirs:
        for file in os.listdir(d):
            _, ext = os.path.splitext(file)
            if ext in exts:
                path = os.path.join(d, file)
                files.append(path)
    arg_str = " ".join(files)
    if len(args.include) > 0:
        arg_str += " -I " + " ".join(args.include)
    if args.top:
        arg_str += " --top " + args.top
    driver = pyslang.Driver()
    driver.addStandardArgs()
    driver.parseCommandLine("svlist " + arg_str)
    driver.processOptions()
    driver.parseAllSources()
    compilation = driver.createCompilation()
    source_manager = driver.sourceManager
    root = compilation.getRoot()
    top_instances = root.topInstances
    if len(top_instances) == 0:
        print("Unable to find any instances")
        exit(1)
    elif len(top_instances) > 1:
        print("More than one top instances found")
        exit(1)
    top_instance = top_instances[0]
    filenames = set()
    workset = queue.Queue()
    workset.put(top_instance)
    instances = [top_instance]
    while not workset.empty():
        inst = workset.get()

        for s in inst.body:
            if s.kind == pyslang.SymbolKind.Instance:
                instances.append(s)
                workset.put(s)

                syntax = s.syntax
                if syntax is not None:
                    source_range = syntax.sourceRange
                    start_loc = source_range.start
                    filename = source_manager.getFullPath(start_loc.buffer)
                    filenames.add(str(filename))

    res = "\n".join(filenames)
    if args.output == "-":
        print(res)
    else:
        with open(args.output, "w+") as f:
            f.write(res)


if __name__ == "__main__":
    main()
