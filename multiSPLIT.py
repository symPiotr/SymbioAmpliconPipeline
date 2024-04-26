#! /usr/bin/env python3

### Program requirements test and tips should go here
import sys, os, re, time, multiprocessing
if len(sys.argv) != 7:
	sys.exit("""ERROR! CHECK YOUR INPUT PARAMETERS!
-------- multiSPLIT v. 0.1 by Malgorzata Lipowska & Symbio Lab; last changes on 25.04.2024 by Piotr Lukasik ----------

This script reads a list of fastq files (gzipped or uncompressed) corresponding to multi-target amplicon samples
It then screens all reads for the presence of specified primers (potentially preceded by variable-length or informative inserts)
It trims inserts and primers and outputs such filtered reads, sorted by target regions, to directories representing these regions.

Usage: 
    multiSPLIT.py <sample_list> <input_dir> <primer_list> <output_dir> <informative_indexes?> <number_of_cores>

Please provide:
1) sample list with information about your libraries created in following manner (tab-separated):
    SampleName SampleName_R1.fastq	SampleName_R2.fastq
    OR
    SampleName SampleName_R1.fq.gz	SampleName_R2.fq.gz

2) FULL path to the directory with R1 and R2 reads for all the amplicon libraries that you want to analyse,
    e.g.: /home/users/symbio/20240424_amplicons/raw_data)
    Note that shortcuts such as "." may not work!

3) Path to the primer list, where lines represent different primers - for example, "COI	CCHGAYATRGCHTTYCCHCG	CDGGRTGNCCRAARAAYCA"
    This will often be: /mnt/qnap/users/symbio/SymbioAmpliconPipeline/primer_list_standard.txt
    Or perhaps:         /mnt/qnap/users/symbio/SymbioAmpliconPipeline/primer_list_Entomophthora.txt ?
   
4) Path to the output directory
    e.g.: /home/users/symbio/20240424_amplicons/analysis1)

5) Information on whether the last two characters of your sample name indicate well number
   (Have you consiously used informative inserts in your library prep procedure?)
    1=True, 0=False
    Note: If you provide 1 but the last two characters in the sample name are not numbers, it may create an error!

6) Number of cores to use
    e.g. 16
    
""")

Script, sample_list, path_to_your_raw_data, primers_file, output_path, well_info, core_no = sys.argv


### required variables
#primers_file = "/mnt/qnap/users/symbio/software/Informative_indexes_script/primers_Zuza_Igor.txt"
IUPAC_file = "/mnt/qnap/users/symbio/SymbioAmpliconPipeline/bases_IUPAC.txt"
insert_file_F = "/mnt/qnap/users/symbio/SymbioAmpliconPipeline/inserts_F.txt"
insert_file_R = "/mnt/qnap/users/symbio/SymbioAmpliconPipeline/inserts_R.txt"
input_path = path_to_your_raw_data
output_path = output_path
list_file = sample_list
well_in_name_flag = int(well_info)
core_limit = int(core_no)

### functions
# fastq importer to list of lists
def FastqImport(fastq_file):
    if fastq_file.strip().split(".")[-1] == "gz":
        os.system("gunzip -c %s > %s/temp.fq" % (fastq_file, Output_Dir))
        fastq_file = "%s/temp.fq" % Output_Dir
	input = open(fastq_file,"r")
	fastq=[]
	line_counter = 0
	for line in input:
		if line_counter == 0:
			seq_list=[]
		seq_list.append(line.strip())
		line_counter += 1
		if line_counter == 4:
			fastq.append(seq_list)
			line_counter = 0
	input.close()
	if os.path.exists("%s/temp.fq" % Output_Dir):
        os.remove("%s/temp.fq" % Output_Dir)
	return(fastq)

# ambiguous bases dictionary importer
def IUPACImport(IUPAC_file):
	input = open(IUPAC_file,"r")
	IUPAC_dict = {}
	for line in input:
		base_original = line.split()[0]
		base_trans = line.split()[1]
		IUPAC_dict[base_original] = base_trans
	input.close()
	return(IUPAC_dict)

# IUPAC base code to regexp translator
def IUPACRegex(seq):
	seq_regex = ""
	for letter in seq:
		seq_regex += IUPAC_dict[letter]
	return(seq_regex)
		

# import primers into dictionary
def PrimersImport(primers_file):
	input = open(primers_file,"r")
	primers_dict = {}
	for line in input:
	    if len(line.strip().split()) == 3 and not line.startswith("#"):
		    name = line.strip().split()[0]
		    F_seq_raw = line.split()[1]
		    R_seq_raw = line.split()[2]
		    F_seq_regex = IUPACRegex(F_seq_raw)
		    R_seq_regex = IUPACRegex(R_seq_raw)
		    primers_dict[name] = [F_seq_regex,R_seq_regex]
	input.close()
	return(primers_dict)

