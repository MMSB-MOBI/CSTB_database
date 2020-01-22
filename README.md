# CSTB_database
Scripts to manage CSTB database.

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

## Create view

### 1. Create view document 

You can create view document from your own mapper with your regular expression or you can give depth parameters and regular expression will be created automatically. 

Example of mapper file (it's the regular expression that will be created with depth 2): 
```
{
  '^[ACGT]{3}AA[ACGT]{18}$': 'organisms1', 
  '^[ACGT]{3}AC[ACGT]{18}$': 'organisms2', 
  '^[ACGT]{3}AG[ACGT]{18}$': 'organisms3', 
  '^[ACGT]{3}AT[ACGT]{18}$': 'organisms4', 
  '^[ACGT]{3}CA[ACGT]{18}$': 'organisms5', 
  '^[ACGT]{3}CC[ACGT]{18}$': 'organisms6', 
  '^[ACGT]{3}CG[ACGT]{18}$': 'organisms7', 
  '^[ACGT]{3}CT[ACGT]{18}$': 'organisms8', 
  '^[ACGT]{3}GA[ACGT]{18}$': 'organisms9', 
  '^[ACGT]{3}GC[ACGT]{18}$': 'organisms10', 
  '^[ACGT]{3}GG[ACGT]{18}$': 'organisms11', 
  '^[ACGT]{3}GT[ACGT]{18}$': 'organisms12', 
  '^[ACGT]{3}TA[ACGT]{18}$': 'organisms13', 
  '^[ACGT]{3}TC[ACGT]{18}$': 'organisms14', 
  '^[ACGT]{3}TG[ACGT]{18}$': 'organisms15', 
  '^[ACGT]{3}TT[ACGT]{18}$': 'organisms16'}
}
```
With depth 1 it will be : 
```
{
  "^[ACGT]{3}A[ACGT]{19}$": "organisms1",
  "^[ACGT]{3}C[ACGT]{19}$": "organisms2",
  "^[ACGT]{3}G[ACGT]{19}$": "organisms3",
  "^[ACGT]{3}T[ACGT]{19}$": "organisms4"
}

```
#### Create document
```
python bin/create_view.py -d 2 -o data/view16.json
```

### 2. Put view in database

```
curl -X PUT http://couch_agent:couch@localhost:5984/my_db/_design/my_design -d @data/view16.json
```
