import os
import re
import gzip
import argparse
import numpy as np
import nltk.data
import sys
# import termcolor
# from termcolor import colored, cprint
from xml.etree import ElementTree as ET
import xml.etree.ElementTree as ET
from xml.dom import minidom
import multiprocessing as mp
import functools
import resource, sys
from emoji import UNICODE_EMOJI
import demoji
import itertools
from datetime import date
import ast
import copy
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tokenize import WordPunctTokenizer
from statistics import mean, median


def get_all_lcs(all_lcs_path):
    all_lcs_dict = {} #lexical cue -> ignorance type (all caps)
    unique_its = set()
    with open(all_lcs_path, 'r') as all_lcs_file:
        next(all_lcs_file)
        #header: LEXICAL CUE	SYNONYMS	IGNORANCE TYPE
        for line in all_lcs_file:
            (lc, synonyms, it) = line.strip('\n').split('\t')
            ##weirdly future opportunities is in it too
            if it == 'FUTURE_OPPORTUNITIES':
                it = lc.upper()
            else:
                pass

            if all_lcs_dict.get(lc):
                all_lcs_dict[lc] += [it]
            else:
                all_lcs_dict[lc] = [it]

            ##collect all the unique ignorance types
            unique_its.add(it)


    ##collect the number of cues per ignorance type
    lc_count_per_it = {} #it -> # unique lcs
    for it in unique_its:
        lc_count_per_it[it] = 0
    for (key_lc, value_list_it) in all_lcs_dict.items():
        for v in value_list_it:
            lc_count_per_it[v] += 1
    # print('lc count per it')
    # print(lc_count_per_it)


    return all_lcs_dict, unique_its, lc_count_per_it


