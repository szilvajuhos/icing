#
# preprocessing steps:
# demultiplex
#bwa mem -x ont2d ref.fa reads.fq
#genomeCoverageBed -ibam 01_ACAGTC.bam -g ../../IMGT/A_gen.fasta -bg
# 
# we are processing the output from this last one
#

import argparse
import subprocess

def parse_args():
    parser = argparse.ArgumentParser(description='Selecting genomic sequence candidates from a demultiplexed ON amplicon 2D read set')
    parser.add_argument('-b', help='The BAM file generated by \"bwa mem -x ont2d ref.fa reads.fqi\"',required=True, dest="bam")
    parser.add_argument('-r', help='IMGT/HLA genomic reference in FASTA format i.e. one from ftp://ftp.ebi.ac.uk/pub/databases/ipd/imgt/hla/fasta/A_gen.fasta ',required=True, dest="reference")
    return parser.parse_args()

def getCoverage(aBam,aRef):
    """
    We are getting an error if bamtools are not installed.
    Otherwise the output is like (reporting coverage for all positions even if coverage is zero)
    HLA:HLA00001    1424    1475    1
    HLA:HLA00001    1476    1493    1
    HLA:HLA00001    1494    1513    1
    HLA:HLA00001    1514    1547    1
    HLA:HLA00001    1548    1582    1
    ...
    and we want to have a list of contigs with the average coverage like
    [ ("HLA:HLA00005", 1066, 1234), ("HLA:HLA00037",24366,2345) , ... ]
    where the first string is the locus name, the second is the cumulative coverage
    and the third is the number of bases considered
    """
    # store values in a dictionary like
    # { "locus":(covSum,count),..}
    cov = {}
    # get the output from the bamtools software and split it into lines
    out = subprocess.check_output(["genomeCoverageBed","-bga","-ibam", aBam, "-g", aRef]).split("\n")
    for line in out:
        cols = line.split()
        if len(cols) > 3:       # avoid spurious empty lines
            (locus,baseCov) = (cols[0],int(cols[3]))
            if locus in cov:        # we have this locus in the dictionary
                (covSum,count) = cov[locus]
                #import pdb;pdb.set_trace()
                covSum += baseCov
                count += 1
                cov[locus] = (covSum,count)
            else:                   # new locus
                cov[locus] = (baseCov,1)
    return cov

def sortByCoverage(cov):
    # now get the averages:
    avgs = []
    for locus in cov.keys():
        (cumulative, count) = cov[locus]
        avgCoverage = float (cumulative)/count
        avgs.append( (locus, avgCoverage, count) )
    # sort it in a descending order
    return sorted(avgs, key=lambda coverage: coverage[1], reverse=True)

def selectBestCandidates(cnd):
    bestOnes = []
    actualCoverage = cnd[0][1]      # get the topmost element
    for candidate in cnd:
        (locus, avgCov, count) = candidate
        #import pdb;pdb.set_trace()
        if avgCov > actualCoverage/2.0:
            bestOnes.append(candidate)
        else:
            continue
        actualCoverage = avgCov
    return bestOnes

def main():
    args = parse_args()                         # parse commmand-line
    coverages = getCoverage(args.bam, args.reference)
    candidates = sortByCoverage(coverages)
    bestOnes = selectBestCandidates(candidates)
    for ca in bestOnes:
        (locus,coverage,count) = ca
        # print out reference names we are considering for consensus generation
        print locus, coverage

if __name__ == '__main__':
    main()
