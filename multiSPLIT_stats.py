#! /usr/bin/env python3

import os, sys

if len(sys.argv) != 3:
	sys.exit('\nmultiSPLIT_stats.py v. 0.2. Piotr Łukasik, 7th May 2024\n'
	         '-------------------------------------------------------------\n'
	         'This script computes the splitting stats for an amplicon dataset processed by the script MultiSPLIT:  \n'
	         'for all processed libraries, it checks how many reads have been classified to different targets. \n'
	         'The results are printed on the screen, and in the summary file in the "split" folder.\n\n'
	         '    Usage: ./multiSPLIT_stats.py <library_list> <splitting_dir>  \n'
	         '          --- where <library_list> is one of multiSPLIT input files, and <splitting_dir> the output folder of multiSPLIT.py \n\n'
	         '    e.g., multiSPLIT_stats.py sample_list.txt split1 \n')
	         
Script, Library_list, Target_dir = sys.argv


######### Step 1: basic validation, listing targets ####

# Formatting the Target_Dir info - removing the final "/" if present
if Target_dir.endswith("/"):
    Target_dir = Target_dir[:len(Target_dir)-1]
    
# Reading and verifying the Library_list
LibList = open(Library_list, "r")

Lib_list = []
for line in LibList:
    if not len(line.split()) == 3:
        sys.exit('\nFATAL ERROR! Library list seems incorrect!\n')    
    Lib_list.append(line.split()[0])
    
if not len(Lib_list) > 0:
        sys.exit('\nFATAL ERROR! Library list seems empty!\n')

    
    
    
######### Step 2: basic setup, listing targets ####
# Checking if Target_dir exists ...
##### print("Checking the input directory.....   ")
if not os.path.exists(Target_dir):
        sys.exit('\nFATAL ERROR! The indicated target directory does not exist! Check your path, and try again!\n')

# Listing directories in Target_dir, checking if list not empty ...
# Specifically, we assume that all directories should have the name ending with "_trimmed", and count them

TargetDirContents = os.listdir(path=Target_dir)
DirList = []
for item in TargetDirContents:
    if os.path.isdir("%s/%s" % (Target_dir, item)):
        DirList.append(item)

Target_list = []
Dir_list = []

for Dir in DirList:
    if Dir.endswith("_trimmed"):
        Target_list.append(Dir[:-8])
        Dir_list.append(Dir)

if not len(Target_list) > 0:
        sys.exit('\nFATAL ERROR! In the indicated target directory, there are no subdirectories with the expected names\n'
                 '- that is, ending with "_trimmed" or "_untrimmed"!')

#### print("OK!", DirList)


############ Step 3: listing libraries ############

### Creating a dictionary with counts for each library / target
Count_dict = {}          # will ultimately look, {'Lib1': [100,32], 'Lib2': [1,100]]} -> counts of Target1, Target2
for lib in Lib_list:
    Count_dict[lib] = []

# to Count_dict, adding values for all libraries and all targets 
for i in range(len(Target_list)):
    for lib in Lib_list:
        if os.path.exists("%s/%s/%s_R1_%s.fastq" % (Target_dir, Dir_list[i], lib, Target_list[i])):
            with open("%s/%s/%s_R1_%s.fastq" % (Target_dir, Dir_list[i], lib, Target_list[i]), "r") as f:
                Count_dict[lib].append(sum(1 for _ in f)/4)
        else:
            Count_dict[lib].append(0)

# adding Untrimmed / Unrecognized
for lib in Lib_list:
    with open("%s/incorrect_untrimmed/%s_R1_unrecognized.fastq" % (Target_dir, lib), "r") as f:
        Count_dict[lib].append(sum(1 for _ in f)/4)



############ Step 4: printing outputs ############

Output_file = open("%s/splitting_stats.txt" % Target_dir, "w")

print("Library", end="\t")
print("Library", end="\t", file=Output_file)

for target in Target_list:
    print(target, end="\t")
    print(target, end="\t", file=Output_file)    

print("Unrecognized","Total", sep="\t")
print("Unrecognized","Total", sep="\t", file=Output_file)

for lib in Lib_list:
    print(lib, end="\t")
    print(lib, end="\t", file=Output_file)
    
    total = 0
    for value in Count_dict[lib]:
        total += value
        print(int(value), end="\t")
        print(int(value), end="\t", file=Output_file)
    print(int(total))
    print(int(total), file=Output_file)
    
Output_file.close()

#################### DONE ! ##########################
