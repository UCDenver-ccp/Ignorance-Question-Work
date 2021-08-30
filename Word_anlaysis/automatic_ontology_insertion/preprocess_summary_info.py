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
import ast
import matplotlib.pyplot as plt
import statistics
from datetime import date




def read_summary_info(preprocess_summary_info_path, all_ignorance_types, possible_section_names):
    ###summary information
    num_docs_per_it = {} #number of documents per ignorance type: it -> count
    for it in all_ingorance_types:
        num_docs_per_it[it] = 0


    overall_section_info = {} #section -> [(pmc_name, num_cues, unique_its)]
    for s in possible_section_names:
        overall_section_info[s] = []


    doc_info = {} #pmcid -> (total_cues, unique_its)

    successful_count = 0



    count = -1

    with open(preprocess_summary_info_path, 'r+') as preprocess_summary_info_file:
        next(preprocess_summary_info_file)
        next(preprocess_summary_info_file)
        next(preprocess_summary_info_file)
        for line in preprocess_summary_info_file:


            # print(line)


            if 'total number of preprocessed documents (docs with cues):' in line:
                total_files_processed = int(line.split('\t')[-1].replace('\n', ''))
                print(total_files_processed)

            elif '.nxml.gz.txt' in line:
                successful_count += 1
                if count == 3:

                    for i in range(len(sections_per_doc)):
                        overall_section_info[sections_per_doc[i]] += [(pmc_file_name, num_cues_per_section[i], num_unique_its_per_section[i])]



                """
                FILENAME	NUMBER OF CUES PER DOCUMENT	NUMBER OF UNIQUE IGNORANCE TYPES PER DOCUMENT	LIST OF UNIQUE 
                    IGNORANCE TYPES	PER SECTION INFORMATION BELOW
                BMJ_2008_Nov_7_337_a2001.nxml.gz.txt	91	14	['QUESTION_ANSWERED_BY_THIS_WORK', 
                'SUPERFICIAL_RELATIONSHIP', 'ANOMALY_CURIOUS_FINDING', 'FUTURE_PREDICTION', 'PROBABLE_UNDERSTANDING', 
                'FULL_UNKNOWN', 'DIFFICULT_TASK', 'INCOMPLETE_EVIDENCE', 'URGENT_CALL_TO_ACTION', 
                'ALTERNATIVE_OPTIONS', 'PROBLEM_COMPLICATION', 'FUTURE_WORK', 'EXPLICIT_QUESTION', 'CONTROVERSY']
                    abstract	introduction	method	results	discussion
                    2	2	11	18	58
                    2	2	7	7	13
                """

                pmc_file_info = line.replace('\n','').split('\t')
                pmc_file_name = pmc_file_info[0]
                num_cues_per_doc = pmc_file_info[1]
                num_unique_its_per_doc = pmc_file_info[2]

                doc_info[pmc_file_name] = (num_cues_per_doc, num_unique_its_per_doc)


                unique_its = ast.literal_eval(pmc_file_info[3])
                # print(unique_its)
                for it in unique_its:
                    num_docs_per_it[it] += 1




                count = 0



            elif line.startswith('\t'):
                if count == 0:
                    sections_per_doc = line.replace('\n','').split('\t')[1:]
                    count += 1



                elif count == 1:
                    num_cues_per_section = line.replace('\n','').split('\t')[1:]
                    count += 1

                elif count == 2:
                    num_unique_its_per_section = line.replace('\n', '').split('\t')[1:]
                    count += 1
                else:
                    print('IT SHOULD NEVER GET HERE!')
                    pass




    if successful_count != total_files_processed:
        print(successful_count)

        raise Exception('ERROR WITH PROCESSING THROUGH EVERY DOCUMENT TO SAVE THE SECTION INFO STUFF! (COUNT=3 SPOT)')

    return total_files_processed, num_docs_per_it, overall_section_info, doc_info




