set -e

function usage(){
    echo "usage : add_genome.sh -f <path> --taxid=<int> --id=<str>
    [OPTIONS]
    -h : print help
    [Inputs]
    -f <path> : path to fasta genome to add in database
    --taxid <int> : ncbi taxid
    --id <str> : genome identifiant (for example, GCF_xxxxxxx for Refseq genome)
    [Outputs]
    -o <path> : output directory to write files to insert (default : .)
    [Databases]
    --motif-broker-url <url> : motif broker listening url (defaut : http://localhost:3282)
    --db_url <url> : database url (default : http://localhost:1234)
    --taxonDB_name <str> : taxon_db database name (default : taxon_db)
    --taxonTree_name <str> : taxon_tree database name (default : taxon_tree)
    [Others]
    --test : test version, database url will be http://localhost:5984 and files will not be copied to arwen and arwen-dev
    "
}

function args_gestion(){
    if [[ ! $FASTA ]]; then
        quit=1
        echo "-f is mandatory. Give fasta file"
    fi
    if [[ ! $OUTDIR ]]; then
        OUTDIR=.
    fi

    if [[ ! $TAXID ]]; then
        quit=1
        echo "--taxid is mandatory."
    fi

    if [[ ! $GENOME_ID ]]; then
        quit=1
        echo "--id is mandatory. Give genome id."
    fi

    if [[ ! $MB_URL ]]; then
        MB_URL="http://localhost:3282/"
    fi

    if [[ ! $TAXONDB_NAME ]]; then
        TAXONDB_NAME="taxon_db"
    fi

    if [[ ! $DB_URL ]]; then
        DB_URL="http://localhost:1234/"
    fi

    if [[ ! $TREE_DB_NAME ]]; then
        TREE_DB_NAME="taxon_tree"
    fi

    if [[ $TEST ]]; then
        DB_URL="http://localhost:5984"
    fi

    if [[ $quit ]]; then
        usage
        exit 1
    fi
}

function args_verif(){
    if [[ ! -f $FASTA ]]; then
        echo "$FASTA doesn't exist"
        exit 1
    fi
    if [[ ! -d $OUTDIR ]]; then
        mkdir -p $OUTDIR
    fi

    #Verif arwen-dev is mount
    if [[ ! $TEST ]]; then
        if [[ ! $(ls /mnt/arwen-dev) ]]; then
            echo "arwen-dev is not mount"
            exit
        fi

        if [[ ! $(ls /mnt/arwen) ]]; then
            echo "arwen is not mount"
            exit
        fi
    fi
}

TEMP=$(getopt -o h,o:,f: -l taxid:,id:,motif-broker-url:,db_url:,taxonDB_name:,taxonTree_name:,test -- "$@")

eval set -- "$TEMP"

while true ; do 
	case "$1" in 
		-f) 
			FASTA=$2
			shift 2;; 
		-o) 
			OUTDIR=$2
			shift 2;; 
        --taxid)
            TAXID=$2
            shift 2;; 
        --id)
            GENOME_ID=$2
            shift 2;;
        --motif-broker-url)
            MB_URL=$2
            shift 2;; 
        --taxonDB_name)
            TAXONDB_NAME=$2
            shift 2;;
        --db_url)
            DB_URL=$2
            shift 2;;
        --taxonTree_name)
            TREE_DB_NAME=$2
            shift 2;;
        --test)
            TEST=1
            shift;;   
		-h) 
			usage 
			shift ;;
		--)  
			shift ; break ;; 					
	esac 
done

args_gestion
args_verif

#Search script dir
tool_dir=$(echo $0 | rev | cut -f 3- -d "/" | rev)
if [[ $tool_dir == "" ]]; then 
	tool_dir="." 
elif [[ $tool_dir == $0 ]]; then 
	tool_dir=".." 	
fi 
BIN=$tool_dir/bin

