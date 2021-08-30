#!/usr/bin/env bash


craft_path='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/Negacy_seq_2_seq_NER_model/ConceptRecognition/CRAFT-3.1.3/' ##NOT USED

concept_recognition_master_path='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Concept-Recognition-as-Translation-master/'


eval_path='/Output_Folders/Evaluation_Files/'

##folders for all outputs within the evaluation files
output_folders='Output_Folders/'
concept_system_output='concept_system_output/'
article_folder='Articles/' #want files.txt
tokenized_files='Tokenized_Files/'
save_models_path='Models/SPAN_DETECTION/'
results_span_detection='Results_span_detection/'
concept_norm_files='Concept_Norm_Files/'
pmcid_sentence_files_path='PMCID_files_sentences/'
concept_annotation='concept-annotation/' ##not used!

##list of ontologies that have annotations to preproess
ontologies='full_unknown,explicit_question,incomplete_evidence,probable_understanding,superficial_relationship,future_work,future_prediction,important_consideration,anomaly_curious_finding,alternative_options_controversy,difficult_task,problem_complication,question_answered_by_this_work,0_all_combined,1_binary_combined'
ontologies='0_all_combined,1_binary_combined'


evaluation_files="all"

gold_standard='True'

algos='BIOBERT' #CRF, LSTM, LSTM_CRF, CHAR_EMBEDDINGS, LSTM_ELMO, BIOBERT


all_lcs_path='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Ontologies/Ontology_Of_Ignorance_all_cues_2020-03-27.txt' #NOT USED



#FOR BIOBERT
biobert='BIOBERT'
if [ $algos == $biobert ]; then
#    ##move test.tsv file to fiji for predictions
#    prediction_file='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/Negacy_seq_2_seq_NER_model/ConceptRecognition/Evaluation_Files/Tokenized_Files/BIOBERT'
#    scp $prediction_file/test.tsv mabo1182@fiji.colorado.edu:/Users/mabo1182/negacy_project/Evaluation_Files/Tokenized_Files/BIOBERT/
#
#    #GO TO FIJI_RUN_EVAL_BIOBERT!
#    ##TODO: biobert run classification algorithm - fiji_run_eval_biobert.sh on fiji!!!
#    #sbatch GPU_run_fiji_eval_biobert.sbatch - runs fiji_run_eval_biobert.sh


    ##BRING ALL OUTPUT LOCALLY FOR BIOBERT
    declare -a arr=('full_unknown' 'explicit_question' 'incomplete_evidence' 'probable_understanding' 'superficial_relationship' 'future_work' 'future_prediction' 'important_consideration' 'anomaly_curious_finding' 'alternative_options_controversy' 'difficult_task' 'problem_complication' 'question_answered_by_this_work' '0_all_combined' '1_binary_combined')

    declare -a arr=('0_all_combined' '1_binary_combined')
#
#    ##loop over each ontology and run the corresponding model
    fiji_results_span_detection='/Users/mabo1182/epistemic_classification/Output_Folders/Results_span_detection/'
    fiji_tokenized_files='/Users/mabo1182/epistemic_classification/Output_Folders/Tokenized_Files/'
    biobert_training='BIOBERT_TRAINING'
    biobert='/BIOBERT'
    local_results='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Concept-Recognition-as-Translation-master/Output_Folders/Results_span_detection/'

    for i in "${arr[@]}"
    do
        ##results for training
        echo $i
        results_path=$fiji_results_span_detection$i$biobert
        local_path=$local_results$i$biobert
#        scp mabo1182@fiji.colorado.edu:$results_path/*_test.txt* $local_path
        scp mabo1182@fiji.colorado.edu:$results_path/token_test.txt $local_path
        scp mabo1182@fiji.colorado.edu:$results_path/label_test.txt $local_path
    done

    ###ner_detokenize_updated for predictions only
    #updated detokenize to put all stuff back together to CONLL format!

    biotags='B,I,O-,O' #ordered for importance
    gold_standard='false'
    gold_standard='true'
    true='true'

    declare -a ont=('full_unknown' 'explicit_question' 'incomplete_evidence' 'probable_understanding' 'superficial_relationship' 'future_work' 'future_prediction' 'important_consideration' 'anomaly_curious_finding' 'alternative_options_controversy' 'difficult_task' 'problem_complication' 'question_answered_by_this_work' '0_all_combined' '1_binary_combined')

    declare -a ont=('0_all_combined' '1_binary_combined')


    for i in "${ont[@]}"
    do
        echo "$i"
        tokenized_files='Tokenized_Files'
        results_span_detection='Results_span_detection/'
        NER_DIR=$concept_recognition_master_path$output_folders$tokenized_files$biobert
        OUTPUT_DIR=$concept_recognition_master_path$output_folders$results_span_detection$i$biobert

        python3 biobert_ner_detokenize_updated.py --token_test_path=$OUTPUT_DIR/token_test.txt --label_test_path=$OUTPUT_DIR/label_test.txt --answer_path=$NER_DIR/test.tsv --output_dir=$OUTPUT_DIR --biotags=$biotags --gold_standard=$gold_standard

        echo 'DONE WITH TEST.TSV'


        ##if gold standard then we also want the gold standard information using the ontology_test.tsv files
        if [ $gold_standard == $true ]; then
            ont_test='_test.tsv'
            python3 biobert_ner_detokenize_updated.py --token_test_path=$OUTPUT_DIR/token_test.txt --label_test_path=$OUTPUT_DIR/label_test.txt --answer_path=$NER_DIR/$i$ont_test --output_dir=$OUTPUT_DIR --biotags=$biotags --gold_standard=$gold_standard


            ##classification report if gold standard

            python3 biobert_classification_report.py --ner_conll_results_path=$OUTPUT_DIR/ --biotags=$biotags --ontology=$i --output_path=$OUTPUT_DIR/ --gold_standard=$gold_standard

            #copy the classification report to the main results with ontology name
            biobert_class_report='_biobert_local_eval_files_classification_report_full.txt'

            cp $OUTPUT_DIR/biobert_classification_report.txt $concept_recognition_master_path$output_folders$results_span_detection$i/$i$biobert_class_report



        fi

    done


    tokenized_files='Tokenized_Files/'
    results_span_detection='Results_span_detection/'
    biobert_prediction_results=$concept_recognition_master_path$output_folders$results_span_detection
    ontologies='1_binary_combined'

    ##create the evaluation dataframe!
    python3 biobert_eval_dataframe_output.py -ontologies=$ontologies -excluded_files=$evaluation_files -tokenized_file_path=$concept_recognition_master_path$output_folders$tokenized_files -biobert_prediction_results=$biobert_prediction_results -output_path=$biobert_prediction_results -algos=$algos --pmcid_sentence_files_path=$pmcid_sentence_files_path

fi





##preprocess to get all the concepts for the next steps - preprocess so we can see all the terms for all ontologies

ontologies='1_binary_combined'
python3 eval_preprocess_concept_norm_files.py -ontologies=$ontologies -results_span_detection_path=$concept_recognition_master_path$output_folders$results_span_detection -concept_norm_files_path=$concept_recognition_master_path$output_folders$concept_norm_files -evaluation_files=$evaluation_files



##run the open_nmt to predict
#run_eval_open_nmt.sh