# import inserts into dictionaries by primer
def InsImport(insert_file):
	input = open(insert_file,"r")
	ins_dict = {}
	primer = ""
	for line in input:
		if primer != line.split()[0]:
			primer = line.split()[0]
			ins_dict[primer] = {}
		row = line.split()[1]
		if len(line.split()) == 3:
			ins = line.split()[2] + "$"
		else:
			ins = "$"
		ins_dict[primer][ins] = row
	input.close()
	return(ins_dict)

# import tab-separated list of sample names and their forward and reverse file names
def ListImport(list_file):
	input = open(list_file,"r")
	samples_list = []
	for line in input:
		samples_list.append(line.strip().split())
	input.close()
	return(samples_list)

# flip order in insert dictionaries by primer, adding the NA category
def InsDictFlip(ins_dict):
	ins_dict_flip = {}
	for primer in ins_dict:
		ins_dict_flip[primer]={}
		for ins in ins_dict[primer]:
			val = ins_dict[primer][ins]
			ins_dict_flip[primer][val] = ins
		ins_dict_flip[primer]["NA"]="NA"
	return(ins_dict_flip)

# match insert to the end of sequence fragment, prefer longer matches
def InsMatch(primer,seq,ins_dict):
	match_len = 0
	position = "NA"
	for ins_seq in ins_dict[primer]:
		if match_len < len(ins_seq):
			ins_match = re.search(ins_seq,seq)
			if bool(ins_match):
				match_len = len(ins_seq)
				position = ins_dict[primer][ins_seq]
	return(position)

# matrix for visualizing wells recognized as source of sequence
def PlateVis():
	header_col = [""] + list(range(1,14)) + ["NA"]
	header_row = list(range(1,10)) + ["NA"]
	plate_vis = []
	plate_vis.append(header_col)
	for row in header_row:
		row_vis = [row]
		for col in header_col[1:]:
				row_vis.append(0)
		plate_vis.append(row_vis)
	return(plate_vis)

# plate visualization printout
def PlatePrint(plate_vis_dict,primer,flip_ins_F_dict,flip_ins_R_dict):
	plate_vis = []
	row_flag = 1
	for row in plate_vis_dict[primer]:
		col_flag = 1
		row_string=""
		for col in row:
			if (row_flag == 1) & (col_flag == 0):
				col = str(col) + "_" + str(flip_ins_R_dict[primer][str(col)])
			if (row_flag == 0) & (col_flag == 1):
				col = str(col) + "_" + str(flip_ins_F_dict[primer][str(col)])
			col_flag = 0
			row_string += str(col) + "\t"
		row_string = row_string.rstrip()
		row_flag = 0
		plate_vis.append(row_string)
	return(plate_vis)

### pipeline
# import dictionaries
IUPAC_dict = IUPACImport(IUPAC_file)
primers_dict = PrimersImport(primers_file)
ins_F_dict = InsImport(insert_file_F)
ins_R_dict = InsImport(insert_file_R)
flip_ins_F_dict = InsDictFlip(ins_F_dict)
flip_ins_R_dict = InsDictFlip(ins_R_dict)

# import list_file and read content of input_path
os.chdir(input_path)
files_list = os.listdir(input_path)
samples_list = ListImport(list_file)

# create output directories
os.mkdir(output_path)
os.mkdir(output_path+"/incorrect_untrimmed")
for primer in primers_dict:
	os.mkdir(output_path + "/" + primer + "_trimmed")


if well_in_name_flag == 1:
	os.mkdir(output_path + "/plate_visualizations")

# run PISS:
#   for each pair of files from the list_file present in the input_path:
#	   if well_info == 1; create visualization file
#	   for each pair of F and R reads:
#		   for each primer in primers_dict:
#			   search for match within the first 30 nucleotides of the sequence
#			   if primers are recognized in both F and R read; if well_info == 0 assign as recognized; otherwise unrecognized
#			   if recognized & well_info == 1; search for match among primer-specific list of inserts within nucleotides directly preceding recognized primer; add value to visualization file
#				   if insert-determined well no matches well no declared in sample name; assign as recognized; otherwise wrong-well
#		   if recognized; trim off primer; otherwise do not trim
#		   output to files in directories representing recognized genes with correct well assignment (trimmed), recognized genes from wroong-well, and unrecognized genes
#	   draw plate visualization output file

