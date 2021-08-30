import os
import argparse

import pandas as pd
import math




class SentenceGetter(object):
    def __init__(self, data):
        self.n_sent = 1
        self.data = data
        self.empty = False

        ##columns: PMCID	SENTENCE_NUM	SENTENCE_START	SENTENCE_END	WORD	POS_TAG	WORD_START	WORD_END
        agg_func = lambda s: [(w, p) for w, p in zip(s["WORD"].values.tolist(), s["POS_TAG"].values.tolist())]
        agg_func_rest = lambda t: [(a,b,c,d,e,f) for a,b,c,d,e,f in zip(t["PMCID"].values.tolist(),t["SENTENCE_NUM"].values.tolist(), t["SENTENCE_START"].values.tolist(), t["SENTENCE_END"].values.tolist(), t["WORD_START"].values.tolist(), t["WORD_END"].values.tolist())]

        # reindex in terms of the order of the sentences
        correct_indices = self.data.SENTENCE_NUM.unique()  # sentence nums in order (list)

        ##feature information
        self.grouped = self.data.groupby("SENTENCE_NUM", sort=False).apply(agg_func)
        # self.grouped.reindex(correct_indices, level="SENTENCE_NUM")
        self.sentences = [s for s in self.grouped]



        ##the rest of the sentence information
        self.grouped_rest = self.data.groupby("SENTENCE_NUM", sort=False).apply(agg_func_rest)
        # self.grouped_rest.reindex(correct_indices, level="SENTENCE_NUM")
        self.sentence_info = [t for t in self.grouped_rest]

        # print(self.sentences[290:])
        # print(self.sentence_info[290:])



        # raise Exception('HOLD!')





def load_predictions(biobert_prediction_results, ontology):
    all_predicted_info = [] #list of tuples of predicted stuff (token, predicted tag)


    ##pandas dataframe = changing special characters weirdly! ex: ('\tO\nnormal\tO\n', 'O')
    # predict_table = pd.read_table('%s%s/%s/%s' %(biobert_prediction_results, ontology, 'BIOBERT', 'NER_predict_conll.txt'), sep='\t')
    # for i, row in predict_table.iterrows():
    #     # if i==10:
    #     #     raise Exception('HOLD')
    #     # else:
    #     all_predicted_info += [(row['TOKEN'], row['PREDICTED'])]


    ##read it all in line by line
    with open('%s%s/%s/%s' %(biobert_prediction_results, ontology, 'BIOBERT', 'NER_predict_conll.txt'), 'r+') as prediction_file:
        next(prediction_file) #header
        for line in prediction_file:
            if len(line.strip('\n').split('\t')) == 1:
                pass
            else:
                (token, biotag) = line.strip('\n').split('\t')

                all_predicted_info += [(token, biotag)]


    return all_predicted_info




def load_data(tokenized_file_path, filename, all_sentences, all_sentence_info, excluded_files, ontology):

    all_pmcid_list = []
    valid_filename = False
    # for root, directories, filenames in os.walk(tokenized_file_path):
    #     for filename in sorted(filenames):

    # print(filename)
    #find the correct tokenized files to take
    # if filename.endswith('.pkl') and (filename.replace('.pkl', '') in excluded_files or filename.replace('.nxml.gz.pkl', '') in excluded_files):
    #     valid_filename = True
    # elif 'covid' == ontology.lower() and filename.endswith('.pkl'):
    #     valid_filename = True
    # elif filename.endswith('.nxml.gz.pkl') and excluded_files[0] == 'all':
    #     valid_filename = True
    # else:
    #     valid_filename = False
    #
    # ##take all the tokenized files
    # if valid_filename:
    # print(root)
    print(filename)
    all_pmcid_list += [filename.replace('.pkl','')]
    # print(filename)

    ##columns = ['PMCID', 'SENTENCE_NUM', 'SENTENCE_START', 'SENTENCE_END', 'WORD', 'POS_TAG', 'WORD_START', 'WORD_END']

    pmc_tokenized_file = pd.read_pickle(tokenized_file_path+filename)
    # print(pmc_tokenized_file[0])

    getter = SentenceGetter(pmc_tokenized_file)
    # print(len(getter.sentences))
    # print(type(getter.sentences))
    all_sentences += getter.sentences
    all_sentence_info += getter.sentence_info
    # print(len(all_sentences))
    return all_sentences, all_sentence_info, all_pmcid_list


