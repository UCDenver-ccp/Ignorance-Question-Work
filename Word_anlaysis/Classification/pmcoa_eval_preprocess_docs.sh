#!/usr/bin/env bash

##path to the held out 30 documents for gold standard evaluation
craft_path='' #TODO: not used currently so we are good!

concept_recognition_path='' #only used with gold standard

scratch_eval_path='/scratch/Users/mabo1182/epistemic_classification/Output_Folders/Evaluation_Files/'
eval_path='/Users/mabo1182/epistemic_classification/Output_Folders/Evaluation_Files/'

concept_system_output='' #only used with gold standard

article_folder='General_PMCOA_Articles/'

tokenized_files='Tokenized_Files/General_PMCOA'

pmcid_sentence_files_path='PMCID_files_sentences/'
general_pmcoa='General_PMCOA'

concept_annotation='' ##not used

ontologies='' #not really used

evaluation_files='all'

gs_tokenized_files=''


##preprocess the articles (word tokenize) to prepare for span detection
python3 eval_preprocess_docs.py -craft_path=$craft_path -concept_recognition_path=$concept_recognition_path -eval_path=$scratch_eval_path -concept_system_output=$concept_system_output -article_folder=$article_folder -tokenized_files=$tokenized_files/ -pmcid_sentence_files=$pmcid_sentence_files_path -concept_annotation=$concept_annotation -ontologies=$ontologies -evaluation_files=$evaluation_files --gs_tokenized_files=$gs_tokenized_files



##move all back to home directory
##copy the tokenized files
cp $scratch_eval_path$tokenized_files/* $eval_path$tokenized_files/


##copy the sentences
cp $scratch_eval_path$pmcid_sentence_files_path$general_pmcoa/* $eval_path$pmcid_sentence_files_path$general_pmcoa/


