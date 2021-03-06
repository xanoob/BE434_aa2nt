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
        description='Get orthogroups, gff, fasta inputs',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-l',
                        '--listog',
                        help='Ortholog groups of interest',
                        metavar='listog',
                        type=argparse.FileType('rt'),
                        default=None,
                        required=True)

    parser.add_argument('-o',
                        '--orthog',
                        help='Ortholog groups with member sequence ids',
                        metavar='ortho',
                        type=argparse.FileType('rt'),
                        default=None,
                        required=True)

    parser.add_argument('-g',
                        '--gff',
                        nargs='+',
                        help='GFF3 files',
                        metavar='gff',
                        type=argparse.FileType('rt'),
                        default=None,
                        required=True)

    parser.add_argument('-f',
                        '--fasta',
                        nargs='+',
                        help='nucleotide fasta ',
                        metavar='fasta',
                        type=argparse.FileType('rt'),
                        default=None,
                        required=True)

    parser.add_argument('-t',
                        '--taxalist',
                        nargs='+',
                        help='list of taxa as in same format as fasta files',
                        type=str,
                        default=None,
                        required=True)

    parser.add_argument('-v',
                        '--verbose',
                        help='Print out updates',
                        action='store_true')


    args = parser.parse_args()

    for entry in args.taxalist:
        if os.path.isfile(entry):
            with open(entry, 'rt', encoding='utf-8') as in_f:
                args.taxalist = in_f.read().splitlines()


    return args

# --------------------------------------------------
def main():
    """Main function"""

    args = get_args()

    vflag = args.verbose
    oglist = ognames(args.listog)
    ogmember = ogmembers(oglist, args.orthog)
    taxalist = args.taxalist
    bytaxa_aa_dict = bytaxa_aa(taxalist, ogmember, vflag)
    aa2nt_dict = aa_to_nt(args.gff, vflag)
    bytaxa_nt_dict = bytaxa_nt(bytaxa_aa_dict, aa2nt_dict, vflag)
    get_status = searchfasta(args.fasta, bytaxa_nt_dict, vflag)


# --------------------------------------------------

def ognames(oginput) -> list:
    """ return list from file of OG names """

    ognames = [og.rstrip() for og in oginput]
    return ognames

def test_ognames():
    """ test that ognames reads file and returns list"""
    ogtestlist = open("test_inputs/listOGs_test.txt")
    assert(ognames(ogtestlist)) == ['OG0000001', 'OG0000002']

def ogmembers(oglist, ogtable) -> dict:
    """ return dictionary of aa sequence ids for OGs supplied by user """

    orthodict = {line.split()[0].replace(':', '') : line.split()[1:] for line in ogtable}
    orthosub = {OG: orthodict[OG] for OG in oglist} # subset of dict in oglist

    return orthosub


def test_ogmembers():
    ogtestlist = open("test_inputs/listOGs_test.txt")
    ogtestmembers = open("test_inputs/listOrthogroups_test.txt")
    ogtestlist_results = ognames(ogtestlist)
    assert(ogmembers(ogtestlist_results, ogtestmembers) == {'OG0000001' : ['Xylcub1_466037', 'Xylcur114988_1_4597462', 'Xylscr1_448861'],
                                                            'OG0000002' : ['Xylcub1_129159', 'Xylcur114988_1_88005']})


def bytaxa_aa(taxalist, ogmember, vflag) -> dict:
    """ return dictionary of aa ids generated by ogmembers() organized by taxa """

    id = re.compile(r".+_(\d{2,})")
    bytaxa_aa = defaultdict(list)
    for taxon in taxalist:
        pattern = re.compile(rf"{taxon}.+")
        for aa in ogmember.values():
            matchlist = [match.group(0) for match in map(pattern.search, aa) if match] # get entries that match
            match_aa = [match.group(1) for match in map(id.search, matchlist) if match] # get ids only
            bytaxa_aa[taxon].extend(match_aa)
        verbose(f"{len(bytaxa_aa[taxon])} aa ids in OG for {taxon}", vflag)

    return bytaxa_aa


def test_bytaxa_aa():
    taxalist = ['Xylcub1', 'Xylcur114988_1', 'Xylscr1']
    ogtestlist = open("test_inputs/listOGs_test.txt")
    ogtestmembers = open("test_inputs/listOrthogroups_test.txt")
    ogtestlist_results = ognames(ogtestlist)
    ogtestmembers_result = ogmembers(ogtestlist_results, ogtestmembers)
    flag = ''
    assert bytaxa_aa(taxalist, ogtestmembers_result, flag) == { 'Xylcub1': ['466037', '129159'],
                                                                          'Xylcur114988_1' : ['4597462', '88005'],
                                                                        'Xylscr1' : ['448861']}

def aa_to_nt(gff_list, vflag) -> dict:
    """ dictionary of aa to nt id per taxa from gff3 files """

    start = process_time()
    verbose("Building aa2nt dictionary from gff3 files", vflag)


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

    verbose(f"Done building aa2nt dict, elapsed time {end - start}", vflag)

    return aa_to_nt


def test_aa_to_nt():

    gff_list = ["test_inputs/Xylcub1_GeneCatalog_.gff", "test_inputs/Xylcur114988_1_GeneCatalog_.gff", "test_inputs/Xylscr1_GeneCatalog_.gff"]
    filedata = {filename: open(filename, 'rt') for filename in gff_list}
    filedata_list = list(filedata.values())
    flag = ''

    assert(aa_to_nt(filedata_list, flag)) == { 'Xylcub1': {'466037': '302', '129159' : '303'},
                                                'Xylcur114988_1' : {'4597462': '304', '88005': '305'},
                                                'Xylscr1' : {'448861' : '301'} }

