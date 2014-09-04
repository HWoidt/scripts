#!/bin/bash

# ------------------------
# User configuration
# ------------------------

# directory for this course
HWDESIGN_BASEDIR="~/uni/ms1/hardware_design"

# directory for downloaded content (relative to HWDESIGN_BASEDIR)
# WARNING: this directory will be deleted in order to clean up before
# downloading content! Be sure to use it only for downloaded/generated data
DATA_NAME="coursedata"

# Dependencies:
#       coreutils
#       wget
#       unzip

# #####################################

# ------------------------
# Lectures
# ------------------------

# set up working environment
cd $HWDESIGN_BASEDIR
rm -r $DATA_NAME
mkdir -p $DATA_NAME/labs
cd $DATA_NAME/

# get index document
wget http://www.ict.kth.se/courses/IL2217/

# load 2/pages variant of slides for all lectures
cat index.html  | grep pdf | grep 2/page | cut -d '"' -f 2 | while read f; do wget --max-redirect=1 $f; done

mv F10_2.pdf FA_2.pdf
mv F11_2.pdf FB_2.pdf

# ------------------------
# Labs
# ------------------------
cd labs

# get data
wget http://www.it.kth.se/courses/IL2217/Laborations/index.html
egrep -r pdf\|zip\|PPM index.html | cut -d '"' -f 4 | grep http | while read f; do wget $f; done

# extract archives (into their own directory)
# http://wiki.bash-hackers.org/syntax/pe#substring_removal
# ^-- for ${VAR%str} syntax
for f in $(ls *.zip); do
        unzip -d ${f%.zip} $f
done;
