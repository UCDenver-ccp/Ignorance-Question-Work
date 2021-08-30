import argparse
import os
import pickle


def create_ontology_dict(ontology_cues_file_path, output_path):

    ontology_cues_dict = {} #lexical cue -> [synonym, ignorance_type] #all lowercase


    ##get all the dictionary information
    with open(ontology_cues_file_path, 'r+') as ontology_cues_file:
        next(ontology_cues_file) ##first line is headers: LEXICAL CUE	SYNONYMS	IGNORANCE TYPE
        for line in ontology_cues_file:
            lexical_cue, synonym, ignorance_type = line.strip('\n').split('\t')
            ##all lexical cues should be unique by definition - so if not raise error
            if ontology_cues_dict.get(lexical_cue):
                print('current line:', lexical_cue, synonym, ignorance_type)
                print('current dict info:', ontology_cues_dict[lexical_cue])
                raise Exception('ERROR: there should be no duplicates of lexical cues!!')
            ##collect all the cues, synonyms, and ignorance type for the dictionary
            else:
                ontology_cues_dict[lexical_cue] = [synonym, ignorance_type]


    ##save the dictionary
    output_dict_file = open('%s%s.pkl' %(output_path, 'Ontology_Of_Ignorance_dictionary'), 'wb+')
    pickle.dump(ontology_cues_dict, output_dict_file)
    output_dict_file.close()

    return ontology_cues_dict



def normalize_src_file(ontology, ontology_cues_dict, concept_norm_path, output_path):
    ##normalize all that we can and count what we cannot normalize - need to do lowercase and regex

    ##count of no matches between the predictions and the dictionary
    overall_counts_per_model_dict = {} #model name -> [total_annotations, no match count]

    # overall_count_no_matches = 0 #TODO: src file combines all algos so maybe want to split the count by that (using link file in future)


    ##output file
    with open('%s%s/%s_model-dict_pred.txt' %(output_path, ontology, ontology), 'w+') as output_file, open('%s%s/%s_combo_src_file.txt' %(concept_norm_path, ontology, ontology), 'r+') as src_file, open('%s%s/%s_combo_link_file.txt' %(concept_norm_path, ontology, ontology), 'r+') as link_file:
        combo_link_info = link_file.readlines() #list of all the info - model in last column split on '_PMC'

        ##no headers in src file and thus none in output file either
        for i, line in enumerate(src_file):
            model_name = combo_link_info[i].split('\t')[-1].split('_PMC')[0]
            # print(combo_link_info[i])
            # print(model_name)
            # raise Exception('hold')
            ##count the totals
            if overall_counts_per_model_dict.get(model_name):
                overall_counts_per_model_dict[model_name][0] += 1
            else:
                overall_counts_per_model_dict[model_name] = [1,0]

            input = line.strip('\n') #spaces and capitalization
            input_check = input.lower().replace(' ... ', '...').replace('... ', '...').replace(' ...','...').replace(' ','_')
            ##see if we can find the input in the ontology_cues_dict
            if ontology_cues_dict.get(input_check):
                output_file.write('%s\n' %(ontology_cues_dict[input_check][1])) #output the ignornace type specifically as the normalization
            else:
                print('ONTOLOGY DICT FAIL!')
                print(i)
                print(input)
                print(input_check)
                overall_counts_per_model_dict[model_name][1] += 1 #count no matches
                # overall_count_no_matches += 1
                output_file.write('\n') ##leave it blank if no match

                # raise Exception('HOLD!')
    # total_annotations = i+1
    # print('total annotations:', i+1)
    # print('total no matches:', overall_count_no_matches)
    return overall_counts_per_model_dict


