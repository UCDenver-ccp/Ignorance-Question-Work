#!/usr/bin/env bash

##path to the main craft documents
craft_path='../CRAFT-3.1.3/' #not used!

##concept recongition master path
concept_recognition_master_path='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Concept-Recognition-as-Translation-master/'

##path to the output folders
concept_recognition_path='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Concept-Recognition-as-Translation-master/Output_Folders/'

##path to the evaluation files where all output will be stored during the evaluation
eval_path='/Output_Folders/Evaluation_Files/'



##folders for all outputs within the evaluation files
concept_system_output='concept_system_output/'
article_folder='Articles/' #want files.txt
tokenized_files='Tokenized_Files/'
save_models_path='Models/SPAN_DETECTION/'
results_span_detection='Results_span_detection/'
concept_norm_files='Concept_Norm_Files/'
pmcid_sentence_files_path='PMCID_files_sentences/'
concept_annotation='concept-annotation/' ##not used!

##list of ontologies that have annotations to preproess
ontologies='full_unknown,explicit_question,incomplete_evidence,probable_understanding,superficial_relationship,future_work,future_prediction,important_consideration,anomaly_curious_finding,alternative_options_controversy,difficult_task,problem_complication,question_answered_by_this_work'

ontologies='0_all_combined,1_binary_combined'

ontologies='1_binary_combined'


##list of excluded files from training if you want in order to now evaluate on internally - default is None
evaluation_files="all"

##whether we have the gold standard to compare or not (True or False) - default False
gold_standard='True'

##the span detection algorithms to use
algos='CRF' #CRF, LSTM, LSTM_CRF, CHAR_EMBEDDINGS, LSTM_ELMO, BIOBERT
#algos='BIOBERT'

##preprocess the articles (word tokenize) to prepare for span detection
python3 eval_preprocess_docs.py -craft_path=$craft_path -concept_recognition_path=$concept_recognition_path -eval_path=$concept_recognition_path -concept_system_output=$concept_system_output -article_folder=$article_folder -tokenized_files=$tokenized_files -pmcid_sentence_files=$pmcid_sentence_files_path -concept_annotation=$concept_annotation -ontologies=$ontologies -evaluation_files=$evaluation_files --gold_standard=$gold_standard




##FOR BIOBERT and LSTM-ELMO which need to be run on supercomputers (GPUs ideally)
biobert='BIOBERT'
lstm_elmo='LSTM_ELMO'

##BIOBERT algo - preprocess locally but run the rest on a supercomputer and then bring local
if [ $algos == $biobert ]; then
    ###creates the biobert test.tsv file and then run on supercomputer
    python3 eval_span_detection.py -ontologies=$ontologies -excluded_files=$evaluation_files -tokenized_file_path=$concept_recognition_path$tokenized_files -save_models_path=$concept_recognition_path$save_models_path -output_path=$concept_recognition_path$results_span_detection  -algos=$algos --gold_standard=$gold_standard  --pmcid_sentence_files_path=$pmcid_sentence_files_path --gs_tokenized_files=$concept_recognition_path$tokenized_files

    ## 1. Move ONTOLOGY_test.tsv (where ONTOLOGY are all the ontologies) file to supercomputer for predictions (Fiji)
    ## 2. On the supercomputer run fiji_run_eval_biobert.sh
    ## 3. Move the biobert models local to save for each ontology
    ## 4. Move label_test.txt and token_test.txt locally for each ontology
    ## 5. Run run_eval_biobert_pipepine_1.5.sh to process the results from BioBERT



##Run lstm-elmo on supercomputer because issues locally (ideally with GPUs)
elif [ $algos == $lstm_elmo ]; then
    tokenized_files_updated='Tokenized_Files'
    fiji_path='/Output_Folders/Evaluation_Files/'
    pmcid_sentence_files_path_updated='PMCID_files_sentences'


    ## 1. Move tokenized files to supercomputer (fiji)
    ## 2. Move sentence files (PMCID_files_sentences/) to supercomputer (fiji)
    ## 3. Run ONTOLOGY_fiji_LSTM_ELMO_span_detection.sh (ONTOLOGY is the ontologies of choice) on supercomputer
    ## 4. Move the LSTM_ELMO models locally to save
    ## 5. Move the /Output_Folders/Evaluation_Files/Results_span_detection/ files for LSTM_ELMO local: ONTOLOGY_LSTM_ELMO_model_weights_local_PMCARTICLE.txt where ONTOLOGY is the ontology of interest and PMCARTICLE is the PMC article ID
    ## 6. Run run_eval_LSTM_ELMO_pipeline_1.5.sh to process the results from LSTM_ELMO


## the rest of the span detection algorithms can be run locally
else
    ##runs the span detection models locally
    python3 eval_span_detection.py -ontologies=$ontologies -excluded_files=$evaluation_files -tokenized_file_path=$concept_recognition_path$tokenized_files -save_models_path=$concept_recognition_master_path$save_models_path -output_path=$concept_recognition_path$results_span_detection  -algos=$algos --gold_standard=$gold_standard  --pmcid_sentence_files_path=$pmcid_sentence_files_path --gs_tokenized_files=$concept_recognition_path$tokenized_files

    ##process the spans to run through concept normalization
#    python3 eval_preprocess_concept_norm_files.py -ontologies=$ontologies -results_span_detection_path=$concept_recognition_path$results_span_detection -concept_norm_files_path=$concept_recognition_path$concept_norm_files -evaluation_files=$evaluation_files

fi


##run the open_nmt to predict
#run_eval_open_nmt.sh
