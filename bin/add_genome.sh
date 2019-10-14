set -e

function usage(){
    echo 'usage : add_genome.sh -f <str>
	[OPTIONS]
	-h : print help
	-f <str> : path to fasta genome to add in database
    -o <str> : output directory to write files to insert (default : .)
    -n <str> : genome name that you want to display in tree' 
}

function args_gestion(){
    if [[ ! $FASTA ]]; then
        quit=1
        echo "-f is mandatory. Give fasta file"
    fi
    if [[ ! $OUTDIR ]]; then
        OUTDIR=.
    fi
    if [[ ! $NAME ]]; then
        quit=1
        echo "-n is mandatory. Give genome name."
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

while getopts "f:ho:n:" option; do 
    case $option in
        f)
            FASTA=$OPTARG
            ;;
        o)
            OUTDIR=$OPTARG
            ;;
        n)
            NAME=$OPTARG
            ;;
        h)
            usage
            ;;
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

echo "== Search sgRNA, indexing genome"
mkdir -p $OUTDIR/genome_pickle
mkdir -p $OUTDIR/genome_index
echo Launch python $BIN/create_metafile.py -file "$FASTA" -out "$NAME" -rfg "$OUTDIR"
python $BIN/create_metafile.py -file "$FASTA" -out "$NAME" -rfg "$OUTDIR"

echo "== Add to taxon_db"
echo Launch python $BIN/create_file_taxon_db.py single -r 