def summary_visualization(total_files_processed, num_docs_per_it, overall_section_info, doc_info, output_summary_path):

    #num_docs_per_it - #number of documents per ignorance type: it -> count
    #overall_section_info - #section -> [(pmc_name, num_cues, unique_its)]
    #doc_info - #pmcid -> (total_cues, unique_its)


    ###TODO: FIX ERRORS WITH HISTOGRAM
    ignorance_types = num_docs_per_it.keys()
    num_docs_per_it_list = [num_docs_per_it[i] for i in ignorance_types]
    #
    # n, bins, patches = plt.hist(x=num_docs_per_it_list, bins='auto', color='#0504aa',
    #                             alpha=0.7, rwidth=0.85)
    # plt.grid(axis='y', alpha=0.75)
    # plt.xlabel('ignorance types')
    # plt.ylabel('number of documents')
    # plt.title('NUMBER OF DOCUMENTS PER IGNORANCE TYPE')
    # plt.show()



    lcs_all_docs_list = []
    unique_its_all_docs_list = []

    max_lcs = 0
    max_pmcid = None
    min_lcs = 1000
    min_pmcid = None

    for pmcid in doc_info.keys():
        lcs_all_docs_list += [int(doc_info[pmcid][0])]
        unique_its_all_docs_list += [int(doc_info[pmcid][1])]


        if int(doc_info[pmcid][0]) > max_lcs:
            max_pmcid = pmcid
            max_lcs = int(doc_info[pmcid][0])
        else:
            pass

        if int(doc_info[pmcid][0]) < min_lcs:
            min_pmcid = pmcid
            min_lcs = int(doc_info[pmcid][0])
        else:
            pass



    ##DOCUMENT INFORMATION
    average_lcs_all_docs = statistics.mean(lcs_all_docs_list)
    median_lcs_all_docs = statistics.median(lcs_all_docs_list)
    average_unique_its_all_docs = statistics.mean(unique_its_all_docs_list)
    median_unique_its_all_docs = statistics.median(unique_its_all_docs_list)

    mid_pmcids = []

    for pmcid in doc_info.keys():
        if int(doc_info[pmcid][0]) == int(average_lcs_all_docs):
            mid_pmcids += [pmcid]
            mid_lcs = doc_info[pmcid][0]
        else:
            pass



    with open('%sdoc_info_summary_%s.txt' %(output_summary_path, date.today()), 'w+') as doc_info_file:
        doc_info_file.write('%s\t%s\n\n' %('TOTAL NUMBER OF DOCUMENTS ASSESSED:', total_files_processed))

        doc_info_file.write('%s\n' %'NUMBER OF DOCS PER IGNORANCE TYPE')
        for i in num_docs_per_it.keys():
            doc_info_file.write('%s\t%s\n' %(i, num_docs_per_it[i]))
        doc_info_file.write('\n')

        doc_info_file.write('%s\t%.1f\n' %('AVERAGE LEXICAL CUES PER DOC:', average_lcs_all_docs))
        doc_info_file.write('%s\t%.1f\n' % ('MEDIAN LEXICAL CUES PER DOC:', median_lcs_all_docs))
        doc_info_file.write('%s\t%.1f\n' %('AVERAGE UNIQUE IGNORANCE TYPES PER DOC:', average_unique_its_all_docs))
        doc_info_file.write('%s\t%.1f\n' % ('MEDIAN UNIQUE IGNORANCE TYPES PER DOC:', median_unique_its_all_docs))
        doc_info_file.write('\n')




        doc_info_file.write('%s\t%s (%s)\n' %('PMCID WITH MAXIMUM LEXICAL CUES:', max_pmcid, max_lcs))
        doc_info_file.write('%s\t%s (%s)\n' % ('PMCID WITH MINIMUM LEXICAL CUES:', min_pmcid, min_lcs))
        doc_info_file.write('\n%s\n' %'ALL PMCIDS WITH AVERAGE LEXICAL CUES')
        for p in mid_pmcids:
            doc_info_file.write('%s\t%s (%s)\n' % ('PMCID WITH AVERAGE LEXICAL CUES:', p, mid_lcs))



    ##SECTION INFO: #overall_section_info - #section -> [(pmc_name, num_cues, unique_its)]
    sections = []
    # all_section_num_cues = []
    # all_section_unique_its = []

    all_section_info = [] #tuples

    with open('%ssection_info_summary_%s.txt' %(output_summary_path, date.today()), 'w+') as section_info_file:
        section_info_file.write('%s\n' %'SECTION INFORMATION SUMMARY PER SECTION')
        section_info_file.write('%s\t%s\t%s\t%s\t%s\t%s\n' %('SECTION', 'TOTAL_DOCS', 'AVERAGE LEXICAL CUES', 'MEDIAN LEXICAL CUES', 'AVERAGE UNIQUE IGNORANCE TYPES', 'MEDIAN UNIQUE IGNORANCE TYPES'))

        for s in overall_section_info.keys():
            section_info_file.write('%s\t' %s)

            sections += [s]
            section_num_cues = []
            section_unique_its = []
            for t in overall_section_info[s]:
                section_num_cues += [int(t[1])]
                section_unique_its += [int(t[2])]
            # all_section_num_cues += [section_num_cues]
            # all_section_unique_its += [section_unique_its]


            if len(section_unique_its) != len(section_num_cues):
                raise Exception('ERROR WITH SECTION INFORMATION AROUND UNIQUE ITS AND NUM_CUES!')

            total_pmcids_per_section = len(section_num_cues)
            average_section_num_cues = statistics.mean(section_num_cues)
            median_section_num_cues = statistics.median(section_num_cues)


            average_section_unique_its = statistics.mean(section_unique_its)
            median_section_unique_its = statistics.median(section_unique_its)

            all_section_info += [(total_pmcids_per_section, average_section_num_cues, median_section_num_cues, average_section_unique_its, median_section_unique_its)]


            section_info_file.write('%s\t%.1f\t%.1f\t%.1f\t%.1f\n' %(total_pmcids_per_section, average_section_num_cues, median_section_num_cues, average_section_unique_its, median_section_unique_its))







