import os
# import re
# import gzip
# import argparse
# import numpy as np
import nltk
# nltk.download()
import nltk.data
# import sys
# import termcolor
# from termcolor import colored, cprint
# from xml.etree import ElementTree as ET
# import xml.etree.ElementTree as ET
# from xml.dom import minidom
# import multiprocessing as mp
# import functools
# import resource, sys
# from emoji import UNICODE_EMOJI
# import demoji
from nltk.tokenize import sent_tokenize, word_tokenize
import pandas as pd
# from nltk.tokenize import TreebankWordTokenizer
# from nltk.tokenize import WhitespaceTokenizer
from nltk.tokenize import WordPunctTokenizer
# import copy
# import json
import pickle
import argparse



def sentence_tokenize(pmc_doc_text, pmc_doc_file):
    sentence_list = sent_tokenize(pmc_doc_text) #list of sentences (placement in the list is the sentence number
    sentence_list_indicies = [] #tuples of start and stop
    index = None
    for t in range(len(sentence_list)):
        s = sentence_list[t]

        if sentence_list_indicies:


            start = pmc_doc_text.index(s, sentence_list_indicies[-1][1]) #the sentence has to start after the last one added ended
            end = start + len(s)


            ##combining 2 sentences because some concepts span 2 sentences which is a problem
            if pmc_doc_file in  ['12585968.txt', '14723793.txt']:
                if s.endswith('Genic.') and start == 6553:
                    # print('got here')
                    index = t
                elif 'Sm.' in s and start == 5248:
                    index = t


        else:
            start = pmc_doc_text.index(s)
            end = start + len(s)

        sentence_list_indicies += [(start, end)]

    if index is not None:
        sentence_combo = sentence_list[index] + ' ' +  sentence_list[index+1]
        # print(sentence_combo)
        sentence_indicies_combo = [(sentence_list_indicies[index][0], sentence_list_indicies[index+1][1])]
        # print(sentence_indicies_combo)
        # print(len(sentence_list), len(sentence_list_indicies))

        sentence_list = sentence_list[:index] + [sentence_combo] + sentence_list[index+2:]
        sentence_list_indicies = sentence_list_indicies[:index] + sentence_indicies_combo + sentence_list_indicies[index+2:]

        # print('final', len(sentence_list), len(sentence_list_indicies))


    if len(sentence_list_indicies) != len(sentence_list):
        raise Exception('ERROR WITH SENTENCE INDICIES!')

    return sentence_list, sentence_list_indicies


def word_tokenize_sentences(pmcid, sentence, sentence_indicies, sentence_number, pmc_doc_text):
    # print(sentence_number)

    all_sent_word_info = []

    # word_indicies = list(TreebankWordTokenizer().span_tokenize(sentence)) #from the sentence starting so need add the start of the sentence
    word_indicies = list(WordPunctTokenizer().span_tokenize(sentence))  # from the sentence starting so need add the start of the sentence

    # print(word_indicies)
    # print(sentence_indicies)
    sentence_start = int(sentence_indicies[0])
    sentence_end = int(sentence_indicies[1])




    ##FINAL DOCUMENT WORD INDICIES
    doc_word_indicies = []
    for (s,e) in word_indicies:
        doc_word_indicies += [(sentence_start + s, sentence_start + e)]

    if doc_word_indicies[-1][1] != sentence_end:
        print(sentence_end, doc_word_indicies[-1][1])
        raise Exception("ERROR WITH UPDATING THE WORD INDICIES TO BE FOR THE WHOLE DOCUMENT USING THE SENTENCE STARTS!")

    ##FINAL WORD TOKENS
    # word_tokens = list(TreebankWordTokenizer().tokenize(sentence))
    word_tokens = list(WordPunctTokenizer().tokenize(sentence))
    # print(word_tokens)


    if len(doc_word_indicies) != len(word_tokens):
        raise Exception('ERROR WITH WORD TOKENIZING INTO WORDS AND INDICIES')


    # print(word_tokens)

    ##FINAL POS TAGS
    word_tokens_pos_tags = nltk.pos_tag(word_tokens) #list of tuples of [(word, POS)]


    if len(word_tokens) != len(word_tokens_pos_tags):
        raise Exception("ERROR WITH WORD TOKENIZING AND POS TAGS!")


    ##CHECK THAT THE SPANS ARE CORRECT if they have no concepts in it:
    else:
        for i in range(len(doc_word_indicies)):
            (s1, e1) = doc_word_indicies[i]

            # TODO: errors with weird characters so only checking if its alpha!
            if pmc_doc_text[s1:e1].isalpha() and pmc_doc_text[s1:e1] != word_tokens[i]:
                print(pmc_doc_text[s1:e1], word_tokens[i])
                raise Exception("ERROR WITH CHECKING THAT THE SPANS PULL OUT THE CORRECT TEXT!")

            (word, pos_tag) = word_tokens_pos_tags[i]
            ## all_sent_word_info:  [[pmcid, sentence_number, sentence_start, sentence_end, word, pos_tag, word_start, word_end]]
            all_sent_word_info += [[pmcid, '%s_%s' %(pmcid,sentence_number), sentence_start, sentence_end, word, pos_tag, s1, e1]]





    ##check that everything is the same length - maybe won't be if i only change the ID
    if len(all_sent_word_info) != len(word_tokens):
        print(len(all_sent_word_info), len(word_tokens))
        raise Exception('ERROR WITH KEEPING TRACK OF ALL_SENT_WORD_INFO!')


    ##per sentence
    # if disc_count > 0:
    #     print('pmcid', pmcid)
        # print('discontinuous count of "O-"', disc_count)
    return all_sent_word_info



