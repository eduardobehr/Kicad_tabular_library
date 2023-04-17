# Description

Kicad Library to/from SQLite3 Database converter.

Input and output files can be (`.kicad_sym`,) and (`.db`,) and vice-versa (although not the same on both ends).

# Usage

## Positional arguments
  `source_file`    Kicad library or SQLite database
  `target_file`    SQLite database or Kicad library

## Help

For help in how to use it, type:

```sh
python ./kicad_db_converter.py  --help
```

## Example

To convert the Kicad library to a database:
```sh
python ./kicad_db_converter.py  mylib.kicad_sym  mydb.db
```

To convert a database back to the Kicad library:
```sh
python ./kicad_db_converter.py  mydb.db  mylib.kicad_sym
```