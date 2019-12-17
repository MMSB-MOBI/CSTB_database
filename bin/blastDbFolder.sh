#!/bin/bash


function help() {
    cat <<EOF
    Build the blast database of a set of genomic fasta files
    Accumulate in a single MFASTA file all sequences from genome FASTA FILES found in SPECIFIED FOLDER.
    Call blastdb on with provede parameters 
    Usage:
    blastDbFolder.sh -i FASTA_INPUT_FOLDER -o DATABASE_TAG
    Options:
        N/A
    Where,
        FASTA_INPUT_FOLDER is the location of the genomic fasta folder
        DATABASE_TAG is the location of the file tag use to generate BLAST_DB outputs
EOF
}

command -v makeblastdb >/dev/null 2>&1 || { echo >&2 "makeblastdb command not found, Exiting"; exit 1; }

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
   	-i|--input)
    FASTA_INPUT_FOLDER="$2"
    shift # past argument
    shift # past value
    ;;
    -o|--output)
    DATABASE_TAG="$2"
    shift # past argument
    shift # past value
    ;;
    -h|--help)
    help; exit 1;
    ;;
    *)    # unknown option
      help; exit 1;
    ;;
esac
done


if [ -z "$DATABASE_TAG" ]
    then
    help 
    exit 1
fi

if [ ! -d "$FASTA_INPUT_FOLDER" ]
    then
    help 
    exit 1
fi

nFasta=$(find $FASTA_INPUT_FOLDER/ -regextype sed -regex ".*\(fna\|fa\|fasta\)$"| wc -l)
echo "$nFasta fasta files to process"
nFastaZ=$(find $FASTA_INPUT_FOLDER/ -regextype sed -regex ".*\(fna\|fa\|fasta\)\.gz$" | wc -l)
echo "$nFastaZ zipped fasta files to process"

MFASTA=$DATABASE_TAG.fasta

if [[ $nFasta -ne 0 && $nFastaZ -ne 0 ]]; then
    echo "A"
    find $FASTA_INPUT_FOLDER/ -regextype sed -regex ".*\(fna\|fa\|fasta\)$" | while read f
        do 
        cat "$f"
    done > $MFASTA

    find $FASTA_INPUT_FOLDER/ -regextype sed -regex ".*\(fna\|fa\|fasta\)\.gz$" | while read zf
        do
        gunzip -c "$zf"
    done >> $MFASTA

elif [[ $nFasta -ne 0 ]]; then
    echo "B"
    find $FASTA_INPUT_FOLDER/ -regextype sed -regex ".*\(fna\|fa\|fasta\)$" | while read f
        do 
        cat "$f"
    done > $MFASTA

elif [[ $nFastaZ -ne 0 ]]; then
    echo "C"
    find $FASTA_INPUT_FOLDER/ -regextype sed -regex ".*\(fna\|fa\|fasta\)\.gz$" | while read zf
        do
        gunzip -c "$zf"
    done > $MFASTA
fi

echo "Formatting as blast database"
makeblastdb -in $MFASTA -dbtype nucl 2>${DATABASE_TAG}_build.err > ${DATABASE_TAG}_build.log
#gzip $MFASTA