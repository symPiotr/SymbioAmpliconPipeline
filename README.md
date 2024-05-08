# Symbio Amplicon Pipeline

### This repository contains recent versions of scripts, and supplemental files, for the analysis of quantitative multi-target amplicon sequencing data that were developed and used used by the Symbiosis Evolution Group at Jagiellonian University.  
  
Earlier versions of the tools were developed as a collaborative effort of several group members and collaborators, including ..., and can be found at
[https://github.com/MikeCollasa/LSD](https://github.com/MikeCollasa/LSD), [https://github.com/Symbiosis-JU/Bioinformatic-pipelines/blob/main/Example_analysis.md](https://github.com/Symbiosis-JU/Bioinformatic-pipelines/blob/main/Example_analysis.md) ...  
  
This document will evolve dramatically over the next few months, and so here are the preliminary information needed to get the lab members started on amplicon data analysis.
  
1. Before you receive the multi-target amplicon sequencing data for your biological samples:  
   - Make sure that you have the full list of samples, with metadata - sample origin, collection date, experimental treatment... These data will form the core of one of your Supplementary Table 1.  
   - Make sure that you have the list of marker regions that you were amplifying, with information on primer sequences.  
   - Make sure that you have laboratory protocols written down.  
  
2. You want to make sure that you have the latest versions of the analysis scripts and additional files. If you work on one of the Institute of Environmental Sciences clusters, you want to ensure that you have folder **/mnt/qnap/users/symbio/SymbioAmpliconPipeline/** in your PATH. Alternatively, you may want to clone the current repository to your chosen location and then add it to your PATH.  
Read [here](https://linuxize.com/post/how-to-add-directory-to-path-in-linux/) how to "add to PATH".
  
3. Once you receive the data, and it is secure in a "raw_data" folder on the cluster, you want to start from breaking it up into bins corresponding to different targetted regions. We have been doing this using script **multiPISS.py**. It is being redeveloped as [multiSPLIT.py](multiSPLIT.py). New functionalities include more extensive instructions, ability to accept gzip-compressed (*.gz) files as input, and the computation of statistics on the number of reads in each category.

"""
(base) piotr.lukasik@azor:~/symbio/SymbioAmpliconPipeline$ multiSPLIT.py 

-------- multiSPLIT v. 0.21 by Malgorzata Lipowska & the Symbio Lab; last changes on 07.05.2024 by Piotr Lukasik ----------

This script reads a list of fastq files (gzipped or uncompressed) corresponding to multi-target amplicon samples
It then screens all reads for the presence of specified primers (potentially preceded by variable-length or informative inserts)
It trims inserts and primers and outputs such filtered reads, sorted by target regions, to directories representing these regions.
It then outputs the statistics - numbers of reads in each of the 

Usage: 
    multiSPLIT.py <sample_list> <input_dir> <primer_list> <output_dir> <informative_indexes?> <number_of_cores>

Please provide:
1) FULL path to the sample list file, with information about your libraries created in following manner (tab-separated):
    SampleName SampleName_R1.fastq	SampleName_R2.fastq
    OR
    SampleName SampleName_R1.fq.gz	SampleName_R2.fq.gz
### if your files have name format SampleName_R1.fq.gz, SampleName_R2.fq.gz, you can generate the list using a loop ---
for file in *_R1.fq.gz; do
    SampleName=`basename $file _R1.fq.gz `
    SampleNameMod=$(echo "$SampleName" | sed 's/-/_/g' | sed 's/_S[0-9]\+$//g')
    echo $SampleNameMod "$SampleName"_R1.fq.gz "$SampleName"_R2.fq.gz >> sample_list.txt
done


2) FULL path to the directory with R1 and R2 reads for all the amplicon libraries that you want to analyse,
    e.g.: /mnt/qnap/users/symbio/raw_data/illumina/amplicon_sequencing/20240430_NextSeq_batch21/GDF)
    Note that shortcuts such as "." may not work!

3) Path to the primer list, where lines represent different primers - for example, "COI	CCHGAYATRGCHTTYCCHCG	CDGGRTGNCCRAARAAYCA"
    This will often be: /mnt/qnap/users/symbio/SymbioAmpliconPipeline/primer_list_standard.txt
    Or perhaps:         /mnt/qnap/users/symbio/SymbioAmpliconPipeline/primer_list_Entomophthora.txt ?
   
4) Path to the output directory
    e.g.: /home/piotr.lukasik/20240507_amplicons/split1)
    
5) Information on whether the last two characters of your sample name indicate well number
   (Have you consiously used informative inserts in your library prep procedure?)
    1=True, 0=False
    Note: If you provide 1 but the last two characters in the sample name are not numbers, it may create an error!

6) Number of cores to use
    e.g. 16
"""
   
5. From there, for each target region, we will proceed using the pipelines roughly outlined at [https://github.com/Symbiosis-JU/Bioinformatic-pipelines/blob/main/Example_analysis.md](https://github.com/Symbiosis-JU/Bioinformatic-pipelines/blob/main/Example_analysis.md) ... although the details will be changing!  