def PrimerInsertSequenceSort(sample):
#	global well_in_name_flag
#	global output_path
#	for sample in samples_list:
	if (sample[1] in files_list) & (sample[2] in files_list):
		file = sample[0]
		fastq_file_F = sample[1]
		fastq_file_R = sample[2]
		plate_vis_dict = {}
		if well_in_name_flag == 1:
			well_no = int(file[-2:])
			for primer in primers_dict:
				if (primer in ins_F_dict) & (primer in ins_R_dict):
					plate_vis_dict[primer] = PlateVis()
		os.chdir(input_path)
		fastq_F = FastqImport(fastq_file_F)
		fastq_R = FastqImport(fastq_file_R)
		os.chdir(output_path)
		total_seq = 0
		total_recogn = 0
		for read in range(0,len(fastq_F)):
			if fastq_F[read][0].split()[0] == fastq_R[read][0].split()[0]:
				read_F = fastq_F[read]
				read_R = fastq_R[read]
				seq_F = read_F[1][0:30]
				seq_R = read_R[1][0:30]
				ins_F = ""
				ins_R = ""
				total_seq += 1
				marker = "unrecognized"
				ok_well = 0
				for primer in primers_dict:
					F_match_temp = re.search(primers_dict[primer][0],seq_F)
					R_match_temp = re.search(primers_dict[primer][1],seq_R)
					if bool(F_match_temp) & bool(R_match_temp):
						marker = primer
						F_match = F_match_temp
						R_match = R_match_temp
				if marker != "unrecognized":
					total_recogn += 1
					if (well_in_name_flag == 1) & (marker in plate_vis_dict):
						ins_F = seq_F[0:F_match.start()]
						ins_R = seq_R[0:R_match.start()]
						row = InsMatch(marker,ins_F,ins_F_dict)
						col = InsMatch(marker,ins_R,ins_R_dict)
						if (row != "NA") & (col != "NA"):
							well = (int(col)-1)*8+int(row)
						for row_vis in plate_vis_dict[marker]:
							if str(row_vis[0]) == row:
								for col_vis in plate_vis_dict[marker][0]:
									if str(col_vis) == col:
										row_vis[col_vis] += 1
						if well_no == well:
							ok_well = 1
					else:
						ok_well = 1
				if ok_well == 1:
					read_F[1] = read_F[1][F_match.end():]
					read_F[3] = read_F[3][F_match.end():]
					read_R[1] = read_R[1][R_match.end():]
					read_R[3] = read_R[3][R_match.end():]
					outp_file_F = open(marker + "_trimmed/" + file + "_R1_" + marker + ".fastq","a")
					outp_file_R = open(marker + "_trimmed/" + file + "_R2_" + marker + ".fastq","a")
				else:
					if (well_in_name_flag == 1) & (marker != "unrecognized"):
						outp_file_F = open("incorrect_untrimmed/" + file + "_R1_" + marker + "_wrong-well.fastq","a")
						outp_file_R = open("incorrect_untrimmed/" + file + "_R2_" + marker + "_wrong-well.fastq","a")
					else:
						outp_file_F = open("incorrect_untrimmed/" + file + "_R1_" + marker + ".fastq","a")
						outp_file_R = open("incorrect_untrimmed/" + file + "_R2_" + marker + ".fastq","a")				
				for element in read_F:
					print(element, file = outp_file_F)
				for element in read_R:
					print(element,file = outp_file_R)
				outp_file_F.close()
				outp_file_R.close()
		for primer in primers_dict:
			if (well_in_name_flag == 1) & (primer in plate_vis_dict):
				outp_file_plate = open("plate_visualizations/" + file + "_" + primer + "_plate","a")
				for row_plate_vis in PlatePrint(plate_vis_dict,primer,flip_ins_F_dict,flip_ins_R_dict):
					print(row_plate_vis, file = outp_file_plate)
				outp_file_plate.close()

def MultiPISS(samples_list, core_limit):
	with multiprocessing.Pool(core_limit) as pool:
		pool.map(PrimerInsertSequenceSort,samples_list)

def Time_PISS(samples_list):
	time_start = time.time()
	for sample in samples_list:
		PrimerInsertSequenceSort(sample)
	duration = str(round(time.time() - time_start,2))
	print("the process lasted " + duration + " seconds")

def Time_MultiPISS(samples_list,core_limit):
	time_start = time.time()
	MultiPISS(samples_list,core_limit)
	duration = str(round(time.time() - time_start,2))
	print("the process lasted " + duration + " seconds")
	
#Time_PISS(samples_list)
Time_MultiPISS(samples_list,core_limit)
