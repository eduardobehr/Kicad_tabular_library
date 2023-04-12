#! /bin/python3
from sexpdata import load, dump, dumps, loads, Symbol
import pandas as pd
from typing import Iterable

INPUT_FILE = "test_files/read_only_inputs/Spice_power_electronics.kicad_sym"

# def recurse(obj: Iterable, parent_depth=0, cb=print) -> None:
#     depth = parent_depth + 1
#     attributes = []
#     if isinstance(obj, Iterable) and not isinstance(obj, (Symbol, str)):
#         # print(type(obj))
#         # return
#         for sub_obj in obj:
#             if sub_obj is not None:
#                 attr = recurse(sub_obj, depth, cb)
#                 attributes.append(attr)
#     else:
#         # cb(depth*"    ", obj)
#         attributes.append(obj)
    
#     return attributes



with open(INPUT_FILE, "r") as input_file:
    model = load(input_file)
    cols = {
        "name": [], 
        "Reference": [],
        "Value": [],
        "Footprint": [],
        # "Datasheet": []
    }

    for element in model:
        row = {
            "name": None, 
            "Reference": None,
            "Value": None,
            "Footprint": None,
            # "Datasheet": None
        }

        if str(element[0]) == "symbol":
            name = element[1]
            

            for subelement in element:
                if str(subelement[0]) == "property":
                    field = str(subelement[1])
                    if field in cols:
                        value = str(subelement[2])
                        row[field] = value
                        row["name"] = name

            for field in row:
                cols[field].append(row[field])
                
    df = pd.DataFrame(cols)
    print(df)


# TODO: 
# Symbol    |   pin_numbers     |   in_bom  |   Reference   |   Value
# R         |       hide        |   no      |       U       |   