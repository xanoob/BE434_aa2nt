#!/usr/bin/env python3
"""
Author : RoxanneB <RoxanneB@localhost>
Date   : 2021-11-29
Purpose: Retrieve nt seq equivalent of selected aa seqs from an orthogroup
"""

import argparse
import re
import os
from Bio import SeqIO
from time import process_time
from collections import defaultdict

# --------------------------------------------------
def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='Get arguments for script',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-l',
                        '--listog',
                        help='Ortholog groups of interest',
                        metavar='listog',
                        type=argparse.FileType('rt'),
                        default=None)

    parser.add_argument('-o',
                        '--orthog',
                        help='Ortholog groups with member sequence ids',
                        metavar='ortho',
                        type=argparse.FileType('rt'),
                        default=None)

    parser.add_argument('-g',
                        '--gff',
                        nargs='+',
                        help='GFF3 files',
                        metavar='gff',
                        type=argparse.FileType('rt'),
                        default=None)

    parser.add_argument('-f',
                        '--fasta',
                        nargs='+',
                        help='fasta',
                        metavar='fasta',
                        type=argparse.FileType('rt'),
                        default=None)

    parser.add_argument('-t',
                        '--taxalist',
                        nargs='+',
                        help='list of taxa as in same format as fasta files',
                        type=str,
                        default=None)

    return parser.parse_args()


# --------------------------------------------------
def main():
    """Main function"""

    args = get_args()
    oglist = ognames(args.listog)
    ogmember = ogmembers(oglist, args.orthog)
    # taxalist = ['Xylcub1', 'Xylcube1', 'Xylcur114988_1', 'Xylscr1']
    taxalist = args.taxalist
    bytaxa_aa_dict = bytaxa_aa(taxalist, ogmember)
    aa2nt_dict = aa_to_nt(args.gff)
    bytaxa_nt_dict = bytaxa_nt(bytaxa_aa_dict, aa2nt_dict)
    searchfasta(args.fasta, bytaxa_nt_dict)

# --------------------------------------------------

def ognames(oginput) -> list:
    """ return list from file of OG names """

    ognames = [og.rstrip() for og in oginput]
    return(ognames)


def ogmembers(oglist, ogtable) -> dict:
    """ return dictionary of aa sequence ids for OGs supplied by user """

    orthodict = {line.split()[0].replace(':', '') : line.split()[1:] for line in ogtable}
    orthosub = {OG: orthodict[OG] for OG in oglist} # subset of dict in oglist

    return(orthosub)


def bytaxa_aa(taxalist, ogmember) -> dict:
    """ return dictionary of aa ids generated by ogmembers() organized by taxa """

    id = re.compile(r".+_(\d{2,})")
    bytaxa_aa = defaultdict(list)
    for taxon in taxalist:
        pattern = re.compile(rf"{taxon}.+")
        for aa in ogmember.values():
            matchlist = [match.group(0) for match in map(pattern.search, aa) if match] # get entries that match
            match_aa = [match.group(1) for match in map(id.search, matchlist) if match] # get ids only
            bytaxa_aa[taxon].extend(match_aa)
        print(f"{len(bytaxa_aa[taxon])} aa ids in OG for {taxon}")

    return(bytaxa_aa)


def bytaxa_nt(bytaxa_aa, aa2nt_dict) -> dict:
    """ return dictionary of nt ids corresponding with aa ids organized by taxa  """

    start = process_time()
    print("look up nt ids for supplied aa ids")
    nucsearch = defaultdict(list)

    for taxon, aa in bytaxa_aa.items():
        nucsearch[taxon] = [aa2nt_dict.get(taxon).get(key) for key in aa]
        print(f"retrieved {len(nucsearch[taxon])} nts for {taxon}")

    end = process_time()
    print(f"Done building nt dict, elapsed time {end - start}")
    return(nucsearch)



def aa_to_nt(gff_list) -> dict:
    """ dictionary of aa to nt id per taxa from gff3 files """

    start = process_time()
    print("building aa2nt dictionary")
    taxon_name = re.compile(r"^(.+)_\w+_")
    aaID = re.compile(r"proteinId=(\d+)")
    ntID = re.compile(r"transcriptId=(\d+)")
    getgeneonly = re.compile(r"scaffold_\d+\s+prediction\s+gene")
    aa_to_nt = defaultdict(dict)

    for gff in gff_list:
        taxon = taxon_name.search(os.path.splitext(os.path.basename(gff.name))[0]).group(1)
        for line in gff:
            if getgeneonly.match(line): # get ID records for 'gene' entries only
                aa_to_nt[taxon][aaID.search(line).group(1)] = ntID.search(line).group(1)


    end = process_time()
    print(f"Done building aa2nt dict, elapsed time {end - start}")

    return(aa_to_nt)


def searchfasta(fastafiles, bytaxa_nt_dict):
    fname = re.compile(r"^(.+)_.+transcripts")
    start = process_time()
    print("searching matches in fasta record")

    for fasta in fastafiles:
        format = 'fasta'
        taxa = fname.search(os.path.splitext(os.path.basename(fasta.name))[0]).group(1)
        outfile = taxa + '.filtered.nt.fasta'

        # turn search terms into one regex term
        searchterms = [entry for entry in bytaxa_nt_dict[taxa]]
        separator = '\||\|'
        sjoin = separator.join(searchterms)
        sjoin = '\|' + sjoin + '\|'
        sterms = re.compile(sjoin)

        print(f"{len(searchterms)} searchterms for {taxa}")

        id_dict = SeqIO.to_dict(SeqIO.parse(fasta, format))
        keep_keys = list(filter(sterms.search,id_dict.keys()))

        print(f"{len(keep_keys)} filtered keys for {taxa}")


        # write files
        with open(outfile, 'w') as outf:
            for key in keep_keys:
                SeqIO.write(id_dict.get(key), outf, "fasta")

        end = process_time()
        print(f"Finished writing, elapsed time {end - start}")

# --------------------------------------------------

if __name__ == '__main__':
    main()