TIMESTAMP=$(date +%Y%m%d%H%M%S)
RESDIR=$OUTDIR/add_genome_$TIMESTAMP
mkdir -p $RESDIR

echo " Fasta file : $FASTA
Taxid : $TAXID
Id : $ID
Output directory : $RESDIR
Database url : $DB_URL
Taxon database name : $TAXONDB_NAME
Taxon tree database name : $TREE_DB_NAME
motif-broker end point : $MB_URL 
"
if [[ $TEST ]];then
    echo "TEST VERSION"
else 
    echo "PRODUCTION VERSION"
fi

read -p "Continue ? (y/n)" cont
while [[ $cont != "y" && $cont != "n" ]]; do
    read -p "Continue ? (y/n)" cont
done

if [[ $cont == "n" ]]; then
    exit
fi

echo "== Add to taxon_db"
echo Launch python $BIN/create_file_taxondb.py single -gcf "$GENOME_ID" -taxid "$TAXID" -r "$MB_URL" -dbName "$TAXONDB_NAME" -fasta "$FASTA" -outdir "$RESDIR"
python $BIN/create_file_taxondb.py single -gcf "$GENOME_ID" -taxid "$TAXID" -r "$MB_URL" -dbName "$TAXONDB_NAME" -fasta "$FASTA" -outdir "$RESDIR"

echo "== Search sgRNA, indexing genome"
mkdir -p $RESDIR/genome_pickle
mkdir -p $RESDIR/genome_index
echo Launch python $BIN/create_metafile.py -file "$FASTA" -rfg "$RESDIR" -taxid "$TAXID" -gcf "$GENOME_ID"
python $BIN/create_metafile.py -file "$FASTA" -rfg "$RESDIR" -taxid "$TAXID" -gcf "$GENOME_ID"

echo "== Insert sgRNA in database"
echo Launch python /home/chilpert/Dev/pyCouch/scripts/couchBuild.py --map /home/chilpert/app/motif-broker-2/data/3letter_prefixe_rules.json --data "$RESDIR/genome_pickle" --url "$DB_URL"
python /home/chilpert/Dev/pyCouch/scripts/couchBuild.py --map /home/chilpert/app/motif-broker-2/data/3letter_prefixe_rules.json --data "$RESDIR/genome_pickle" --url "$DB_URL"

if [[ ! $TEST ]];then
    echo "== Copy index to arwen-dev"
    echo Launch cp $RESDIR/genome_index/* /mnt/arwen-dev/data/databases/mobi/crispr_clean/genome_index/
    cp $RESDIR/genome_index/* /mnt/arwen-dev/data/databases/mobi/crispr_clean/genome_index/

    echo "== Copy pickle to arwen"
    echo Launch cp $RESDIR/genome_pickle/* /mnt/arwen/mobi/group/databases/crispr/crispr_rc01/pickle/
    cp $RESDIR/genome_pickle/* /mnt/arwen/mobi/group/databases/crispr/crispr_rc01/pickle/

fi 

echo "Insert taxon in database"
echo Launch python ~/Dev/pyCouch/scripts/couchBuild.py taxon_db --url "$DB_URL" --data $RESDIR/taxonDB_data
python /home/chilpert/Dev/pyCouch/scripts/couchBuild.py taxon_db --url "$DB_URL" --data $RESDIR/taxonDB_data

echo "== Recalculate tree"
echo Launch python $BIN/create_tree.py -url "$DB_URL/" -taxonDB_name "$TAXONDB_NAME" -o "$RESDIR"
python $BIN/create_tree.py -url "$DB_URL/" -taxonDB_name "$TAXONDB_NAME" -o "$RESDIR"

echo "==Insert tree in database"
echo Launch python ~/Dev/pyCouch/scripts/couchBuild.py $TREE_DB_NAME --url $DB_URL --data $RESDIR/treeDB_data
python /home/chilpert/Dev/pyCouch/scripts/couchBuild.py $TREE_DB_NAME --url $DB_URL --data $RESDIR/treeDB_data