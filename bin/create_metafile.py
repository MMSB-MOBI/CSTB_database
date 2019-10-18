#!/usr/bin/env python3
"""
Create pickle and index file from a fasta file name by its taxonomy ID and GCF ID
"""

import sys
import argparse
sys.path.append("/Users/chilpert/Dev/crispr/lib/") # To replace
import word_detect
import wordIntegerIndexing as decoding
from ete3 import NCBITaxa


def args_gestion():
    """
    Take and treat arguments that user gives in command line
    """
    parser = argparse.ArgumentParser(description="Create pickleand index metafile")
    parser.add_argument("-file", metavar="<str>",
                        help="The fasta file to parse", required=True)
    parser.add_argument("-taxname", metavar="<str>",
                        help="Taxon name")
    parser.add_argument("-taxid", metavar="<str>", help="Taxonomy ID")
    parser.add_argument("-gcf", metavar="<str>", help="GCF ID")
    parser.add_argument("-rfg", metavar="<str>",
                        help="The path to the database for index and pickle file",
                        nargs="?", const="")
    parser.add_argument("-plasmid", action="store_true",
                        help="If present, indicates the genome is a plasmid")
    args = parser.parse_args()

    if not args.taxid and not args.taxname:
        print("You must give --taxid or --taxname")
        exit()

    if args.taxid and args.taxname:
        print("You must give --taxid or --taxname. Not both.")
        exit()

    return args


def name_output(taxid, gcf):
    """
    Given a taxid and a gcf, create a name with the organism name and its gcf
    """
    ncbi = NCBITaxa()
    name_org = ncbi.get_taxid_translator([int(taxid)])[int(taxid)]
    name_org = name_org.replace("'", '')
    name_org =  name_org.replace("/", '_')
    return name_org + " " + gcf


if __name__ == '__main__':
    PARAM = args_gestion()
    PATH_P = PARAM.rfg + "/genome_pickle/" if PARAM.rfg else ""
    if PARAM.taxid :
        NAME = name_output(PARAM.taxid, PARAM.gcf)
    elif PARAM.taxname:
        NAME = PARAM.taxname + " " + PARAM.gcf

    DIC_PICKLE = word_detect.construct_in(PARAM.file, PATH_P + NAME + ".p", NAME)
    if DIC_PICKLE:
        PATH = PARAM.rfg + "/genome_index/" if PARAM.rfg else ""
        decoding.indexAndOccurencePickle(PATH_P + NAME + ".p", PATH + NAME + ".index")
    else:
        print("Program terminated&No sgRNA sequences in the fasta")