def annotation_information(all_lcs_dict, unique_its, annotation_path, section_info_path, section_format, possible_section_names):
    ##count of annotations for each it
    it_annotation_counts_dict = {} #it -> count of annotations
    total_scope_annotations = 0

    ##section information - not unique
    section_counts_dict = {} #section -> [article count, lexical cue count, dictionary from article to count of cues per section] - len of list per article is the number of articles with that section
    for section in possible_section_names:
        section_counts_dict[section] = [set([]), 0, {}]

    no_sections_count = set([])

    for i in unique_its:
        it_annotation_counts_dict[i] = [0, set([])]

    it_annotation_counts_dict['ALL_CATEGORIES'] = [0, set([])]

    ##annotation information per article
    article_annot_info_dict = {} #(article/filename, it) -> [num cues per article, set of unique cues]


    print(possible_section_names)

    ##loop over the annotation fles
    article_count = 0
    for root, directories, filenames in os.walk(annotation_path):
        for filename in sorted(filenames):
            if filename.endswith('.xml'):
                article_count += 1

                ##section filename
                article_section_filename = str(filename.split('.xml')[0]) + '.txt.gz.' + section_format + '.annot.gz'

                print(filename)
                for j in unique_its:
                    article_annot_info_dict[(filename, j)] = [0, set([])]

                with open(root+filename, 'r+') as annotation_file, gzip.open(section_info_path+article_section_filename, 'rt+') as section_info_file:

                    ##read in all the section info and get the starts
                    local_section_info_starts = []

                    for s in possible_section_names:
                        local_section_info_starts += ['NA']

                    for line in section_info_file:
                        section_name = line.split('\t')[-2]
                        section_start = int(line.split('\t')[-1].strip('\n'))

                        ##update the starts to be in the order of the possible_section_names
                        local_section_info_starts[possible_section_names.index(section_name)] = section_start


                    print(local_section_info_starts)

                    ##check to make sure they are in order?
                    #gather all the non-NA section names and starts to see if they are in order
                    local_section_names = []
                    local_section_starts = []
                    local_starts_to_names_dict = {} #dict: start -> name
                    for i,p in enumerate(possible_section_names):
                        if local_section_info_starts[i] != 'NA':
                            local_section_names += [p]
                            local_section_starts += [local_section_info_starts[i]]

                            local_starts_to_names_dict[local_section_info_starts[i]] = p

                            section_counts_dict[p][0].add(filename)

                    #sort the list to be in the correct order
                    sorted_local_section_starts = sorted(local_section_starts)



                    tree = ET.parse(annotation_file)
                    tree_root = tree.getroot()
                    # print(root)

                    ##loop over all annotations
                    for annotation in tree_root.iter('annotation'):
                        annotation_id = annotation.attrib['id']
                        # print('annotation id', annotation_id)
                        empty_annotation = False
                        weird_cues = False
                        full_annotation = False
                        ##loop over all annotation information
                        for child in annotation:
                            # print(child)
                            if child.tag == 'class':
                                ont_lc = child.attrib['id'] #lexical cue

                                # print('ont_lc', ont_lc)

                                if ont_lc:
                                    if ont_lc == 'subject_scope' or all_lcs_dict.get(ont_lc.strip('0_')) or ont_lc.strip('0_').upper() in unique_its:

                                        continue

                                    else:
                                        print('weird cue', ont_lc)
                                        weird_cues = True
                                        # raise Exception('ERROR: MISSING LEXICAL CUE FOR SOME REASON!')
                                else:
                                    empty_annotation = True

                            elif child.tag == 'span':
                                #if no text then an empty annotation
                                if not child.text:
                                    # print(child)
                                    empty_annotation = True
                                else:
                                    full_annotation = True
                                    ##section information - checking span to see which section it is in
                                    span_end = int(child.attrib['end'])
                                    final_start = None
                                    if sorted_local_section_starts:
                                        for start in sorted_local_section_starts:
                                            if span_end < start:
                                                final_start = start
                                                break
                                            else:
                                                pass

                                        if final_start:
                                            #found the section
                                            final_section = local_starts_to_names_dict[final_start]
                                        else:
                                            #the last one because it is to the end of the document
                                            final_section = local_starts_to_names_dict[sorted_local_section_starts[-1]]
                                    else:
                                        no_sections_count.add(filename)




                            else:
                                print('got here weirdly')
                                raise Exception('ERROR WITH READING IN THE ANNOTATION FILES!')
                                pass


                        ##check if an empty annotation or not
                        if empty_annotation or not full_annotation:
                            continue
                        else:
                            if weird_cues:
                                # print(all_lcs_dict['0_alternative_options'])
                                # print(ont_lc)
                                raise Exception('ERROR: MISSING LEXICAL CUES!')

                            ##fill the dictionary with the info
                            if all_lcs_dict.get(ont_lc):
                                ##TODO: taking the first one in the list to count for annotations - not counting everything
                                ##totals
                                it_annotation_counts_dict[all_lcs_dict[ont_lc.strip('0_')][0]][0] += 1
                                it_annotation_counts_dict[all_lcs_dict[ont_lc.strip('0_')][0]][1].add(ont_lc)

                                ##full totals for all categories
                                it_annotation_counts_dict['ALL_CATEGORIES'][0] += 1
                                it_annotation_counts_dict['ALL_CATEGORIES'][1].add(ont_lc)

                                ##per article
                                article_annot_info_dict[(filename, all_lcs_dict[ont_lc.strip('0_')][0])][0] += 1
                                article_annot_info_dict[(filename, all_lcs_dict[ont_lc.strip('0_')][0])][1].add(ont_lc)


                                ##per section
                                #totals
                                section_counts_dict[final_section][1] += 1

                                #per article
                                if section_counts_dict[final_section][2].get(filename):
                                    section_counts_dict[final_section][2][filename] += 1
                                else:
                                    section_counts_dict[final_section][2][filename] = 1

                            elif ont_lc.upper() in unique_its and ont_lc.upper() != 'SUBJECT_SCOPE':
                                ##totals
                                it_annotation_counts_dict[ont_lc.strip('0_').upper()][0] += 1
                                it_annotation_counts_dict[ont_lc.strip('0_').upper()][1].add(ont_lc)

                                ##full totals for all categories
                                it_annotation_counts_dict['ALL_CATEGORIES'][0] += 1
                                it_annotation_counts_dict['ALL_CATEGORIES'][1].add(ont_lc)

                                ##per article
                                article_annot_info_dict[(filename, ont_lc.strip('0_').upper())][0] += 1
                                article_annot_info_dict[(filename, ont_lc.strip('0_').upper())][1].add(ont_lc)

                                ##per section
                                # totals
                                section_counts_dict[final_section][1] += 1

                                # per article
                                if section_counts_dict[final_section][2].get(filename):
                                    section_counts_dict[final_section][2][filename] += 1
                                else:
                                    section_counts_dict[final_section][2][filename] = 1

                            elif ont_lc.upper() == 'SUBJECT_SCOPE':
                                ##total
                                total_scope_annotations += 1


                                it_annotation_counts_dict[ont_lc.upper()][0] += 1
                                it_annotation_counts_dict[ont_lc.upper()][1].add(ont_lc)

                                ##per article
                                article_annot_info_dict[(filename, ont_lc.upper())][0] += 1
                                article_annot_info_dict[(filename, ont_lc.upper())][1].add(ont_lc)


            # else:
            #     print(filename)
            #     raise Exception('ERROR: WEIRD FILE IN ANNOTATIONS!')
            #     for it in unique_its:
            #         print(filename, it)
            #         print(article_annot_info_dict[(filename,it)])
            #     raise Exception('hold')

            # raise Exception('HOLD!')

    ###get all statistics for the articles using article_annot_info_dict[(filename, it)]

    ##first make the lists of all the numbers for each article per ignorance type
    it_lists_per_article_dict = {} #it -> [[# cues per article], [# unique cues per article]]
    for it in unique_its:
        it_lists_per_article_dict[it] = [[],[]]

    for key_list, value_list in article_annot_info_dict.items():
        # print(key_list)
        # print(value_list)
        it_lists_per_article_dict[key_list[1]][0] += [value_list[0]]
        it_lists_per_article_dict[key_list[1]][1] += [len(value_list[1])]
    # print(it_lists_per_article_dict)


    ##get all statistics for each it
    it_stats_per_article_dict = {} #it -> [[mean, median, min, max], [mean, median, min, max]] (regular and then unique)

    ##total stuff for all cues!
    total_count_list = [0 for i in range(article_count)]
    total_unique_count_list = [0 for i in range(article_count)]

    for it in unique_its:
        (full_count_list, unique_count_list) = it_lists_per_article_dict[it]
        if it.upper() != 'SUBJECT_SCOPE':
            for i in range(article_count):
                total_count_list[i] += full_count_list[i]
                total_unique_count_list[i] += unique_count_list[i]
        # print(it)
        # print(len(full_count_list))
        # print(unique_count_list)
        # raise Exception('hold!')

        full_count_stats = [mean(full_count_list), median(full_count_list), min(full_count_list), max(full_count_list)]
        unique_count_stats = [mean(unique_count_list), median(unique_count_list), min(unique_count_list), max(unique_count_list)]
        it_stats_per_article_dict[it] = [full_count_stats, unique_count_stats]

    total_count_stats = [mean(total_count_list), median(total_count_list), min(total_count_list), max(total_count_list)]
    total_unique_count_stats = [mean(total_unique_count_list), median(total_unique_count_list), min(total_unique_count_list), max(total_unique_count_list)]

    it_stats_per_article_dict['ALL_CATEGORIES'] = [total_count_stats, total_unique_count_stats]

    print(it_stats_per_article_dict['ALL_CATEGORIES'])
    # raise Exception('hold')



    ##section information
    final_no_sections_count = len(no_sections_count)
    final_section_info = {} #section -> [total article count, total annotations, average, median, min, max]
    for s in section_counts_dict:
        print(s)
        print(section_counts_dict[s])

        #totals
        total_num_articles_per_section = len(section_counts_dict[s][0]) #need to add 0s for my averaging
        total_annotations_per_section = section_counts_dict[s][1]

        #per articles
        section_counts_per_article = []
        for a, c in section_counts_dict[s][2].items():
            print(a,c)
            section_counts_per_article += [c]
        #update the article lists to include the ones with 0
        for i in range(total_num_articles_per_section -len(section_counts_per_article)):
            section_counts_per_article += [0]



        final_section_info[s] = [total_num_articles_per_section, total_annotations_per_section, mean(section_counts_per_article), median(section_counts_per_article), min(section_counts_per_article), max(section_counts_per_article)]

    return it_annotation_counts_dict, total_scope_annotations, it_stats_per_article_dict, final_no_sections_count, final_section_info


