#!/usr/bin/env bash

ontology_cues_file_path='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Ontologies/Ontology_Of_Ignorance_all_cues_2020-08-25.txt'

ontology_cue_dict_output_path='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Ontologies/'

ontologies_to_combine='full_unknown,explicit_question,incomplete_evidence,probable_understanding,superficial_relationship,future_work,future_prediction,important_consideration,anomaly_curious_finding,alternative_options_controversy,difficult_task,problem_complication,question_answered_by_this_work'

#ontologies='0_all_combined,1_binary_combined'


##need to normalize the binary combined specifically as well
ontologies='1_binary_combined'

concept_norm_path='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Concept-Recognition-as-Translation-master/Output_Folders/Concept_Norm_Files/'

results_concept_norm_path='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Concept-Recognition-as-Translation-master/Output_Folders/Results_concept_norm_files/'

concept_system_output='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Concept-Recognition-as-Translation-master/Output_Folders/concept_system_output/'


##combine all gold standard annotations into one
input_path_extension='gold_standard/'
all_article_list_file='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Concept-Recognition-as-Translation-master/Output_Folders/Tokenized_Files/all_article_list.txt'
evaluation_files='all'
evaluate='true'

##combine all files for general gold standard
python3 combine_all_bionlp_annotations.py -ontologies_to_combine=$ontologies_to_combine  -all_article_list_file=$all_article_list_file -input_path=$concept_system_output --input_path_extension=$input_path_extension -output_path=$concept_system_output$ontologies/

all_combined='0_all_combined'

##also put it in the 0_all_combined ontology folder
python3 combine_all_bionlp_annotations.py -ontologies_to_combine=$ontologies_to_combine  -all_article_list_file=$all_article_list_file -input_path=$concept_system_output --input_path_extension=$input_path_extension -output_path=$concept_system_output$all_combined/



##dictionary normalize for binary - ##TODO: need stats!
python3 dictionary_normalization.py -ontology_cues_file_path=$ontology_cues_file_path -output_path_cue_dict=$ontology_cue_dict_output_path -ontologies=$ontologies -concept_norm_path=$concept_norm_path -results_concept_norm_path=$results_concept_norm_path -concept_norm_link_path=$concept_norm_path -concept_system_output=$concept_system_output -gold_standard_path=$input_path_extension -evaluation_files=$evaluation_files -evaluate=$evaluate


