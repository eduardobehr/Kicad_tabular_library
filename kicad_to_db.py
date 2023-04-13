#! /bin/python3
from sexpdata import load, dump, dumps, loads, Symbol
import pandas as pd
from typing import Iterable
import sqlite3 as sql
from sys import argv
import argparse
from os.path import isfile
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
argparser.add_argument('-v', '--verbose', action='store_true')

args = argparser.parse_args()
if args.help:
    argparser.print_help()
    exit(0)

def verbose(*a, **kwa):
    if args.verbose:
        print(*a, **kwa)

source_file: str = args.source_file
target_file:str = args.target_file

source_extension = source_file[source_file.find('.'):]
source_root = source_file[:source_file.find('.')]

target_extension = target_file[target_file.find('.'):]
target_root = target_file[:target_file.find('.')]

if not source_extension in SUPPORTED_KICAD_EXTENSIONS and not target_extension in SUPPORTED_KICAD_EXTENSIONS:
    raise ValueError(f'Either the source or target file must be a Kicad Library: {SUPPORTED_KICAD_EXTENSIONS}')

if not target_extension in SUPPORTED_DB_EXTENSIONS and not source_extension in SUPPORTED_DB_EXTENSIONS:
    raise ValueError(f'Either the source or target file must be a database file: {SUPPORTED_DB_EXTENSIONS}')




def kicad_to_db(source_file, target_file):
    if source_extension == '.kicad_sym':
        model: list
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

        if isfile(target_file):
            confirmation = input(Color.YELLOW + "\n  Override DB file?" + Color.RESET + " [Y/N]\n  ")
        else:
            confirmation = 'Y'

        if confirmation in ('Y', 'y', 's', 'S'):
            with sql.connect(target_file) as conn:
                df_symbols.to_sql("symbols", conn, if_exists='replace', index=False)
                print("Converted: " + Color.BLUE + f"{source_file}" + Color.RESET + " => " + Color.GREEN +f"{target_file}" + Color.RESET)

    else:
        raise NotImplemented()

def db_to_kicad(source_file, target_file):
    if target_extension == '.kicad_sym':
        with sql.connect(source_file) as conn:
            df_symbols = pd.read_sql("SELECT * FROM symbols", conn)
            # print(df_symbols)
            symbols_from_db = dict()
            for i, row in df_symbols.iterrows():
                symbol = KicadSymbol()
                for field, value in row.items():
                    # print(f"{symbol['Name']}.{field} = {value}")
                    if value:
                        symbol[field] = value 
                # print(symbol, end='\n\n\n')
                symbols_from_db[symbol['Name']] = symbol

            model: list
            with open(target_file, "r") as kicad_lib_file:
                model = load(kicad_lib_file)

            names_found_in_db = [s for s in symbols_from_db]
            any_change = False  # If no change has been made, no need to touch the file
            for j, element in enumerate(model):

                if str(element[0]) == "symbol":
                    name = str(element[1])

                    if name in names_found_in_db:
                        verbose(f"Matched '{name}'")
                        db_symbol = symbols_from_db[name]

                        for k, subelement in enumerate(element):
                            if str(subelement[0]) == "property":
                                field = str(subelement[1])

                                if field in db_symbol:
                                    old_value = str(subelement[2])
                                    new_value = db_symbol[field]
                                    if old_value != new_value:
                                        print(f"Property '{field}' changed for symbol '{name}'")
                                        print(Color.RED + f" -Old value: {old_value}\n" + Color.GREEN + f" +New Value: {new_value}" + Color.RESET)
                                        ans = input(Color.YELLOW + "\n  Proceed with change?" + Color.RESET + " [Y/N]\n  ")

                                        if ans in ('Y', 'y', 's', 'S'):
                                            model[j][k][2] = new_value

                                            any_change = True
                                            print("  OK")

            if any_change:
                with open(target_file, 'w') as kicad_lib_file:
                    kicad_lib_file.write(dumps(model, pretty_print=True))
                verbose(f"Changes written to '{target_file}'")
                print("Converted: " + Color.BLUE + f"{source_file}" + Color.RESET + " => " + Color.GREEN +f"{target_file}" + Color.RESET)
            else:
                print("Nothing to change!")

if source_extension in SUPPORTED_KICAD_EXTENSIONS:
    kicad_to_db(source_file, target_file)
elif source_extension in SUPPORTED_DB_EXTENSIONS:
    db_to_kicad(source_file, target_file)
