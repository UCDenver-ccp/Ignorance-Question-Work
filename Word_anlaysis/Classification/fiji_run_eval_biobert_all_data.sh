#!/usr/bin/env bash

##Move test.tsv file to supercomputer fiji for predictions




##array of all the ontologies
declare -a arr=('full_unknown' 'explicit_question' 'incomplete_evidence' 'probable_understanding' 'superficial_relationship' 'future_work' 'future_prediction' 'important_consideration' 'anomaly_curious_finding' 'alternative_options_controversy' 'difficult_task' 'problem_complication' 'question_answered_by_this_work' '1_binary_combined')

#declare -a arr=('0_all_combined') #separate because of labels are different

#declare -a arr=('1_binary_combined')

##biobert path
#biobert_path='/BIOBERT/'
output='output'
##model path
model_info='/scratch/Users/mabo1182/epistemic_classification/Models/SPAN_DETECTION/'

tokenized_files='/scratch/Users/mabo1182/epistemic_classification/Output_Folders/Tokenized_Files/'

##the output folder for the results of running BioBERT for span detection
results_span_detection='/scratch/Users/mabo1182/epistemic_classification/Output_Folders/Results_span_detection/'
biobert='/BIOBERT/'
train='train.tsv'
train_dev='train_dev.tsv'

biobert_training='BIOBERT_TRAINING'
scratch='/scratch'

##loop over each ontology and run the corresponding BioBERT model
for i in "${arr[@]}"
do
    ##Need to get the global step to know the number for the model run
    echo $i

    ##move the model info to the output dir
    rm -r $results_span_detection$i$biobert
    mkdir $results_span_detection$i$biobert
    cp  $model_info$i$biobert$output/* $results_span_detection$i$biobert

    eval_results_path=$results_span_detection$i$biobert
    algo='BIOBERT'

    ##get the global step number
    python3 biobert_model_eval_result.py -eval_results_path=$eval_results_path -ontology=$i -algo=$algo
    global_step_file='global_step_num.txt'
    eval_global_step_file=$eval_results_path$global_step_file


    global_step=$(<$eval_global_step_file)
    echo $global_step



    ##Articles to run BioBERT span detection on  -
    #full data
    NER_DIR='/scratch/Users/mabo1182/epistemic_classification/Output_Folders/Tokenized_Files/BIOBERT/'



    ##Output files
    OUTPUT_DIR=$results_span_detection$i$biobert

    model='model.ckpt-' ##need highest number found - need to gather this from eval_results


    ##the original base model for BioBERT for running the algorithm
    biobert_original='/Users/mabo1182/epistemic_classification/Code/biobert_v1.0_pubmed_pmc/'


    ## Run BioBERT span detection algorithm
    #https://blog.insightdatascience.com/using-bert-for-state-of-the-art-pre-training-for-natural-language-processing-1d87142c29e7
    ##move label2idx.pkl to output directory to make this work with eval (also changed run_ner.py to get rid of error)
    python3 biobert/run_ner.py --do_train=true --do_predict=true --vocab_file=$biobert_original/vocab.txt --bert_config_file=$biobert_original/bert_config.json --init_checkpoint=$OUTPUT_DIR$model$global_step  --mmax_seq_length=410 --num_train_epochs=0.1 --data_dir=$NER_DIR --output_dir=$OUTPUT_DIR


done


##move label_test.txt and token_test.txt locally to do ner_detokenize and create dataframe for next steps - back to run_eval_biobert_pipepine_1.5.sh