if __name__ == '__main__':
    output_summary_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Development_Pre_natal_nutrition/Prenatal_Nutrition_Python_Scripts/automatic_ontology_insertion/'

    # all_ingorance_types = ['QUESTION_ANSWERED_BY_THIS_WORK', 'SUPERFICIAL_RELATIONSHIP', 'ANOMALY_CURIOUS_FINDING', 'FUTURE_PREDICTION', 'PROBABLE_UNDERSTANDING', 'FULL_UNKNOWN', 'DIFFICULT_TASK', 'INCOMPLETE_EVIDENCE', 'URGENT_CALL_TO_ACTION', 'ALTERNATIVE_OPTIONS', 'PROBLEM_COMPLICATION', 'FUTURE_WORK', 'EXPLICIT_QUESTION', 'CONTROVERSY']


    all_ingorance_types = ['EPISTEMICS', 'FUTURE_OPPORTUNITIES', 'BARRIERS', 'LEVELS_OF_EVIDENCE','QUESTION_ANSWERED_BY_THIS_WORK', 'SUPERFICIAL_RELATIONSHIP', 'ANOMALY_CURIOUS_FINDING', 'FUTURE_PREDICTION', 'PROBABLE_UNDERSTANDING', 'FULL_UNKNOWN', 'DIFFICULT_TASK','INCOMPLETE_EVIDENCE', 'IMPORTANT_CONSIDERATION', 'ALTERNATIVE_OPTIONS_CONTROVERSY','PROBLEM_COMPLICATION', 'FUTURE_WORK', 'EXPLICIT_QUESTION']

    possible_section_names = ['abstract', 'introduction', 'background', 'method', 'results', 'conclusion', 'discussion']

    full_output_summary_path = '%spreprocess_summary_info_%s.txt' %(output_summary_path, date.today())

    total_files_processed, num_docs_per_it, overall_section_info, doc_info = read_summary_info(full_output_summary_path, all_ingorance_types, possible_section_names)
    print('PROGRESS: finished reading in the summary file')

    summary_visualization(total_files_processed, num_docs_per_it, overall_section_info, doc_info, output_summary_path)




