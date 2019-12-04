# CSTB_database
Scripts to manage CSTB database

## Check database consistency 

...

## Replicate database
Need pyCouch module  
Use `replicate_database.py` script :
```
usage: replicate_database.py [-h] [--db <str>] [--all] --url <str>

optional arguments:
  -h, --help   show this help message and exit
  --db <str>   Replicate database(s) corresponding to this regular expression
  --all        Replicate all databases in couchDB
  --url <str>  couchDB endpoint
```
For each database, this will create a backup database with `bak` and a timestamp in name. 

#### Examples :  
For couchDB localized in `http://localhost:5984`
* Replicate all couchDB database
```
python replicate_database.py --url http://localhost:5984 --all
```
* Replicate taxon_tree database
```
python replicate_database.py --url http://localhost:5984 --db taxon_tree
```
* Replicate all crispr_rc01 databases
```
python replicate_database.py --url http://localhost:5984 --db crispr_rc01_v[0-9]+
```

## Add genome
...

