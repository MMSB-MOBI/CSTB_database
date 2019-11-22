set -e

function usage(){
    echo "usage : add_genome.sh -f=<path> --taxid=<int>|--taxname=<str> --id=<str> [-o=<path>]
	[OPTIONS]
	-h : print help
	-f=<path> : path to fasta genome to add in database
    -o=<path> : output directory to write files to insert (default : .)
    --taxid=<int> : ncbi taxid (you can't combine --taxid and --taxname)
    --id=<str> : genome identifiant (for example, GCF_xxxxxxx for Refseq genome)
    --motif-broker-url=<url> : motif broker listening url (defaut : http://localhost:3282)
    --taxonDB_name=<str> : taxon_db database name (default : taxon_db)
    --db_url=<url> : database url (default : http://localhost:5984)
    --taxonTree_DBname : taxon_tree database name (default : taxon_tree)
    --slurm : Use slurm (True/False) (default : False)
    --slurm_array_dir : directory with script for slurm arrays (default : /mobi/group/databases/crispr/crispr_rc01)
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
        DB_URL="http://localhost:5984/"
    fi

    if [[ ! $TREE_DB_NAME ]]; then
        TREE_DB_NAME="taxon_tree"
    fi

    if [[ ! $SLURM ]]; then
        SLURM="False"
    fi

    if [[ $SLURM && ! $SLURM_ARRAY ]]; then
        SLURM_ARRAY="/mobi/group/databases/crispr/crispr_rc01"
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
    if [[ $SLURM -ne "False" && $SLURM -ne "True" ]]; then
        echo "--slurm must be True or False"
        exit
    fi

    if [[ ! -d $OUTDIR ]]; then
        mkdir -p $OUTDIR
    fi

}


while [ "$1" != "" ]; do
    PARAM=`echo $1 | awk -F= '{print $1}'`
    VALUE=`echo $1 | awk -F= '{print $2}'`
    case $PARAM in
        -h | --help)
            usage
            exit
            ;;
        -f)
            FASTA=$VALUE
            ;;
        -o)
            OUTDIR=$VALUE
            ;;
        --taxid)
            TAXID=$VALUE
            ;;      
        --id)
            GENOME_ID=$VALUE
            ;;
        --motif-broker-url)
            MB_URL=$VALUE
            ;;  
        --taxonDB_name)
            TAXONDB_NAME=$VALUE
            ;;  
        --db_url)
            DB_URL=$VALUE
            ;;
        --taxonTree_DBname)
            TREE_DB_NAME=$VALUE
            ;;
        --slurm)
            SLURM=$VALUE
            ;;
        *)
            echo "ERROR: unknown parameter \"$PARAM\""
            usage
            exit 1
            ;;
    esac
    shift
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

#Verif arwen-dev is mount
if [[ ! $(ls /mnt/arwen-dev) ]]; then
    echo "arwen-dev is not mount"
    exit
fi

if [[ ! $(ls /mnt/arwen) ]]; then
    echo "arwen is not mount"
    exit
fi

RESDIR=$(readlink -f $(mktemp -d -p $OUTDIR))
echo RESDIR $RESDIR

echo "== Search sgRNA, indexing genome"
# TO DO : parallelize construction
mkdir -p $RESDIR/genome_pickle
mkdir -p $RESDIR/genome_index
echo Launch python $BIN/create_metafile.py -file "$FASTA" -rfg "$RESDIR" -taxid "$TAXID" -gcf "$GENOME_ID"
python $BIN/create_metafile.py -file "$FASTA" -rfg "$RESDIR" -taxid "$TAXID" -gcf "$GENOME_ID"

echo "== Add sgRNA to couchDB"
if [[ $SLURM == "False" ]]; then
    echo Launch python /home/chilpert/Dev/pyCouch/scripts/couchBuild.py --map /home/chilpert/app/motif-broker-2/data/3letter_prefixe_rules.json --data "$RESDIR/genome_pickle" --url "$DB_URL"
    python /home/chilpert/Dev/pyCouch/scripts/couchBuild.py --map /home/chilpert/app/motif-broker-2/data/3letter_prefixe_rules.json --data "$RESDIR/genome_pickle" --url "$DB_URL"
elif [[ $SLURM == "True" ]]; then
    bash $SLURM_ARRAY/buildCouchArray.sh -i $RESDIR/genome_pickle -l $SLURM_ARRAY -u $DB_URL -m $MAP -a 0 -b 10
fi

echo "== Copy index to arwen-dev"
echo Launch cp $RESDIR/genome_index/* /mnt/arwen-dev/data/databases/mobi/crispr_clean/genome_index/
cp $RESDIR/genome_index/* /mnt/arwen-dev/data/databases/mobi/crispr_clean/genome_index/

echo "== Copy pickle to arwen"
cp $RESDIR/genome_pickle/* /mnt/arwen/data/databases/mobi/crispr_clean/

echo "== Add to taxon_db"
echo Launch python $BIN/create_file_taxondb.py single -gcf "$GENOME_ID" -taxid "$TAXID" -r "$MB_URL" -dbName "$TAXONDB_NAME" -fasta "$FASTA" -outdir "$RESDIR"
python $BIN/create_file_taxondb.py single -gcf "$GENOME_ID" -taxid "$TAXID" -r "$MB_URL" -dbName "$TAXONDB_NAME" -fasta "$FASTA" -outdir "$RESDIR"

echo Launch python ~/Dev/pyCouch/scripts/couchBuild.py taxon_db --url "$DB_URL" --data $RESDIR/taxonDB_data
python /home/chilpert/Dev/pyCouch/scripts/couchBuild.py taxon_db --url "$DB_URL" --data $RESDIR/taxonDB_data

echo "== Recalculate tree"
echo Launch python $BIN/create_tree.py -url "$DB_URL" -taxonDB_name "$TAXONDB_NAME" -o "$RESDIR"
python $BIN/create_tree.py -url "$DB_URL" -taxonDB_name "$TAXONDB_NAME" -o "$RESDIR"

echo "==Insert tree"
echo Launch python ~/Dev/pyCouch/scripts/couchBuild.py $TREE_DB_NAME --url $DB_URL --data $RESDIR/treeDB_data
python /home/chilpert/Dev/pyCouch/scripts/couchBuild.py $TREE_DB_NAME --url $DB_URL --data $RESDIR/treeDB_data