def article_information(article_path):
    total_sentences = 0
    total_words = 0
    all_unique_words = set()

    ##loop over the article files
    for root, directories, filenames in os.walk(article_path):
        for filename in sorted(filenames):
            if filename.endswith('.txt'):
                article_file = open(root+filename, 'r+')
                article_text = article_file.read()  # the whole pmc file text - all lowercase
                ##tokenize into sentences
                sentence_list = sent_tokenize(article_text)
                total_sentences += len(sentence_list)

                tk = WordPunctTokenizer()
                word_list = tk.tokenize(article_text)
                total_words += len(word_list)
                all_unique_words.update(set(word_list))


            # else:
            #     print(filename)
            #     raise Exception('ERROR: WEIRD FILENAME IN ARTICLE PATH!')

    total_unique_words = len(all_unique_words)

    return total_sentences, total_words, total_unique_words

def gold_standard_summary(output_path, it_annotation_counts_dict, lc_count_per_it, it_stats_per_article_dict,  total_scope_annotations, total_sentences, total_words, total_unique_words, final_no_sections_count, final_section_info):

    with open('%s%s%s.txt' %(output_path, 'gold_standard_summary', date.today()), 'w+') as summary_output_file:
        summary_output_file.write('%s\t%s\n' %('TOTAL SENTENCES:', total_sentences))
        summary_output_file.write('%s\t%s\n' % ('TOTAL WORDS:', total_words))
        summary_output_file.write('%s\t%s\n' % ('TOTAL UNIQUE WORDS:', total_unique_words))

        summary_output_file.write('\n')

        summary_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' %('IGNORANCE CATEGORY','TOTAL CUES', 'ANNOTATION COUNT', 'AVERAGE # ANNOTATIONS PER ARTICLE', 'MEDIAN # ANNOTATIONS PER ARTICLE', 'MINIMUM # ANNOTATIONS PER ARTICLE', 'MAXIMUM # ANNOTATIONS PER ARTICLE',  'UNIQUE ANNOTATION COUNT', 'AVERAGE # UNIQUE ANNOTATIONS PER ARTICLE', 'MEDIAN # UNIQUE ANNOTATIONS PER ARTICLE', 'MINIMUM # UNIQUE ANNOTATIONS PER ARTICLE', 'MAXIMUM # UNIQUE ANNOTATIONS PER ARTICLE', ))
        total_annotations = 0
        total_cues = 0
        total_unique_annotations = 0
        for it in it_annotation_counts_dict.keys():
            # print(it)
            # # print(lc_count_per_it[it])
            # print(it_annotation_counts_dict[it])
            # print(it_stats_per_article_dict[it])

            ##SUBJECT SCOPE
            if it.upper() == 'SUBJECT_SCOPE':
                summary_output_file.write('%s\t%s\t%s\t%.2f\t%.2f\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
                it, 'NA', it_annotation_counts_dict[it][0], it_stats_per_article_dict[it][0][0],
                it_stats_per_article_dict[it][0][1], it_stats_per_article_dict[it][0][2],
                it_stats_per_article_dict[it][0][3], 'NA',
                'NA', 'NA',
                'NA', 'NA'))

            ##ALL CATEGORIES
            elif it.upper() == 'ALL_CATEGORIES':
                # raise Exception('hold')
                # print(lc_count_per_it[it])
                # print(it_annotation_counts_dict[it])
                summary_output_file.write('%s\t%s\t%s\t%.2f\t%.2f\t%s\t%s\t%s\t%.2f\t%.2f\t%s\t%s\n' % (
                it, 'NA', it_annotation_counts_dict[it][0], it_stats_per_article_dict[it][0][0],
                it_stats_per_article_dict[it][0][1], it_stats_per_article_dict[it][0][2],
                it_stats_per_article_dict[it][0][3], len(it_annotation_counts_dict[it][1]),
                it_stats_per_article_dict[it][1][0], it_stats_per_article_dict[it][1][1],
                it_stats_per_article_dict[it][1][2], it_stats_per_article_dict[it][1][3]))

            else:
                summary_output_file.write('%s\t%s\t%s\t%.2f\t%.2f\t%s\t%s\t%s\t%.2f\t%.2f\t%s\t%s\n' %(it, lc_count_per_it[it], it_annotation_counts_dict[it][0], it_stats_per_article_dict[it][0][0], it_stats_per_article_dict[it][0][1], it_stats_per_article_dict[it][0][2], it_stats_per_article_dict[it][0][3],   len(it_annotation_counts_dict[it][1]), it_stats_per_article_dict[it][1][0], it_stats_per_article_dict[it][1][1], it_stats_per_article_dict[it][1][2], it_stats_per_article_dict[it][1][3]))

                total_annotations += it_annotation_counts_dict[it][0]
                total_cues += lc_count_per_it[it]
                total_unique_annotations += len(it_annotation_counts_dict[it][1])

        summary_output_file.write('\n')
        summary_output_file.write('%s\t%s\n' % ('TOTAL CUES:', total_cues))
        summary_output_file.write('%s\t%s\n' %('TOTAL CLASS ANNOTATIONS:', total_annotations))
        summary_output_file.write('%s\t%s\n' % ('TOTAL UNIQUE CLASS ANNOTATIONS:', total_unique_annotations))
        summary_output_file.write('%s\t%s\n' %('TOTAL SCOPE ANNOTATIONS:', total_scope_annotations))



        ##section information
        summary_output_file.write('\n\n\n')
        summary_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\n' %('SECTION', 'TOTAL # ARTICLES WITH SECTION', 'ANNOTATION COUNT', 'AVERAGE # ANNOTATIONS PER ARTICLE', 'MEDIAN # ANNOTATIONS PER ARTICLE', 'MINIMUM # ANNOTATIONS PER ARTICLE', 'MAXIMUM # ANNOTATIONS PER ARTICLE'))
        for s, info in final_section_info.items():
            summary_output_file.write('%s\t%s\t%s\t%.2f\t%.2f\t%s\t%s\n' %(s, info[0], info[1], info[2], info[3], info[4], info[5]))


        summary_output_file.write('\n')
        summary_output_file.write('%s\t%s\n' %('# ARTICLES WITH NO SECTIONS', final_no_sections_count))




