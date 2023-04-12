#! /bin/python3
from sexpdata import load, dump, dumps, loads, Symbol
from typing import Iterable

INPUT_FILE = "test_files/read_only_inputs/Spice_power_electronics.kicad_sym"

def recurse(obj: Iterable, parent_depth=0, cb=print):
    depth = parent_depth + 1
    if isinstance(obj, Iterable) and not isinstance(obj, (Symbol, str)):
        # print(type(obj))
        # return
        for sub_obj in obj:
            if sub_obj is not None:
                recurse(sub_obj, depth, cb)
    else:
        cb(depth*"    ", obj)

with open(INPUT_FILE, "r") as input_file:
    model = load(input_file)
    for element in model:
        if str(element[0]) == "symbol":
            name = element[1]
            # print(f"Found symbol: {name}")
            recurse(element)
