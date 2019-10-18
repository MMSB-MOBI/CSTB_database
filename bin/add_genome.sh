set -e

function usage(){
    echo "usage : add_genome.sh -f=<path> --taxid=<int>|--taxname=<str> --id=<str> [-o=<path>]
	[OPTIONS]
	-h : print help
	-f=<path> : path to fasta genome to add in database
    -o=<path> : output directory to write files to insert (default : .)
    --taxid=<int> : ncbi taxid (you can't combine --taxid and --taxname)
    --taxname=<str> : taxon name you want to give (you can't combine --taxid and --taxname)
    --id=<str> : genome identifiant (for example, GCF_xxxxxxx for Refseq genome)
    --force : overwrite results if already exists
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
    if [[ ! $TAXID  && ! $TAXNAME ]]; then
        quit=1
        echo "--taxid or --taxname is mandatory. Give taxon taxid/name."
    fi

    if [[ $TAXID && $TAXNAME ]]; then
        quit=1
        echo "--taxid and --taxname are not compatible. Choose one."
    fi

    if [[ ! $GENOME_ID ]]; then
        quit=1
        echo "--id is mandatory. Give genome id."
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
        --taxname)
            TAXNAME=$VALUE
            ;;    
        --id)
            GENOME_ID=$VALUE
            ;;
        --force)
            FORCE=1
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

echo "== Search sgRNA, indexing genome"
mkdir -p $OUTDIR/genome_pickle
mkdir -p $OUTDIR/genome_index
if [[ -f $OUTDIR/genome_index/$NAME.index && $OUTDIR/genome_pickle/$NAME.p && ! $FORCE ]]; then
    echo "$NAME.index and $NAME.p already exists. Use --force to overwrite"
else
    if [[ $TAXID ]]; then 
        echo Launch python $BIN/create_metafile.py -file "$FASTA" -rfg "$OUTDIR" -taxid "$TAXID" -gcf "$GENOME_ID"
        python $BIN/create_metafile.py -file "$FASTA" -rfg "$OUTDIR" -taxid "$TAXID" -gcf "$GENOME_ID"
    elif [[ $TAXNAME ]]; then
        echo Launch python $BIN/create_metafile.py -file "$FASTA" -rfg "$OUTDIR" -taxname "$TAXNAME" -gcf "$GENOME_ID"
    fi
fi

exit

echo "== Add to taxon_db"
echo Launch python $BIN/create_file_taxon_db.py single -r 