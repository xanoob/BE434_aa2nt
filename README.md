# aa2nt

### BE534 final project

A script to retrieve associated nucleotide sequence records for amino acid sequence records in an ortholog group. This is designed for use with sequences downloaded from JGI.

### Usage

**The program uses as input**

* A file containig a list of selected ortholog group IDs `(-l, --listog)`
* A file containing a table of taxon-sequence IDs per ortholog group, usually output from an ortholog inference program `(-o, orthog)`
* GFF3 files for each taxa `(-g, gff)`
* Nucleotide fasta files for each taxa `(-f, fasta)`
* List of taxa of interest, can be supplied as a text file with one taxon name per line `(-t, taxalist)`
* Users can also specify verbose output (e.g. print what step the script is on) `(-v, verbose)`

**Examples** 

Taxa list as text file:
```
./aa2nt.py -l example_inputs/listOGs.txt -o example_inputs/OGmembers.txt -g example_inputs/*.gff3 -f example_inputs/*.fasta -t example_inputs/taxalist.txt -v

```

Taxalist supplied as argument:
```
./aa2nt.py -l example_inputs/listOGs.txt -o example_inputs/OGmembers.txt -g example_inputs/*.gff3 -f example_inputs/*.fasta -t Xylcub1 Xylscr1 -v

```


### Problem Addressed

Ortholog inference programs (i.e. orthofinder, orthoMCL) utilize amino acid sequences to build ortholog groups. However, we may be interested in retrieving the equivalent nucleotide sequence record for amino acid sequences within selected groups.

**Example orthofinder output table with fasta header based IDs for members in the group**

```
OG0000006: Xylacu1_504868 Xylacu1_506276 Xylcas124033_1_547580 Xylcas124033_1_548538 Xylcub1_118760 Xylcub1_354408 Xylcub1_463436 Xylcub1_481024 Xylcub1_505496 Xylcube1_112179
OG0000007: Xylacu1_188876 Xylacu1_211636 Xylacu1_239015 Xylacu1_334457 Xyllon1_180855 Xyllon1_529536 Xylscr1_129476 Xylscr1_215213 Xylscr1_405676 Xylscr1_414426 Xylscr1_419125 Xylscr1_421215
OG0000008: Xylacu1_276242 Xylcas124033_1_171284 Xylcas124033_1_265152 Xylcas124033_1_28047 Xylcas124033_1_341743 Xylcas124033_1_454174 Xylcas124033_1_513140 

```

In our case, we were interested in retrieving nucleotide sequences for core genes. To do this, we needed to find a way to link sequence ids as formatted in the orthofinder output file to fasta headders in nucleotide and amino acid sequence files. 

However, there were no distinguishing features that linked all types of ID. As an example, for the same record, the following IDs apply:

Ortholog output: Xylscr1_99687 
Amino acid fasta header: >jgi|Xylscr1|99687|CE99686_5963 
Nucleotide fasta header: >jgi|Xylscr1|100117|CE99686_5963 

One can easily link ortholog id to the amino acid fasta header since they have **99687** in common. To link the aa id to nt id, we need to search the gff3 file for each taxa, which contains this information:

```
scaffold_1	prediction	gene	4997	7713	0	-	.	ID=gene_2;Name=jgi.p|Xylscr1|99687;portal_id=Xylscr1;product_name=expressed protein;proteinId=2;transcriptId=100117

```

The script connects all three to retrieve the nucleotide id which can be used to pull out specific fasta sequences.
