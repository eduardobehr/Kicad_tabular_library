#! /bin/python3
from sexpdata import load, dump, dumps, loads, Symbol
import pandas as pd
from typing import Iterable
import sqlite3 as sql
from sys import argv
import argparse
from os.path import isfile
from common import Color, KicadSymbol
from math import nan, isnan

SUPPORTED_KICAD_EXTENSIONS = ('.kicad_sym',)
SUPPORTED_DB_EXTENSIONS = ('.db',)

example = f"""example:\n
To convert the Kicad library to a database:
  python {argv[0]}  mylib.kicad_sym  mydb.db

To convert a database back to the Kicad library:
  python {argv[0]}  mydb.db  mylib.kicad_sym
"""

argparser = argparse.ArgumentParser(
    prog=f'./{argv[0]}',
    description='Kicad Library to/from SQLite3 Database converter.'
        +'Input and output files can be '
        +f'{SUPPORTED_KICAD_EXTENSIONS} and {SUPPORTED_DB_EXTENSIONS}'
        +' and vice-versa (although not the same on both ends).',
    epilog=example,
    formatter_class=argparse.RawTextHelpFormatter
)



argparser.add_argument('source_file', help=f'Kicad library or SQLite database')
argparser.add_argument('target_file', help='SQLite database or Kicad library')
argparser.add_argument('-v', '--verbose', help="Describe detailed actions while processing", action='store_true')
argparser.add_argument('-y', '--yes', help="Say 'yes' to all changes prompts", action='store_true')

args = argparser.parse_args()

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
                                    new_value = str(db_symbol[field])
                                    if old_value != new_value:
                                        print(f"Property '{field}' changed for symbol '{name}'")
                                        print(Color.RED + f" -Old value: {old_value}\n" + Color.GREEN + f" +New Value: {new_value}" + Color.RESET)
                                        
                                        ans: str = 'Y'
                                        if not args.yes:
                                            ans = input(Color.YELLOW + "\n  Proceed with change?" + Color.RESET + " [Y/N]\n  ")

                                        if ans in ('Y', 'y', 's', 'S'):
                                            model[j][k][2] = new_value

                                            any_change = True
                                            print("  OK")

                        for db_field in db_symbol:
                            element_fields = [f[1] for f in element if str(f[0]) == "property"]
                            new_value = str(db_symbol[db_field])

                            if db_field not in element_fields and db_field != "Name":
                                print(f"New property '{db_field}' for symbol '{name}'")
                                if (new_value.isdigit() and isnan(float(new_value))) or new_value == "":
                                    print(f"  '{db_field}' has no value: {new_value}")
                                    continue

                                ans: str = 'Y'
                                if not args.yes:
                                    ans = input(Color.YELLOW + f"  New value is '{new_value}'. Add new property?" + Color.RESET + " [Y/N]\n  ")

                                if ans in ('Y', 'y', 's', 'S'):
                                    last_id = [f[3][1] for f in element if str(f[0]) == 'property' if str(f[3][0]) == 'id'][-1]
                                    new_id = last_id + 1
                                    new_property = [
                                        Symbol('property'),
                                        db_field,               # name
                                        str(db_symbol[db_field]),    # value # FIXME: make string instead of number
                                        [Symbol('id'), new_id],
                                        [Symbol('at'), 0, 0, 0],
                                        [Symbol('effects'),
                                            [Symbol('font'),
                                                [Symbol('size'), 1.27, 1.27]
                                            ],
                                            Symbol('hide')
                                        ],
                                    ]

                                    model[j].append(new_property)
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