def output_span_detection_results(all_pmcid_list, pmcid_starts_dict, output_path, filename, output_results, output_results_path):
    ##output the results in BIO format for concept normalization
    # ontology = filename.split('_')[0] ##error on GO_BP, GO_MF, GO_CC
    word_index = 0
    for pmcid in all_pmcid_list:
        # print('\tarticle:', pmcid)
        [pmcid_start_index, pmcid_end_index] = pmcid_starts_dict[pmcid]
        # print(pmcid_start_index, pmcid_end_index)

        # ##update the order so that it is in integer order of sentences not alphabetical order
        # updated_indices = {} #a dictionary of the correct order of sentence number: index -> information
        # max_sentence_num = 0
        # for o in output_results[pmcid_start_index:pmcid_end_index]:
        #     sentence_num = int(o[1].split('_')[-1])
        #     if updated_indices.get(sentence_num):
        #         updated_indices[sentence_num] += [o]
        #     else:
        #         updated_indices[sentence_num] = [o]
        #
        #     max_sentence_num = max(max_sentence_num, sentence_num)



        # if word_index == pmcid_starts_dict[pmcid]:
        #     continue
        # else:
        # print(output_results_path, pmcid)
        with open('%s_%s.txt' % (output_results_path, pmcid),'w+') as output_results_file:
            output_results_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
            'PMCID', 'SENTENCE_NUM', 'SENTENCE_START', 'SENTENCE_END', 'WORD', 'POS_TAG', 'WORD_START', 'WORD_END',
            'BIO_TAG', 'PMC_MENTION_ID', 'ONTOLOGY_CONCEPT_ID', 'ONTOLOGY_LABEL'))
            ##for each word in the sentence - output the information
            for o in output_results[pmcid_start_index:pmcid_end_index]:
            # for j in range(max_sentence_num+1):
            #     for o in updated_indices[j]:
                    # print(o)
                ##for column output the information
                for i, a in enumerate(o):
                    # print(a)
                    if i == len(o) - 1:
                        output_results_file.write('%s\n' % a)
                    else:
                        output_results_file.write('%s\t' % a)
                word_index += 1

                ##break here if the word_index is higher and we want to move to the next article
                if word_index == pmcid_end_index:
                    break
                else:
                    pass