def full_system_output(ontology, filename, concept_norm_results_path, concept_norm_link_path, output_file_path):
    ##not char files!

    ##read in the concept_norm_output_file
    with open('%s%s/%s' %(concept_norm_results_path, ontology, filename), 'r+') as concept_norm_results_file:
        concept_norm_results = concept_norm_results_file.read().split('\n')

    ##read in the link file:
    with open('%s%s/%s_%s' %(concept_norm_link_path, ontology, ontology, 'combo_link_file.txt'), 'r+') as combo_link_file:
        combo_link_info = combo_link_file.read().split('\n')


    ##check they are the same length
    if len(concept_norm_results) != len(combo_link_info):
        print(filename)
        print(len(concept_norm_results))
        print(len(combo_link_info))
        raise Exception('ERROR WITH CONCEPT NORMALIZATION OUTPUT MATCHING LINK FILE!')
    else:
        ##output the bionlp files

        for i,c in enumerate(concept_norm_results):
            # print(i,c)
            if c:
                ont_ID = c.replace(' ', '')
                # print(ont_ID)
                # print(combo_link_info[i])
                [pmc_mention_id, sentence_num, word_indices, word, span_model] = combo_link_info[i].split('\t')
                # print(span_model)
                # print(word_indices)
                ##update the word_indices:
                if ';' in word_indices:

                    # print(word_indices)
                    updated_word_indices = ''

                    split_word = word.split(' ')

                    word_indices_list = word_indices.split(';')
                    word_indices_list = [w.split(' ') for w in word_indices_list]

                    if '...' not in split_word: #no discontinuity
                        ##take the first start and last end to get the concept indices
                        updated_word_indices = '%s %s' %(word_indices_list[0][0], word_indices_list[-1][1])
                    else:
                        discontinuity_indices = [i for i, x in enumerate(split_word) if x == '...']
                        for (j, (s, e)) in enumerate(word_indices_list):
                            s = int(s)
                            e = int(e)
                            if j == 0:
                                updated_word_indices += '%s ' % s  # start value
                                current_e = e
                            else:
                                ##check if discontinuity
                                if j in discontinuity_indices:
                                    updated_word_indices += '%s;%s ' % (current_e, s)
                                    current_e = e
                                else:
                                    current_e = e

                        updated_word_indices += '%s' % current_e

                    ##check that the discontinuous is correct: '...' = ';' - changed ' ... ' to ' ...'
                    if (' ... ' in word and ';' not in updated_word_indices) or (';' in updated_word_indices and ' ...' not in word):
                        print(filename)
                        print('WEIRD DISCONTINUITY ISSUES:', word, updated_word_indices)
                        raise Exception('ERROR WITH DISCONTINUITY AND UPDATED WORD INDICES!')
                    else:
                        pass
                else:
                    updated_word_indices = word_indices
                    # print(updated_word_indices)


                ##output the concept_system_output files per models
                with open('%s%s/%s.bionlp' %(output_file_path, ontology, span_model), 'a') as output_file:
                    output_file.write('T%s\t%s %s\t%s\n' %(i, ont_ID, updated_word_indices, word))


            else:
                # print('none',c)
                pass