def eval_preprocess_docs(eval_path, articles, tokenized_files, pmcid_sentence_files, ontologies, evaluation_files):

    max_files = 10
    file_num = 0
    # print('MAX FILES: ', max_files)


    ##capture the summary per article
    output_path = eval_path+tokenized_files
    eval_preprocess_summary_path = eval_path + 'eval_preprocess_article_summary.txt'
    eval_summary = open(eval_preprocess_summary_path, 'w+')
    eval_summary.write('%s\t%s\t%s\n' %('ARTICLE', 'TOTAL_SENTENCE_COUNT', 'TOTAL_WORD_COUNT'))

    # ##FOR TFIDF PREDICTION AND CLASSIFICATION ON CRAFT
    pmcid_sentence_dict = {} #(pmcid, sentence_num) -> [sentence, sentence_indices]
    # valid_filename = False

    for root, directories, filenames in os.walk(eval_path + articles):
        for filename in sorted(filenames):
            # if file_num < max_files:
            ##covid literature all with .txt and weird unique ids for names
            if 'covid' in [o.lower() for o in ontologies] and filename.endswith('.txt'):
                valid_filename = True

            elif evaluation_files[0].lower() == 'all' and filename.endswith('.txt'):
                valid_filename = True


            ##for all other ontologies where we write in the evaluation files
            elif filename.endswith('.txt') and (filename.replace('.txt', '') in evaluation_files or filename.replace('.nxml.gz.txt', '') in evaluation_files):
                valid_filename = True

            else:
                valid_filename = False



            if valid_filename:
                print('CURRENT ARTICLE:', filename)
                with open(root + filename, 'r+', encoding='utf-8') as pmc_doc_file:
                    pmc_doc_text = pmc_doc_file.read()

                    ##pmc_doc_sentence_list_indicies = [(start, end)]
                    pmc_doc_sentence_list, pmc_doc_sentence_list_indicies = sentence_tokenize(pmc_doc_text, filename)
                    eval_summary.write('%s\t%s\t' %(filename, len(pmc_doc_sentence_list)))
                    pmc_doc_word_list = []
                    pmc_doc_total_words = 0
                    pmc_doc_word_list_full = []

                    ##PER SENTENCE WORD TOKENIZE WITH SPANS (START AND END)
                    for s in range(len(pmc_doc_sentence_list)):
                        # print(s)
                        sentence = pmc_doc_sentence_list[s]
                        sentence_indicies = pmc_doc_sentence_list_indicies[s]
                        pmcid = filename.replace('.txt', '')
                        # print(sentence_indicies)

                        ##(pmcid, sentence_num) -> [sentence, sentence_indices, [ontology_concepts]]
                        if pmcid_sentence_dict.get((pmcid, s)):
                            pass
                        else:
                            pmcid_sentence_dict[(pmcid, s)] = [sentence, sentence_indicies]  ##(pmcid, sentence_num) -> [sentence]

                        all_sent_word_info = word_tokenize_sentences(filename.replace('.txt', ''), sentence, sentence_indicies, s, pmc_doc_text)  #the output of the word_tokenize
                        sent_num_words = len(all_sent_word_info)
                        pmc_doc_total_words += sent_num_words


                        pmc_doc_word_list += all_sent_word_info  # lists of all the words in the document (length of the words!)



                    if len(pmc_doc_word_list) != pmc_doc_total_words:
                        raise Exception('ERROR: pmc_doc_word_list should capture all the words in flat list combining everything regardless of sentence')
                    else:
                        eval_summary.write('%s\n' %(len(pmc_doc_word_list)))

                    ##OUTPUT THE BIO FORMAT RESULTS pandas dataframe! all_sent_word_info
                    columns = ['PMCID', 'SENTENCE_NUM', 'SENTENCE_START', 'SENTENCE_END', 'WORD', 'POS_TAG',
                               'WORD_START', 'WORD_END']

                    ##DATAFRAME
                    output_df = pd.DataFrame(pmc_doc_word_list, columns=columns)
                    # print(output_df)

                    output_df.to_pickle(output_path + '%s.pkl' % (filename.replace('.txt', '')))
                    output_df.to_csv(output_path + '%s.tsv' % (filename.replace('.txt', '')),'\t')

                file_num += 1







    #TODO: output the sentence information without concepts since they dont exist yet
    ##output the PMCID dictionary for TFIDF: pmcid_sentence_dict = {} #(pmcid, sentence_num) -> [sentence, sentence_indices, [ontology_concepts]]
    all_pmcids = [p for (p,s) in pmcid_sentence_dict.keys()]

    for pmcid in all_pmcids:
        with open('%s%s_%s.txt' %(output_path.replace('Tokenized_Files', pmcid_sentence_files), pmcid, 'sentence_info'), 'w+') as pmcid_output_file:
            pmcid_output_file.write('%s\t%s\t%s\t%s\n' %('PMCID', 'SENTENCE_NUMBER', 'SENTENCE', 'SENTENCE_INDICES'))
            i = 0
            while pmcid_sentence_dict.get((pmcid,i)):
                pmcid_output_file.write('%s\t%s\t%s\t%s\n' % (pmcid, i, [pmcid_sentence_dict[(pmcid, i)][0]], pmcid_sentence_dict[(pmcid, i)][1]))
                i += 1
            # for i in range(1000):
            #     if pmcid_sentence_dict.get((pmcid, i)):
            #         fin = False
            #         pmcid_output_file.write('%s\t%s\t%s\t%s\n' %(pmcid, i, [pmcid_sentence_dict[(pmcid, i)][0]], pmcid_sentence_dict[(pmcid, i)][1]))
            #     else:
            #         fin = True
            #         break
        # if fin:
        #     pass
        # else:
        #     raise Exception('ISSUE WITH MAKING SURE WE CAPTURE ALL WORDS IN THE SENTENCE IN ORDER!')


    ##dump the dictionary into a json: TypeError: keys must be str, int, float, bool or None, not tuple
    # with open('%s%s.txt' % (output_path.replace('Tokenized_Files', 'PMCID_files_sentences'), 'pmcid_sentence_dict'),
    #           'w+') as pmcid_sentence_dict_output_dump:
    #
    #
    #     json.dump(pmcid_sentence_dict, pmcid_sentence_dict_output_dump)