def biobert_eval_results_span_detection(tokenized_file_path, ontology, biobert_prediction_results, output_path, excluded_files, algos, pmcid_sentence_file_path, ):



    ##read in all the prediction information - contains all information for all files
    all_predicted_info = load_predictions(biobert_prediction_results, ontology)

    api_index = 0

    print(tokenized_file_path)

    ##gather all sentence per file/pmcid!
    for root, directories, filenames in os.walk(tokenized_file_path):

        for filename in sorted(filenames):
            if (filename.endswith('.pkl') and (filename.replace('.pkl', '') in excluded_files)) or filename.replace('.nxml.gz.pkl','') in excluded_files or (filename.endswith('.nxml.gz.pkl') and excluded_files[0].lower() == 'all'):
                valid_filename = True
            elif 'covid' == ontology.lower() and filename.endswith('.pkl'):
                valid_filename = True
            else:
                valid_filename = False

            ##take all the tokenized files
            if valid_filename:
                pmcid = filename.replace('.pkl', '')
                # print('got here!')

                ##initialize all sentences
                all_sentences = []
                all_sentence_info = []

                ##load the data for all sentences in the evaluation data - loop in load_data
                all_sentences, all_sentence_info, all_pmcid_list = load_data(tokenized_file_path, filename, all_sentences, all_sentence_info, excluded_files, ontology)
                # print(all_sentences[0], all_sentence_info[0], all_pmcid_list[0])
                print('NUMBER OF SENTENCES TO EVALUATE ON:', len(all_sentences))

                if len(all_sentences) != len(all_sentence_info):
                    raise Exception('ERROR WITH GATHERING SENTENCE INFORMATION!')
                else:
                    pass

                # print(all_sentences[0])
                # print(all_sentence_info[0])




                ##output the results span detection file
                with open('%s%s/%s_%s_%s.txt' % (output_path, ontology, ontology, 'biobert_model_local', pmcid), 'w+') as output_results_file:
                    # print(output_results_file)
                    #header
                    output_results_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
                        'PMCID', 'SENTENCE_NUM', 'SENTENCE_START', 'SENTENCE_END', 'WORD', 'POS_TAG', 'WORD_START', 'WORD_END', 'BIO_TAG', 'PMC_MENTION_ID', 'ONTOLOGY_CONCEPT_ID', 'ONTOLOGY_LABEL'))


                    ##output the information per line
                    #all_sentences - word, pos_tag
                    #all_sentences_info - pmcid, sentence_num, sentence_start, sentence_end, word_start, word_end
                    #all_predicted_info - word, biotag
                    for a, s in enumerate(all_sentences):
                        for b, w in enumerate(s):



                            #check that the words are the same for sentences and predicted
                            if w[0] != all_predicted_info[api_index][0]:
                                # print(w[0], type(w[0]))
                                # print(all_predicted_info[api_index][0], type(all_predicted_info[api_index][0]))
                                print(all_predicted_info[api_index])
                                print(w)
                                raise Exception('ERROR WITH PREDICTION WORD AND SENTENCE WORD!')
                                # try:
                                #     if math.isnan(all_predicted_info[api_index][0]) and w[0] == 'null':
                                #         print('got here')
                                #         pass
                                # except TypeError:
                                #     if all_predicted_info[api_index][0] in w[0]:
                                #         pass
                                #
                                #     else:
                                #         # print('all sentence then predicted')
                                #         # print(w[0], type(w[0]))
                                #         # print(all_predicted_info[api_index][0], type(all_predicted_info[api_index][0]))
                                #         raise Exception('ERROR WITH PREDICTION WORD AND SENTENCE WORD!')
                            else:
                                pass

                            output_results_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' %(all_sentence_info[a][b][0], all_sentence_info[a][b][1], all_sentence_info[a][b][2], all_sentence_info[a][b][3], w[0], w[1], all_sentence_info[a][b][4], all_sentence_info[a][b][5], all_predicted_info[api_index][1], None, None, None))

                            api_index += 1








if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-ontologies', type=str, help='a list of ontologies to use delimited with ,')
    parser.add_argument('-excluded_files', type=str, help='a list of excluded files delimited with ,')
    parser.add_argument('-tokenized_file_path', type=str, help='the file path for the tokenized files')
    parser.add_argument('-biobert_prediction_results', type=str, help='the file path to the biobert_prediction path')

    parser.add_argument('-output_path', type=str, help='the file path to the results of the span detection models')



    parser.add_argument('-algos', type=str,
                        help='a list of algorithms to evaluate with models delimited with , and all uppercase')

    #OPTIONAL = DEFAULT IS NONE
    parser.add_argument('--gold_standard', type=str, help='True if gold standard available else false', default=None)
    parser.add_argument('--pmcid_sentence_files_path', type=str,
                        help='the file path to the pmicd sentence files for the ontologies', default=None)
    parser.add_argument('--all_lcs_path', type=str, help='the file path to the lexical cues for the ignorance ontology', default=None)

    args = parser.parse_args()

    ontologies = args.ontologies.split(',')
    excluded_files = args.excluded_files.split(',')
    algos = args.algos.split(',')

    for ontology in ontologies:
        # all_predicted_info = load_predictions(args.biobert_prediction_results, ontology)
        print('Ontology:', ontology)
        biobert_eval_results_span_detection(args.tokenized_file_path, ontology, args.biobert_prediction_results, args.output_path, excluded_files, algos, args.pmcid_sentence_files_path)

    print('PROGRESS: FINISHED CONVERTING BIOBERT OUTPUT TO DATAFRAME!')
