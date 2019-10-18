#!/usr/bin/env python3
"""
Load the MaxiTree object from the taxon_tree_db and insert a new member.
Then, create a pickle file to insert it into the database
"""

import os
import argparse
import requests
import maxi_tree as mt

def args_gestion():
    """
    Take and treat arguments that user gives in command line
    """
    parser = argparse.ArgumentParser(description="Update the MaxiTree object from the database")
    parser.add_argument("-url", metavar="<str>", required=True,
                        help="Taxon_db endpoint")
    parser.add_argument("-taxonDB_name", metavar="<str>", required=True,
                        help="Name of the taxon database")
    parser.add_argument("-o", metavar="<path>", help = "Directory to store taxon_tree data (default : .)", default = ".")
    return parser.parse_args()


if __name__ == '__main__':
    PARAM = args_gestion()

    #MAXITREE = mt.MaxiTree.from_database(PARAM.url, PARAM.treeName)

    MAXITREE = mt.MaxiTree.from_taxon_database(PARAM.url, PARAM.taxonDB_name)

    #MAXITREE.insert(PARAM.taxid, PARAM.taxonDB, PARAM.taxonName) if PARAM.taxid else MAXITREE.insert_plasmid(PARAM.name, PARAM.taxonDB, PARAM.taxonName)

    try:
        os.mkdir(PARAM.o + "/treeDB_data/")
    except OSError:
        print("Be careful : The directory treeDB_data exists")

    MAXITREE.dump(PARAM.o + "/treeDB_data/maxi_tree.p")