if __name__ == '__main__':
    gs_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/'
    gs_path_v2 = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation_v2/'

    article_path = 'Articles/'
    annotation_path = 'Annotations/'


    ##ALL LCS PATH - NEED TO CHANGE FOR EACH UPDATE!
    # all_lc_path = 'Ontologies/Ontology_Of_Ignorance_all_cues_2020-03-27.txt'
    all_lc_path = 'Ontologies/Ontology_Of_Ignorance_all_cues_2020-08-25.txt'


    # ##possible section names for the regex-sections.annot
    # section_info_path = 'section_info_crude/'
    # section_format = 'regex-sections'
    # possible_section_names = ['abstract', 'introduction', 'background', 'method', 'results', 'discussion', 'conclusion']

    ##NEED TO GRAB SECTION INFORMATION
    # ##possible section names for the BioC-sections.annot
    section_info_path = 'section_info_BioC/'
    section_format = 'BioC-sections'
    possible_section_names = ['title', 'abstract', 'introduction', 'methods', 'results', 'discussion', 'conclusion']

    ##gather all lexical cues and unique its
    all_lcs_dict, unique_its, lc_count_per_it = get_all_lcs(gs_path+all_lc_path)
    unique_its.add('SUBJECT_SCOPE')
    print(type(unique_its))

    print('UNIQUE ITS', unique_its)

    print(len(unique_its))
    # raise Exception('break!')

    all_lcs_dict['is'] = ['EXPLICIT_QUESTION']##we took this out later
    all_lcs_dict['than'] = ['ALTERNATIVE_OPTIONS_CONTROVERSY'] ##we took this out later
    all_lcs_dict['alternative_options'] = ['ALTERNATIVE_OPTIONS_CONTROVERSY']
    all_lcs_dict['urgent_call_to_action'] = ['IMPORTANT_CONSIDERATION']

    # print(unique_its)
    ##gather all annotation information for each ignorance type
    it_annotation_counts_dict, total_scope_annotations, it_stats_per_article_dict, final_no_sections_count, final_section_info  = annotation_information(all_lcs_dict, unique_its, gs_path+annotation_path, gs_path+section_info_path, section_format, possible_section_names)
    # print(it_annotation_counts_dict)
    # print(article_annot_info_dict)

    #gather all article information
    total_sentences, total_words, total_unique_words = article_information(gs_path+article_path)


    ##output all the information
    gold_standard_summary(gs_path, it_annotation_counts_dict, lc_count_per_it, it_stats_per_article_dict, total_scope_annotations, total_sentences, total_words, total_unique_words, final_no_sections_count, final_section_info)