def evaluate_all_models(concept_system_output_path, gold_standard_path, ontology, evaluation_files, evaluation_output_file):

    ##read in the gold_standard output
    all_gs_bionlp_dict = {} #pmc_id -> gs_bionlp_dict
    # print(gold_standard_path) -
    if len(gold_standard_path.split('/')) == 2: #'gold_standard/'.split('/') = ['gold_standard', ''] - length 2
        gold_standard_path_final = '%s%s/%s' % (concept_system_output_path, ontology, gold_standard_path)
    else:
        gold_standard_path_final = '%s%s/' %(gold_standard_path, ontology.lower())

    # print('gold standard path final', gold_standard_path_final)
    for root, directories, filenames in os.walk(gold_standard_path_final):
        for filename in sorted(filenames):
            if filename.endswith('.bionlp') and (filename.replace('.bionlp','') in evaluation_files or evaluation_files == 'all'):
                gs_bionlp_dict = {} #(word_indices, spanned_text) -> [ont_ID, T#]
                with open(root+filename, 'r+') as gs_bionlp_file:
                    for line in gs_bionlp_file:
                        # print(line)
                        if line.startswith('T'):
                            [T_num, ont_info, spanned_text] = line.split('\t')
                            [ont_ID, word_indices] = [ont_info.split(' ')[0], ont_info.split(ont_info.split(' ')[0])[1][1:]]
                            # print(T_num, ont_ID, word_indices, spanned_text)
                            if gs_bionlp_dict.get((word_indices, spanned_text)):
                                ##TODO: duplicate from annotations but not an actual issue - get rid of duplicates in future
                                if ont_ID == gs_bionlp_dict[(word_indices, spanned_text)][0]:
                                    ##duplicate - same exact everything else
                                    pass

                                else:
                                    ##TODO: overlaps
                                    print(filename)
                                    print('ISSUE HERE!', line) #TODO!!
                                    print(gs_bionlp_dict[(word_indices, spanned_text)])
                                    gs_bionlp_dict[(word_indices, spanned_text)] += [ont_ID, T_num] ##TODO: adding the info for now
                                    print(gs_bionlp_dict[(word_indices, spanned_text)])
                                    # pass
                                    # raise Exception('ERROR WITH MAKING SURE THE ONTOLOGY CONCEPTS LABELED ARE UNIQUE PER ONTOLOGY!')
                            else:
                                gs_bionlp_dict[(word_indices, spanned_text)] = [ont_ID, T_num]
                        else:
                            print('WEIRD LINES:', filename)

                    print('total gold standard annotations:', len(gs_bionlp_dict.keys()))
                    # total_gs_annotations += len(gs_bionlp_dict.keys())
                    all_gs_bionlp_dict[filename.replace('.bionlp','')] = [gs_bionlp_dict, len(gs_bionlp_dict.keys())]


    ##set up the output for the summary of the evaluation
    full_output_file = open('%s%s/0_%s_full_system_evaluation_summary.txt' %(concept_system_output_path, ontology, ontology), 'w')
    full_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' %('MODEL', 'TOTAL GOLD STANDARD ANNOTS', 'TOTAL PREDICTED ANNOTS', 'DUPLICATE COUNT', 'TRUE POSITIVES', 'FALSE POSITIVES', 'FALSE NEGATIVES', 'SUBSTITUTIONS', 'PRECISION', 'RECALL', 'F-MEASURE', 'SLOT ERROR RATE'))

    # print('PROGRESS: FULL ')



    ##read in the model output files to compare to the gold standard dictionaries above
    for root_p, directories_p, filenames_p in os.walk('%s%s/' % (concept_system_output_path, ontology)):
        for filename_p in sorted(filenames_p):
            if filename_p.endswith('.bionlp') and 'model' in filename_p:
                # print(filename_p)
                ##evaluation metrics:
                tp = 0
                fp = 0
                fn = 0  # all the ones left in the gs dict but not used
                tn = 0
                substitutions = 0
                total_predicted_annotations = 0

                current_predicted_annotations = []
                duplicate_count = 0

                current_total_annotations = 0

                with open(root_p+filename_p, 'r') as model_bionlp_file:
                    for i, line in enumerate(model_bionlp_file):
                        if line:
                            # print(line)
                            [T_num_p, ont_info_p, spanned_text_p] = line.split('\t')
                            [ont_ID_p, word_indices_p] = [ont_info_p.split(' ')[0], ont_info_p.split(ont_info_p.split(' ')[0])[1][1:]]
                            # print(T_num_p, ont_ID_p, word_indices_p, spanned_text_p)

                            ##check if done or duplicate
                            if [ont_ID_p, word_indices_p, spanned_text_p] in current_predicted_annotations:
                                duplicate_count += 1
                            else:

                                current_predicted_annotations += [[ont_ID_p, word_indices_p, spanned_text_p]]
                                # print(all_gs_bionlp_dict)

                                ##check if the predicted are in the bionlp dictionary
                                if all_gs_bionlp_dict.get(filename_p.replace('.bionlp','').split('_')[-1]):
                                    [current_gs_bionlp_dict, current_total_annotations] = all_gs_bionlp_dict[filename_p.replace('.bionlp','').split('_')[-1]]
                                    if current_gs_bionlp_dict.get((word_indices_p, spanned_text_p)):
                                        ##TODO changed to allow for multiple answers:
                                        # if current_gs_bionlp_dict[(word_indices_p, spanned_text_p)][0] == ont_ID_p:
                                        if ont_ID_p in current_gs_bionlp_dict[(word_indices_p, spanned_text_p)]:
                                            # print('GOT HERE!!')
                                            tp += 1
                                        else:
                                            ##substitution!
                                            substitutions += 1
                                            # print(word_indices_p, spanned_text_p, ont_ID_p)
                                            # raise Exception('ERROR WITH ONTOLOGY ID')
                                    else:
                                        fp += 1
                                ##there are no annotations to it at all so all are false positives!
                                else:
                                    fp += 1

                                total_predicted_annotations = i+1
                    fn = current_total_annotations - tp
                    print('total duplicates', duplicate_count)
                    print(current_total_annotations, total_predicted_annotations - duplicate_count, tp, fp, fn)



                    if tp != 0:
                        precision = float(tp) / float(tp + fp)
                        recall = float(tp)/float(tp+fn)
                        SER = float(substitutions + fp + fn) / float(tp + substitutions + fn)  # https://pdfs.semanticscholar.org/451b/61b390b86ae5629a21461d4c619ea34046e0.pdf - want a smaller number
                    else:
                        precision = 0
                        recall = 0
                        SER = 1 #the higher the number the worse it is
                    if precision+recall != 0:
                        f_measure = float(2*precision*recall)/float(precision+recall)
                    elif precision+recall == 0 and tp == 0:
                        f_measure = 0
                    else:
                        raise Exception('ERROR WITH PRECISION AND RECALL IN RELATION TO TRUE POSITIVES!')




                    ##'MODEL', 'TOTAL GOLD STANDARD ANNOTS', 'TOTAL PREDICTED ANNOTS', 'DUPLICATE COUNT', 'TRUE POSITIVES', 'FALSE POSITIVES', 'FALSE NEGATIVES', 'SUBSTITUTIONS', 'PRECISION', 'RECALL', 'F-MEASURE', 'SLOT ERROR RATE'
                    full_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\t%.2f\t%.2f\n' %(filename_p.replace('.bionlp', ''), current_total_annotations, total_predicted_annotations-duplicate_count, duplicate_count, tp, fp, fn, substitutions, precision, recall, f_measure, SER))

                    evaluation_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\t%.2f\t%.2f\n' %(ontology, filename_p.replace('.bionlp', ''), current_total_annotations, total_predicted_annotations-duplicate_count, duplicate_count, tp, fp, fn, substitutions, precision, recall, f_measure, SER))





