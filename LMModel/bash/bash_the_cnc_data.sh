#!/bin/bash

# Author: Thomas M. Rudolf
# Created: 17th November 2023
# Last Modified: 19th November 2023

# Description:
# using the compbined file in /preprocessed_data from different measurements with the same machine tool but changing parameters




#combine all existing preprocessed data and save them in total_cnc_data.sv:
head -n 1 ../preprocessed_data/preprocessed_cnc_data_wsp1030_co.csv > ../preprocessed_data/total_cnc_data.out && tail -n+3 -q ../preprocessed_data/*.csv >> ../preprocessed_data/total_cnc_data.out
cp ../preprocessed_data/total_cnc_data.out ../preprocessed_data/total_cnc_data.csv
rm ../preprocessed_data/total_cnc_data.out