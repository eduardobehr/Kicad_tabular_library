#! /bin/python3
from sexpdata import load, dump, dumps, loads, Symbol
import pandas as pd
from typing import Iterable
import sqlite3 as sql
from sys import argv
import argparse
from common import Color, KicadSymbol

argparser = argparse.ArgumentParser(
    prog=f'./{argv[0]}',
    description='Kicad Library to SQLite3 Database converter',
    add_help=False,
)

SUPPORTED_KICAD_EXTENSIONS = ('.kicad_sym',)
SUPPORTED_DB_EXTENSIONS = ('.db',)

argparser.add_argument('source_file', help=f'Kicad library file {SUPPORTED_KICAD_EXTENSIONS}')
argparser.add_argument('target_file', help='Database file')
argparser.add_argument('-h', '--help', action='store_true')

args = argparser.parse_args()
if args.help:
    argparser.print_help()
    exit(0)

source_file: str = args.source_file
target_file:str = args.target_file

if not source_file[source_file.find('.'):] in SUPPORTED_KICAD_EXTENSIONS:
    raise ValueError(f'Input file extension not allowed. Allowed formats are: {SUPPORTED_KICAD_EXTENSIONS}')

if not target_file[target_file.find('.'):] in SUPPORTED_DB_EXTENSIONS:
    raise ValueError(f'Output file extension not allowed. Allowed formats are: {SUPPORTED_DB_EXTENSIONS}')





with open(source_file, "r") as kicad_lib_file:
    model = load(kicad_lib_file)
    df_symbols = pd.DataFrame()
    for element in model:

        if str(element[0]) == "symbol":
            name = str(element[1])

            symbol = KicadSymbol()
            symbol['Name'] = name

            for subelement in element:
                if str(subelement[0]) == "property":
                    field = str(subelement[1])
                    value = str(subelement[2])
                    symbol[field] = value

            df_symbols = pd.concat([df_symbols, pd.DataFrame.from_records([symbol])])


    # print(df_symbols['Name'])
    with sql.connect(target_file) as conn:
        df_symbols.to_sql("symbols", conn, if_exists='replace', index=False)


print("Converted: " + Color.BLUE + f"{source_file}" + Color.RESET + " => " + Color.GREEN +f"{target_file}" + Color.RESET)