def eval_gold_standard(gs_tokenized_files, ontologies, evaluation_files, gs_output):
    ##the gold standard files
    for ontology in ontologies:

        ##delete files that already exist
        gold_standard_directory = os.listdir('%s%s/%s/' % (gs_output, ontology, 'gold_standard'))
        for prev_gs_bionlp in gold_standard_directory:
            if prev_gs_bionlp.endswith('.bionlp'):
                os.remove(os.path.join('%s%s/%s/' % (gs_output, ontology, 'gold_standard'), prev_gs_bionlp))
            else:
                pass

        for root, directories, filenames in os.walk(gs_tokenized_files + ontology + '/'):
            for filename in sorted(filenames):
                if filename.endswith('_mention_id_dict.pkl') and (filename.replace('_mention_id_dict.pkl', '') in evaluation_files or evaluation_files[0].lower() == 'all'):
                    # print('got here')
                    ##dict: mention_ID -> (start_list, end_list, spanned_text, mention_class_ID, class_label, sentence_number - NONE for now)
                    mention_ID_dict_pkl = open(root + filename, 'rb')
                    mention_ID_dict = pickle.load(mention_ID_dict_pkl)

                    for i, mention_ID in enumerate(mention_ID_dict.keys()):
                        (start_list, end_list, spanned_text, mention_class_ID, class_label, sentence_number) = mention_ID_dict[mention_ID]
                        # print(start_list, end_list, spanned_text, mention_class_ID, class_label, sentence_number)

                        updated_word_indices = ''
                        for j, s in enumerate(start_list):
                            e = end_list[j]
                            if j == 0:
                                updated_word_indices += '%s %s' %(s, e)  # start values
                            else:
                                updated_word_indices += ';%s %s ' %(s,e) #continuing values - discontinuity


                        ##output the concept_system_output files per models
                        with open('%s%s/%s/%s.bionlp' % (gs_output, ontology, 'gold_standard', sentence_number.split('_')[0]), 'a') as output_file:
                            output_file.write('T%s\t%s %s\t%s\n' % (i, class_label, updated_word_indices, spanned_text))