if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-ontology_cues_file_path', type=str, help='the file path to all the ontology cues')
    parser.add_argument('-output_path_cue_dict', type=str,
                        help='the file path to output the dictionary to save for future use')
    parser.add_argument('-ontologies', type=str, help='list of ontologies of interest delimited by , with no space')
    parser.add_argument('-concept_norm_path', type=str, help='the file path to the concept norm files')
    parser.add_argument('-results_concept_norm_path', type=str, help='the file path to the results for concept norm files')
    parser.add_argument('-concept_norm_link_path', type=str,
                        help='the file path to the concept norm files where the link file is')
    parser.add_argument('-concept_system_output', type=str, help='the file path to the concept system output')

    parser.add_argument('-gold_standard_path', type=str,
                        help='the folder to the gold standard annotations for evaluation')
    parser.add_argument('-evaluation_files', type=str, help='a list of the evaluation files delimited by , or all')
    parser.add_argument('-evaluate', type=str, help='true if evaluate the models given a gold standard else false')
    args = parser.parse_args()

    ontologies = args.ontologies.split(',')

    ##grab all ontology cues from the dictionary for matching
    ontology_cues_dict = create_ontology_dict(args.ontology_cues_file_path, args.output_path_cue_dict)

    evaluation_output_path = args.concept_system_output + '0_final_summary_output.txt'

    evaluation_output_file = open(evaluation_output_path, 'w+')
    evaluation_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
        'ONTOLOGY', 'MODEL', 'TOTAL GOLD STANDARD ANNOTS', 'TOTAL PREDICTED ANNOTS', 'DUPLICATE COUNT',
        'TRUE POSITIVES',
        'FALSE POSITIVES', 'FALSE NEGATIVES', 'SUBSTITUTIONS', 'PRECISION', 'RECALL', 'F-MEASURE', 'SLOT ERROR RATE'))

    match_summary_file = open('%s%s' %(args.concept_system_output, '0_match_summary.txt'), 'w+')
    match_summary_file.write('%s\t%s\t%s\t%s\n' %('ONTOLOGY', 'MODEL', 'TOTAL ANNOTATIONS', 'TOTAL DICTIONARY NO MATCHES'))

    ##normalize for each ontology
    for ontology in ontologies:
        overall_counts_per_model_dict = normalize_src_file(ontology, ontology_cues_dict, args.concept_norm_path, args.results_concept_norm_path) ##model name -> [total_annotations, no match count]

        for model_name in overall_counts_per_model_dict.keys():
            # print(model_name)
            # print(model_name.split(ontology+'_')[-1])
            match_summary_file.write('%s\t%s\t%s\t%s\n' %(ontology, model_name.split(ontology+'_')[-1], overall_counts_per_model_dict[model_name][0], overall_counts_per_model_dict[model_name][1]))

        # raise Exception('hold')


        ##delete all previous model runs and evaluation data
        concept_system_directory = os.listdir('%s%s/' % (args.concept_system_output, ontology))
        for prev_bionlp in concept_system_directory:
            if prev_bionlp.endswith('.bionlp'):
                os.remove(os.path.join('%s%s/' % (args.concept_system_output, ontology), prev_bionlp))

        ##TODO: output normalization files as the bionlp format
        for root, directories, filenames in os.walk('%s%s/' % (args.results_concept_norm_path, ontology)):
            for filename in sorted(filenames):
                # if file_num < max_files:
                if filename.endswith('pred.txt'):
                    full_system_output(ontology, filename, args.results_concept_norm_path, args.concept_norm_link_path,
                                       args.concept_system_output)
                    print('PROGRESS: FULL SYSTEM OUTPUT EVALUATED FOR:', filename)

        if args.evaluate.lower() == 'true':
            print('PROGRESS: EVALUATING MODELS!')
            evaluate_all_models(args.concept_system_output, args.gold_standard_path, ontology, args.evaluation_files, evaluation_output_file)
        else:
            pass

