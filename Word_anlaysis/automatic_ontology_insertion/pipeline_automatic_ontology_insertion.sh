#!/bin/bash

path_file='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/Pre_natal_nutrition/Prenatal_Nutrition_Python_Scripts/automatic_ontology_insertion'


##RUN THE LEXICAL CUE ONTOLOGY INSERTION SCRIPT
python3 $path_file/lexical_cue_ontology_insertion.py


##DETERMINE ALL THE EXCLUDED LCS
python3 $path_file/all_excluded_LCs.py
