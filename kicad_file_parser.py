#! /bin/python3
from sexpdata import load, dump, dumps, loads, Symbol

INPUT_FILE = "test_files/read_only_inputs/Spice_power_electronics.kicad_sym"

with open(INPUT_FILE, "r") as input_file:
    model = load(input_file)
    for element in model:
        if str(element[0]) == "symbol":
            name = element[1]
            print(f"Found symbol: {name}")