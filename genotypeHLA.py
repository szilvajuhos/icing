#!/usr/bin/env python
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Alphabet import IUPAC
import click
import sys


def validate_locus(ctx,param,value):
    try:
        assert value in ["HLA-A","HLA-B", "HLA-C", "HLA-DPA1", "HLA-DPB1", "HLA-DQA1", "HLA-DQB1", "HLA-DRA", "HLA-DRB1", "HLA-DRB3", "HLA-DRB4", "HLA-DRB5", "HLA-DRB6", "HLA-DRB7", "HLA-DRB8", "HLA-DRB9"]
    except:
        raise click.BadParameter('Please define locus as HLA-A, HLA-B, HLA-DRB1 ... as you can find in awk -F[\*\ ] \'/^DE/ && /HLA/ {print $4}\' hla.dat|sort -u')
    return value

@click.command(context_settings = dict( help_option_names = ['-h', '--help'] ))
@click.option('--cons','-c', type=str, help='FASTA file containing consensuses (or a single consensus)')
@click.option('--dat','-d', type=str, help='the IMGT/HLA reference hla.dat file from ftp://ftp.ebi.ac.uk/pub/databases/ipd/imgt/hla/hla.dat')
@click.option('--locus','-l', type=str, help='the locus [either HLA-A, HLA-B, HLA-DRB1 ...]',default="HLA-A",callback=validate_locus)
def doGenotype(cons, dat, locus):
    fixedFile = fixIMGTfile(dat)
    ( primaryExons, secondaryExons, intronsAndUTRs) = getCompartmenstForAlleles(fixedFile,locus)
	# for each consensus
	#	preselect types considering only the important exons
	#	refine the preselected list by checking mismatch in the secondary exons
	#	final touches by looking at the introns/UTRs
    for seq_record in SeqIO.parse(cons,"fasta"):
		print "Processing consensus: " + seq_record.id
		# select genotypes considering only the important exons
		genotypes = preSelectTypes(primaryExons,seq_record)
		if len(genotypes) == 0:		# we have failed for some reason
			print "Could not find a proper type for consensus"
		elif len(genotypes) == 1:	# there is a single genotype only: no need to shrink the candidate set
			print "Final HLA type for consensus: " + genotypes[0]
		else:	# there are more than one type candidates, go for exons
			genotypes = selectGenotypesConsideringAllExons(secondaryExons,cons)
			if len(genotypes) > 1:
				genotypes = selectGenotypesConsideringIntronsAndUTRs(intronsAndUTRs,cons)
			print "Final HLA type for consensus:" 
			for gt in genotypes:
				print gt


def getCompartmenstForAlleles(fixedIMGT,locus):
	"""
	Go through each entry in the IMGT/HLA EMBL file, and store out exons in a dictionary.
	For Class-I we are storing exons 2 & 3, for Class-II only exon 2. 
	The data is is like

	primary{}
	ex2='ACTGATCGATCGATACG'
	ex3='CCAGGCCTGGATCGCATTAGC'
	primary['HLA000101']=[ex2,ex3]
	{'HLA000101': ['ACTGATCGATCGATACG', 'CCAGGCCTGGATCGCATTAGC']}
	"""
	print "Processing reference IMGT file"
	primary = {}
	secondary = {}
	intronsAndUTRs = {}
	for seq_record in SeqIO.parse(fixedIMGT,"imgt"):
		# if it is the correct locus and there is a sequence record (not a deleted one)
		if seq_record.description.startswith(locus) and len(seq_record.seq) > 1:
			primary[seq_record.id] = getPrimaryExons(seq_record,locus)
		
	print "ready"	
	return (primary,"rubbish","rubbish")

def getPrimaryExons(sr,locus):
	exonList = []
	for f in sr.features:
		if f.type == "exon":
			if f.qualifiers['number'] == ['2'] :
				exonList.append( sr.seq[f.location.start:f.location.end] )
			if locus in ["HLA-A","HLA-B", "HLA-C"]  and f.qualifiers['number'] == ['3']:
				exonList.append( sr.seq[f.location.start:f.location.end] )
	return exonList

def preSelectTypes(primary,consensus):
	return ["HLA00005","HLA000101"]

def selectGenotypesConsideringAllExons(seconday,consensus):
	return ["HLA00005","HLA000101"]

def selectGenotypesConsideringIntronsAndUTRs(introns,consensus):
	return ["HLA00005","HLA000101"]
	

def fixIMGTfile(hladat):
    """
    For some reason IMGT is not following the standard EMBL format, so we have to add entries to the ID line
    So, we will add an extra "IMGT;" as:
    ID   HLA00001; SV 1; standard; DNA; HUM; 3503 BP.
     going to be -> 
    ID   HLA00001; SV 1; standard; DNA; IMGT; HUM; 3503 BP.
    """
    newFileName = "fixed" + hladat
    fixedfh = open(newFileName,"w")
         
    with open(hladat,"r") as fh:
        for line in fh:
            if line.startswith("ID"):
                parts = line.split()
                line = parts[0] + "   " + \
                        parts[1] + " " +\
                        parts[2] + " " +\
                        parts[3] + " " +\
                        parts[4] + " " +\
                        parts[5] + " " +\
                        "IMGT; " +\
                        parts[6] + " " +\
                        parts[7] + " " +\
                        parts[8] + "\n"
            fixedfh.write(line)
    return newFileName


if __name__ == "__main__":
	doGenotype()