def bytaxa_nt(bytaxa_aa, aa2nt_dict, vflag) -> dict:
    """ return dictionary of nt ids corresponding with aa ids organized by taxa  """

    start = process_time()
    verbose("Looking up nt ids for supplied aa ids", vflag)
    nucsearch = defaultdict(list)

    for taxon, aa in bytaxa_aa.items():
        nucsearch[taxon] = [aa2nt_dict.get(taxon).get(key) for key in aa]
        verbose(f"Retrieved {len(nucsearch[taxon])} nts for {taxon}", vflag)

    end = process_time()
    verbose(f"Done building nt dict, elapsed time {end - start}", vflag)

    return nucsearch

def test_bytaxa_nt():
    flag = ''
    taxalist = ['Xylcub1', 'Xylcur114988_1', 'Xylscr1']
    ogtestlist = open("test_inputs/listOGs_test.txt")
    ogtestmembers = open("test_inputs/listOrthogroups_test.txt")
    ogtestlist_results = ognames(ogtestlist)
    ogtestmembers_result = ogmembers(ogtestlist_results, ogtestmembers)
    bytaxa_aa_result = bytaxa_aa(taxalist, ogtestmembers_result, flag)

    gff_list = ["test_inputs/Xylcub1_GeneCatalog_.gff", "test_inputs/Xylcur114988_1_GeneCatalog_.gff", "test_inputs/Xylscr1_GeneCatalog_.gff"]
    filedata = {filename: open(filename, 'rt') for filename in gff_list}
    filedata_list = list(filedata.values())
    aa_to_nt_result = (aa_to_nt(filedata_list, flag))

    assert bytaxa_nt(bytaxa_aa_result, aa_to_nt_result, flag) == { 'Xylcub1': ['302', '303'],
                                                                          'Xylcur114988_1' : ['304', '305'],
                                                                        'Xylscr1' : ['301']}

def searchfasta(fastafiles, bytaxa_nt_dict, vflag):
    fname = re.compile(r"^(.+)_.+transcripts")
    start = process_time()

    verbose("Searching for matches in fasta files", vflag)

    outfile_list = []
    for fasta in fastafiles:
        format = 'fasta'
        taxa = fname.search(os.path.splitext(os.path.basename(fasta.name))[0]).group(1)
        outfile = taxa + '.filtered.nt.fasta'
        outfile_list.append(outfile)

        # turn search terms into one regex term
        searchterms = [entry for entry in bytaxa_nt_dict[taxa]]
        separator = '\||\|'
        sjoin = separator.join(searchterms)
        sjoin = '\|' + sjoin + '\|'
        sterms = re.compile(sjoin)

        verbose(f"{len(searchterms)} searchterms for {taxa}", vflag)


        id_dict = SeqIO.to_dict(SeqIO.parse(fasta, format))
        keep_keys = list(filter(sterms.search,id_dict.keys()))

        verbose(f"{len(keep_keys)} filtered keys for {taxa}", vflag)

        # write files
        with open(outfile, 'w') as outf:
            for key in keep_keys:
                SeqIO.write(id_dict.get(key), outf, "fasta")

        # check if files are there

        verbose(f"Finished writing {taxa}", vflag)

    file_status = []
    for ff in outfile_list:
        if os.path.isfile(ff):
            file_status.append('T')
        else:
            pass

    end = process_time()
    verbose(f"Finished! Elapsed time {end - start}", vflag)

    if not vflag:
        print("Finished!")

    return(file_status)


def test_searchfasta():
    """ test if it actually writes something """

    flag = ''
    taxalist = ['Xylcub1', 'Xylcur114988_1', 'Xylscr1']
    ogtestlist = open("test_inputs/listOGs_test.txt")
    ogtestmembers = open("test_inputs/listOrthogroups_test.txt")
    ogtestlist_results = ognames(ogtestlist)
    ogtestmembers_result = ogmembers(ogtestlist_results, ogtestmembers)
    bytaxa_aa_result = bytaxa_aa(taxalist, ogtestmembers_result, flag)

    gff_list = ["test_inputs/Xylcub1_GeneCatalog_.gff", "test_inputs/Xylcur114988_1_GeneCatalog_.gff", "test_inputs/Xylscr1_GeneCatalog_.gff"]
    filedata = {filename: open(filename, 'rt') for filename in gff_list}
    filedata_list = list(filedata.values())
    aa_to_nt_result = (aa_to_nt(filedata_list, flag))
    bytaxa_nt_result = bytaxa_nt(bytaxa_aa_result, aa_to_nt_result, flag)

    fasta_list = ["test_inputs/Xylcub1_GeneCatalog_transcripts_.fasta", "test_inputs/Xylcur114988_1_GeneCatalog_transcripts_.fasta", "test_files/Xylscr1_GeneCatalog_transcripts_.fasta"]
    fasta_data = {filename: open(filename, 'rt') for filename in fasta_list}
    fastadata_list = list(fasta_data.values())

    assert(searchfasta(fastadata_list, bytaxa_nt_result, flag) == ['T', 'T', 'T'])


def verbose(statement, flag):
    if flag:
        print(statement)

# --------------------------------------------------

if __name__ == '__main__':
    main()