if __name__=='__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-craft_path', type=str, help='the file path to the craft documents (here version 3.1.3)')
    parser.add_argument('-concept_recognition_path', type=str, help='the file path to the working directory')
    parser.add_argument('-eval_path', type=str, help='the file path to the evaluation folder')
    parser.add_argument('-concept_system_output', type=str, help='folder for the full output')
    parser.add_argument('-article_folder', type=str, help='folder for the article text')
    parser.add_argument('-tokenized_files', type=str, help='folder for the tokenized files (output of this script)')
    parser.add_argument('-pmcid_sentence_files', type=str, help='folder for the pmcid sentence files (output of this script)')
    parser.add_argument('-concept_annotation', type=str, help='folder for concept annotations')
    parser.add_argument('-ontologies', type=str, help='a list of ontologies to use delimited with ,')
    parser.add_argument('-evaluation_files', type=str, help='a list of files to evaluate delimited with ,')
    parser.add_argument('--gold_standard', type=str, help='true if we have the gold standard and false if we dont', default=None)
    parser.add_argument('--gs_tokenized_files', type=str, help='path to the gold standard tokenized files if they exist', default=None)


    args = parser.parse_args()



    if args.gold_standard and not args.gs_tokenized_files:
        gs_tokenized_files = args.concept_recognition_path + args.tokenized_files
    else:
        gs_tokenized_files = args.concept_recognition_path + args.gs_tokenized_files

    gs_output = args.eval_path + args.concept_system_output

    ontologies = args.ontologies.split(',')
    evaluation_files = args.evaluation_files.split(',')

    # current_BIO_hierarchy = ['B', 'B-', 'I', 'I-', 'O']



    eval_preprocess_docs(args.eval_path, args.article_folder, args.tokenized_files, args.pmcid_sentence_files, ontologies, evaluation_files)
    print('PROGRESS: FINISHED PREPROCESSING ALL EVALUATION DOCS!')
    print('GOLD STANDARD:', args.gold_standard)
    if str(args.gold_standard).lower() == 'true':
        eval_gold_standard(gs_tokenized_files, ontologies, evaluation_files, gs_output)
        print('PROGRESS: FINISHED PROCESSING GOLD STANDARD TO EVALUATE ON!')
    else:
        pass

