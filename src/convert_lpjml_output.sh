#!/bin/bash

echo "This program converts all binary files in a given LPJmL output directory"
echo "to netcdf with LPJmL tool bin2cdf."

if [ "$LPJROOT" = "" ]; then
    echo "Error: LPJROOT is empty."
    exit 1;
fi

if [ "$1" = "" ]; then
    echo "Error: I need the first arguement to be the input folder."
    exit 1;
fi

if [ "$2" = "" ]; then
    echo "Error: I need the second arguement to be the output folder."
    exit 1;
fi

input_folder=$1
output_folder=$2

echo "Input folder: $input_folder"
echo "Output folder: $output_folder"


mkdir -p $output_folder

grid_file=$input_folder/grid.bin

for filename in $( ls $input_folder/*.bin.json ); do
    
    varname=$(basename "$filename" .bin.json)
    echo "Detect file: $filename => $varname"
    
    #cmd="$LPJROOT/bin/bin2cdf -metafile $varname $grid_file $input_folder/${varname}.bin $output_folder/${varname}.nc"
    cmd="$LPJROOT/bin/bin2cdf $varname $grid_file $input_folder/${varname}.bin $output_folder/${varname}.nc"
    echo ">> $cmd"
    eval $cmd 

done 




