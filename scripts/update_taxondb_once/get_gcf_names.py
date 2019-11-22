import os
DIR = "/mnt/arwen-dev/data/databases/mobi/crispr_clean/genome_index/"

for f in os.listdir(DIR):
    gcf = f.replace(".index","").split(" ")[-1]
    if gcf != "None":
        name = " ".join(f.replace(".index", "").split(" ")[:-1])
        print(gcf + "\t" + name)
