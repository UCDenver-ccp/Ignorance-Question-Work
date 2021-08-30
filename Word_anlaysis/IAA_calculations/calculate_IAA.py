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


# demoji.download_codes()

def all_ontology_cues(all_ontology_inserted_lcs_path):
    """
	Gathers all the ontology inserted lexical cues for use in automatic regex annotation (preprocessing)
	:param all_ontology_inserted_lcs_path: the file path to all of the ontology inserted lexical cues
	:return: all_lcs: a list of all the ontology terms to be used in the next phases
	"""

    all_lc_it_dict = {}  # lexical cue -> ignorance type
    # all_lcs = []  # lexical cue, synonym (regex), ignorance type
    all_its = set([])

    with open(all_ontology_inserted_lcs_path, 'r+') as all_ontology_inserted_lcs_file:
        tree = ET.parse(all_ontology_inserted_lcs_file)
        ont_root = tree.getroot()
        # print(ont_root)

        for annotation_assertion in ont_root.iter('{http://www.w3.org/2002/07/owl#}AnnotationAssertion'):
            useful = False
            for child in annotation_assertion:

                if child.tag == '{http://www.w3.org/2002/07/owl#}AnnotationProperty' and child.attrib['IRI'] == '#epistemicCategory':
                    useful = True
                elif useful:
                    # lexical cue
                    if child.tag == '{http://www.w3.org/2002/07/owl#}IRI':
                        lc = child.text.replace('#', '')
                    # ignorance type
                    elif child.tag == '{http://www.w3.org/2002/07/owl#}Literal':

                        all_its.add(child.text)  ##gather all ignorance types
                        if all_lc_it_dict.get(lc):
                            all_lc_it_dict[lc] += [
                                child.text]  ##TODO: issue with multiple ignorance types per cue (10 of them)
                        # print('got here')
                        # print(lc, all_lc_it_dict[lc])
                        else:
                            all_lc_it_dict[lc] = [child.text]



                else:
                    break
    # print(all_lc_it_dict)
    return all_lc_it_dict, list(all_its)


def collect_annotations(annotation_path, article, all_lc_it_dict, span_overlap_score_dict, sole_annotator):
    #per article and per annotator
    ##TODO: confirm that all lexical cues have a subject/scope - the same subject/scope for many lexical cues - need to be encompassed by a subject/scope
    annotation_article_dict = {}  # ignorance type -> [[annotation_id, ont_lc, [(spans) sorted by starts]]]
    no_spans = []
    duplicate_problem = set([])  ##add things to see if they don't add cuz they are already there
    num_duplicates = 0

    # print('CURRENT SOLE ANNOATOR:', sole_annotator)

    #span_overlap_score_dict = {} #most lenient score that includes same span overlap: (pmcid, span sorted by starts) -> [list of annotators] if overlap

    #'/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/1_First_Full_Annotation_Task_Elizabeth_11.6.19/'

    # print('annotation path:', annotation_path)
    if 'v2' in annotation_path:
        current_annotator = annotation_path.split('/')[-2].split('_')[-3].upper()
    elif type(annotation_path) == dict:
        current_annotator = sole_annotator
        annotation_path = annotation_path[current_annotator]
    else:
        current_annotator = annotation_path.split('/')[-2].split('_')[-2].upper()
    # print('current annotator:', current_annotator)


    if current_annotator.isdigit():
        current_annotator = 'PREPROCESS'
        annotation_file_path = '%s/Annotations/%s.nxml.gz.xml' % (annotation_path, article)
    elif current_annotator.upper() in 'GOLD_STANDARD':
        # print(annotation_path)
        for filename in os.listdir(annotation_path+'Annotations'):
            # print(entry)
            if filename.startswith('%s.nxml.gz.xml' %(article)):
                # print(article)
                # print(filename)
                annotation_file_path = '%s%s/%s' %(annotation_path, 'Annotations', filename)
                break
            else:
                continue

    else:
        annotation_file_path = '%s/Annotations/%s.nxml.gz.xml' % (annotation_path, article)

    # raise Exception('hold!')
    # print(annotation_file_path)

    if 'v2' in annotation_path:
        sole_annotator = annotation_file_path.split('/')[-1].split('.')[-2].split('_')[0]
    else:
        pass
    # print('SOLE ANNOTATOR:', sole_annotator)

    with open(annotation_file_path, 'r') as annotation_file:
        tree = ET.parse(annotation_file)
        root = tree.getroot()
        # print(root)


        ##loop over all annotations
        for annotation in root.iter('annotation'):
            annotation_id = annotation.attrib['id']
            # print('annotation id', annotation_id)
            spans = []
            empty_annotation = False
            ##loop over all annotation information
            for child in annotation:
                # print(child)
                if child.tag == 'class':
                    ont_lc = child.attrib['id']
                    # print('ont_lc', ont_lc)
                    if all_lc_it_dict.get(ont_lc):
                        it = all_lc_it_dict[ont_lc][0]  # ignorance type category #TODO: MULTIPLE CATEGORIES IT COULD BE! Taking the first one for now!
                    else:
                        it = ont_lc
                elif child.tag == 'span':
                    ##empty annotation - delete
                    if not child.text:
                        # print(child)
                        empty_annotation = True
                        # raise Exception('ERROR WITH EMPTY ANNOTATION')
                    else:
                        span_start = int(child.attrib['start'])
                        span_end = int(child.attrib['end'])
                        spans += [(span_start, span_end)]

                else:
                    print('got here weirdly')
                    raise Exception('ERROR WITH READING IN THE ANNOTATION FILES!')
                    pass

            if empty_annotation:
                continue
            else:
                ##fill the dictionary with the info
                spans = sorted(spans, key=lambda x: x[0])  ##sorted by starts
                if len(spans) == 0:
                    # print(article, annotation_id)
                    no_spans += [annotation_id]
                # print(spans)
                # print(it)
                else:
                    # print(ont_lc, spans)
                    # if ont_lc == 'impact':
                    duplicate_problem_old = duplicate_problem.copy()  ##need to make sure to copy the list and not make it changeable
                    duplicate_problem.add('%s_%s' % (ont_lc, spans))
                    # print(duplicate_problem)

                    if len(duplicate_problem_old) == len(duplicate_problem):
                        num_duplicates += 1
                        # raise Exception('duplicates!')
                    else:
                        if annotation_article_dict.get(it):
                            annotation_article_dict[it] += [[annotation_id, ont_lc, spans]]
                        else:
                            annotation_article_dict[it] = [[annotation_id, ont_lc, spans]]

                        ##output the span scoring
                        # print('info for scoring')
                        # print(article)
                        # print(spans)
                        if span_overlap_score_dict.get((article, str(spans))):
                            span_overlap_score_dict[(article, str(spans))] += [current_annotator]
                        else:
                            span_overlap_score_dict[(article, str(spans))] = [current_annotator]

    with open('%sIAA/%s_ann_summary.txt' % (annotation_path, article), 'w+') as article_summary_output:
        article_summary_output.write('%s\t%s\n' % ('IGNORANCE TYPE', 'ANNOTATION COUNT'))
        for i in annotation_article_dict:
            # print(i, len(annotation_article_dict[i]))
            article_summary_output.write('%s\t%s\n' % (i, len(annotation_article_dict[i])))

    # print('NUMBER OF NO SPANS:', len(no_spans))  # TODO: WEIRD HUNG SPANS!

    print('NUMBER OF DUPLICATES:', num_duplicates)

    return annotation_article_dict, span_overlap_score_dict, sole_annotator


def split_lists(lst_of_lst):
    # print(lst_of_lst)
    lst1 = []
    lst2 = []
    # lst3 = []

    for a in lst_of_lst:
        lst1 += [[a[0]]]
        lst2 += [[a[1], a[2]]]
    # lst3 += [a[2]]

    return lst1, lst2  # ,lst3



def fuzzy_match(item, item_annotator, item_annotation_id, lst, lst_annotator, lst_annotation_id, all_lc_it_dict):
    ##see if the item overlaps with an element in the lst
    # print('ITEM', item, item_annotator, item_annotation_id) #list for annotation_id
    # print('LST', lst, lst_annotator, lst_annotation_id) #list of list for annotation id
    min_item_start = min([a[0] for a in item[1]])
    max_item_end = max([a[1] for a in item[1]])
    # item_it = all_lc_it_dict[item[0]]
    # overlap_match_indices_list = [] #list of the indices in the lst of the item
    # main_category_indices_list = []

    all_match_types = [None for l in lst] ##update with the match types!


    # print(lst)
    for i in range(len(lst)):
        # print(lst[i][1])
        min_lst_start = min([b[0] for b in lst[i][1]])
        max_lst_end = max([b[1] for b in lst[i][1]])

        ##exact_match!
        if item == lst[i]:
            all_match_types[i] = 'EXACT_MATCH'

        ##OVERLAP MATCH!
        elif (lst[i][0] in item[0] or item[0] in lst[i][0]) and ((min_item_start <= min_lst_start and max_item_end >= max_lst_end) or (min_item_start >= min_lst_start and max_item_end <= max_lst_end)):
            # print('OVERLAPPING!!!')
            # #
            # # print(i)
            # print(lst[i])
            # print(item)
            # print(min_item_start, max_item_end)
            # print(min_lst_start, max_lst_end)

            # return 'OVERLAP', i
            all_match_types[i] = 'OVERLAP_MAX'

        ##MAIN CATEGORY MATCH - if spans match and then the main category matches either one of the 2 or both match the main category
        elif item[1] == lst[i][1]:
            # print('got here!')
            # print(item[0], lst[i][0], lst[i][1])

            if (all_lc_it_dict.get(item[0]) and lst[i][0] in all_lc_it_dict[item[0]]) or (all_lc_it_dict.get(lst[i][0]) and item[0] in all_lc_it_dict[lst[i][0]]) or (all_lc_it_dict.get(item[0]) and all_lc_it_dict.get(lst[i][0]) and all_lc_it_dict[item[0]] == all_lc_it_dict[lst[i][0]]): #or (item[0] in all_lc_it_dict.keys() and lst[i][0] in all_lc_it_dict.keys()):
                # print('and here!')
                # print('MAIN CATEGORY MATCH!')
                # print(item)
                # print(lst[i])
                all_match_types[i] = 'MAIN_CATEGORY'

            # raise Exception('HOLD for main category!')


        else:
            pass

    # return False, None  ##otherwise if no overlap!
    # print('all match types:', all_match_types)
    node_value = (item_annotator, item_annotation_id, item)
    edges_list = []
    for m, match_type in enumerate(all_match_types):
        if match_type:
            # print(match_type)
            # print(lst_annotator)

            edges_list += [((lst_annotator, lst_annotation_id[m], lst[m]), match_type)]
        else:
            pass
    # print('nodes list:', nodes_list)
    # print('edges list:', edges_list)


    # return all_match_types
    # return overlap_match_indices_list
    return node_value, edges_list



# xml_creation(article, combo_annotators, xml_dict, IAA_output_path)
# xml_creation(pmc_doc_path, all_occurrence_dict, xml_output_path, weird_lcs)
def xml_creation(article, pmc_doc_path, combo_annotators, xml_dict, xml_output_path):
    """
	Create a new xml file of annotations based on the regex automatic preprocessing for one document at a time to paralellize
	:param article: article name that we are outputing the information
	:param pmc_doc_path: path to the txt files to get the whole text
	:param combo_annotators: a list of the annotators
	:param xml_dict: a dictionary from annotator -> (it, annot list)
	:param xml_output_path: the output file path for the xml files (ideally to the Annotations folder for knowtator)
	:return:


	<?xml version="1.0" encoding="UTF-8" standalone="no"?>
	<knowtator-project>
	  <document id="PMC6056931.nxml.gz" text-file="PMC6056931.nxml.gz.txt">
		<annotation annotator="Default" id="PMC6056931.nxml.gz-1" type="identity">
		  <class id="important"/>
		  <span end="192" id="PMC6056931.nxml.gz-2" start="183">important</span>
		</annotation>
	  </document>
	</knowtator-project>

	"""

    ##FILE OUTPUT NAME
    # print(pmc_doc_path)
    pmc_output_name = '%s.nxml.gz' % article
    print(pmc_output_name)

    string_combo_annotators = ''
    for a in combo_annotators:
        string_combo_annotators += '_%s' % a

    string_combo_annotators = string_combo_annotators[1:]

    pmc_doc_file = open('%s%s.nxml.gz.txt' % (pmc_doc_path, article), 'r')
    pmc_full_text = pmc_doc_file.read()

    ##CREATE THE XML FILE WITH HEADERS AND STRUCTURE
    ##TODO: need to add the encoding and standalone as node declarations!!!

    # SET THE ELEMENTS OF THE TREE:

    knowtator_project = ET.Element('knowtator-project')  # root element - tree
    doc_element = ET.SubElement(knowtator_project, 'document')

    ##WITHIN THE DOCUMENT SET ALWAYS

    ##ADD IN EACH ANNOTATION - MAKING SURE TO TAKE ONLY ONES WITH OCCURRENCES OF LCS
    # PUT IN TEXT - SET = ADDING AN ATTRIBUTE
    # all_occurrence_dict[(ontology_cue, ignorance_type)] = [regex_cue, cue_occurrence_list]

    doc_element.set('id', '%s' % (pmc_output_name))
    doc_element.set('text-file', '%s' % (pmc_output_name + '.txt'))

    ##sort the xml_dict by starts to make it easier to read:
    sorted_xml_dict = []  # [possible annotators, ignorance type, annot_list, start (sorting)]
    for a in xml_dict.keys():
        # print(a, xml_dict[a])
        for b in range(len(xml_dict[a])):
            # print(xml_dict[a][b][0])
            # print(xml_dict[a][b][1])
            # print(xml_dict[a][b][1][1][0][0])

            sorted_xml_dict += [[a, xml_dict[a][b][0], xml_dict[a][b][1], xml_dict[a][b][1][1][0][0]]]

    sorted_xml_dict = sorted(sorted_xml_dict, key=lambda x: x[3])
    # print(sorted_xml_dict)

    ##loop over all occurrences to get them all under the documents: # (ontology_cue, ignorance_type, index_to_keep) -> [regex, occurrences_list]
    iterator = 1
    for s in range(len(sorted_xml_dict)):
        # print(xml_dict[a])

        a = sorted_xml_dict[s][0]
        ignorance_type, annot_list = (sorted_xml_dict[s][1], sorted_xml_dict[s][2])
        lexical_cue = annot_list[0]  # cue in the ontology of ignorance
        cue_occurrence_list = annot_list[1]
        # print(cue_occurrence_list)

        annotation = ET.SubElement(doc_element, 'annotation')
        class_id = ET.SubElement(annotation, 'class')
        class_id.set('id', '%s' % (lexical_cue))
        annotation.set('annotator', a)
        annotation.set('id', '%s-%s' % (pmc_output_name, iterator))
        annotation.set('type', 'identity')

        for c in range(len(cue_occurrence_list)):
            start_final = cue_occurrence_list[c][0]
            end_final = cue_occurrence_list[c][1]

            # print(pmc_full_text[start:end])
            # print(all_starts)
            # print(all_ends)

            span = ET.SubElement(annotation, 'span')

            span.set('end', '%s' % (end_final))
            span.set('id', '%s-%s' % (pmc_output_name, iterator))
            span.set('start', '%s' % (start_final))
            span.text = '%s' % pmc_full_text[start_final:end_final]

            iterator += 1

    ##OUTPUT THE XML FILE TO THE ANNOTATIONS FILE

    xml_annotations_file = minidom.parseString(ET.tostring(knowtator_project)).toprettyxml(indent="   ")
    with open('%s%s.xml.%s.xml' % (xml_output_path, pmc_output_name, string_combo_annotators), "w") as file_output:
        file_output.write(xml_annotations_file)




def find_node_BFS(graph, items_to_find):
    # print('items to find', items_to_find)
    # for i in items_to_find:
        # print(i.get_value())

    explored = []
    # keep track of nodes to be checked
    queue = []
    for hn in graph:
        # print('head node', hn, hn.get_value())
        queue += [hn]
        # keep looping until there are nodes still to be checked
        while queue:
            # pop shallowest node (first node) from queue
            # print('queue', queue)
            # print('explored', explored)
            node = queue.pop(0)

            # print('node:', node, type(node))#, node.get_value())


            ##make sure it is not already explored
            if node not in explored:
                # print('node', node, node.get_value())
                # print('node value', node.get_value())
                # print('node tuple:', node_tuple)
                if node not in items_to_find:
                    # add node to list of checked nodes
                    explored.append(node)
                    neighbours = node.get_edges()  # list of edges with the matching type
                    # print('all neighbors', neighbours)


                    # add neighbours of node to queue
                    if neighbours:
                        for neighbour in neighbours:
                            # print('neighbor', neighbour) #,neighbour.get_value(), neighbour.get_edges())
                            if isinstance(neighbour, tuple):
                                neighbour_updated = neighbour[0]
                            else: #node!
                                # # print(neighbour)
                                # neighbour_updated = neighbour
                                raise Exception('ERROR: SHOULD ALWAYS BE TUPLES THAT INCLUDE THE MATCH TYPE!')

                            queue.append(neighbour_updated) #we don't want the matching type to keep looping through
                    else:
                        pass

                ##we found the node in the graph head nodes
                else:
                    # print('HERE!')
                    # raise Exception('hold please!')
                    return node
            else:
                pass


    return 'NEW_HEAD_NODE'

def output_BFS(ignorance_type, all_lc_it_dict, graph, xml_dict, IAA_output_file):
    #xml_dict: # annotator -> (it, annot_list)
    #graph: list of head nodes
    #IAA_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' %('ignorance type', 'total annotations', 'exact matches', 'overlapping matches', 'main category matches', 'mismatches', 'percent exact matches', 'percent matches')) #all information, total_annotations = denominator, percent matches includes overlaps and main category

    # print('START OUTPUT BFS TRAVERSE!')
    annotator_hierarchy = ['MAIN_CATEGORY', 'OVERLAP_MAX', 'EXACT_MATCH'] #order of taking the annotator if more than one - use indices and take minimum to figure out annotator
    it_exact_matches = 0
    it_overlapping_matches = 0
    it_main_category_matches = 0
    it_mismatches = 0
    # match_count_dict = {'MAIN_CATEGORY': it_main_category_matches, 'OVERLAP_MAX': it_overlapping_matches, 'EXACT_MATCH':it_exact_matches}

    # print('graph head nodes:', graph.get_head_nodes())

    # explored = []
    # queue = [] # # keep track of nodes to be checked

    for hn in graph.get_head_nodes():
        explored = []
        queue = [] # keep track of nodes to be checked
        if hn.get_edges():
            # print('HEAD NODE!', hn, hn.get_value())
            ##find the correct match type (annotator) and the max annotation to take
            final_match_type = '' #annotator for xml_dict
            all_span_len = [] #the span length of each node
            final_annot_list = [] #TODO: make sure this is the correct list situation
            current_match_type_list = []


            queue += [hn]
            # keep looping until there are nodes still to be checked
            while queue:
                # pop shallowest node (first node) from queue
                # print('queue', queue)
                # print('explored', explored)
                node = queue.pop(0)
                # print('node', node.get_value())

                ##make sure it is not already explored
                if node not in explored:
                    #add the information to our output
                    current_span_list = node.get_value()[2][-1]
                    current_span_len = max([s[1] for s in current_span_list]) - min([s[0] for s in current_span_list])
                    # print('current span len', current_span_len)
                    # print('final_span_len', final_span_len)
                    ##capture all span lengths
                    all_span_len += [current_span_len]

                    # if current_span_len > final_span_len:
                    #     final_annot_list = node.get_value()[-1] #TODO: make sure this is the correct list situation
                    # else:
                    #     pass


                    #continue with the BFS
                    explored.append(node)
                    neighbours = node.get_edges()  # list of edges with the matching type
                    # print('neighbors:', neighbours)


                    # add neighbours of node to queue with edges
                    if neighbours:

                        for neighbour in neighbours:
                            if isinstance(neighbour, tuple):
                                node_neighbour = neighbour[0]
                                current_match_type_list += [neighbour[1]]
                            else:  # node!
                                raise Exception('ERROR: SHOULD ALWAYS BE TUPLES THAT INCLUDE THE MATCH TYPE!')
                            queue.append(node_neighbour)

                            # print('neighbor', updated_neighbour, updated_neighbour.get_value(), updated_neighbour.get_edges())

                            # current_match_type_list += [neighbour[-1]] #TODO: this may need to come back
                            # print('current_match_type_list', current_match_type_list)
                    else:
                        pass


            ##output the one with the max span or in the hierarchy (MC > OM > EM)

            # if 'OVERLAP_MAX' in current_match_type_list or 'MAIN_CATEGORY' in current_match_type_list:
            #     print('current_match_type_list', current_match_type_list)
            #     print('explored', explored)
            #     raise Exception('HOLD!')
            if current_match_type_list:
                # print('current_match_type_list', current_match_type_list)

                ##main category match

                ##if (all_lc_it_dict.get(item[0]) and lst[i][0] in all_lc_it_dict[item[0]]) or (all_lc_it_dict.get(lst[i][0]) and item[0] in all_lc_it_dict[lst[i][0]]) or (all_lc_it_dict.get(item[0]) and all_lc_it_dict.get(lst[i][0]) and all_lc_it_dict[item[0]] == all_lc_it_dict[lst[i][0]]) or (item[0] in all_lc_it_dict.keys() and lst[i][0] in all_lc_it_dict.keys()):
                if 'MAIN_CATEGORY' in current_match_type_list:
                    final_annotator = 'MAIN_CATEGORY'
                    for ex in explored:
                        # print('ignorance_type', ignorance_type)
                        # print(ex.get_value())
                        # print(ex.get_value()[2][0])
                        # print(all_lc_it_dict[ex.get_value()[2][0]])
                        if ignorance_type == ex.get_value()[2][0]:
                            # print('EXPLORED NODES VALUES',ex.get_value())
                            final_annot_list = ex.get_value()[2]
                            break
                        elif ignorance_type in all_lc_it_dict[ex.get_value()[2][0]]:
                            # print('EXPLORED NODES VALUES', ex.get_value())
                            # print('got here!')
                            final_annot_list = ex.get_value()[2]
                            break
                        else:
                            pass

                    # if ignorance_type == 'question_answered_by_this_work':
                    if len(final_annot_list) == 0:
                        print('ERRORS WITH MAIN CATEGORY OUTPUT_BFS')
                        print(ignorance_type)
                        print(ex.get_value())
                        print(ex.get_value()[2][0])
                        print(all_lc_it_dict[ex.get_value()[2][0]])

                        print(final_annot_list)

                        raise Exception('ERROR WITH MAIN CATEGORY FINAL ANNOT LIST CAPTURING IT!')
                    # print('FOUND THE MAIN CATEGORY!')
                    # print(final_annotator)
                    # print(final_annot_list)
                    # raise Exception('HOLD!')
                ##overlap max match
                elif 'OVERLAP_MAX' in current_match_type_list:
                    final_annotator = 'OVERLAP_MAX'
                    max_span_index = all_span_len.index(max(all_span_len))  # first index of the max span (doesnt matter for exact match)
                    final_annot_list = explored[max_span_index].get_value()[2]
                ##exact match
                elif 'EXACT_MATCH' in current_match_type_list:
                    final_annotator = 'EXACT_MATCH'
                    final_annot_list = explored[0].get_value()[2]
                #should not get here!
                else:
                    raise Exception('ERROR WITH OTHER ANNOTATORS CREEPING IN!')

                # print('FOUND THE correct category!')
                # print(final_annotator)
                # print(final_annot_list)
                # raise Exception('HOLD!')

                # current_match_type_set = set(current_match_type_list)
                # print('current match type set',current_match_type_set)
                # if len(current_match_type_set) == 1:
                #     final_annotator = current_match_type_set[0]
                #     if
                #     max_span_index = all_span_len.index(max(all_span_len)) #first index of the max span (doesnt matter for exact match)

                # annotator_index = min([annotator_hierarchy.index(c) for c in current_match_type_set])
                # final_annotator = annotator_hierarchy[annotator_index]


                # print(final_annotator, (ignorance_type, final_annot_list))
                xml_dict[final_annotator] += [(ignorance_type, final_annot_list)]
                if final_annotator == 'EXACT_MATCH':
                    it_exact_matches += 1
                elif final_annotator == 'OVERLAP_MAX':
                    it_overlapping_matches += 1
                elif final_annotator == 'MAIN_CATEGORY':
                    it_main_category_matches += 1
            else:
                raise Exception('ERROR: NO NEIGHBORS!')
                pass



        ##lone head node
        else:
            # xml_dict: # annotator -> (it, annot_list)
            annotator, annotation_id, annot_list = hn.get_value()
            xml_dict[annotator] += [(ignorance_type, annot_list)]
            # print(annotator, (ignorance_type, annot_list))
            it_mismatches += 1


    # print('all explored', len(explored))

    # print('final dictionary!', xml_dict)
    # print(it_exact_matches, it_overlapping_matches, it_main_category_matches, it_mismatches)

    if IAA_output_file:
        IAA_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' %('ignorance type', 'total annotations', 'exact matches', 'overlapping matches', 'main category matches', 'mismatches', 'percent exact matches', 'percent matches')) #all information, total_annotations = denominator, percent matches includes overlaps and main category
        IAA_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\n\n' %(ignorance_type, len(graph.get_head_nodes()), it_exact_matches, it_overlapping_matches, it_main_category_matches, it_mismatches, float(it_exact_matches)/float(len(graph.get_head_nodes())), float(it_exact_matches+it_overlapping_matches+it_main_category_matches)/float(len(graph.get_head_nodes()))))

    else:
        pass


    if sum([it_exact_matches, it_overlapping_matches, it_main_category_matches, it_mismatches]) != len(graph.get_head_nodes()):
        raise Exception('ERROR WITH CAPTURING ALL MATCHES FOR IGNORANCE TYPE OUTPUT!')
    else:
        pass

    return xml_dict, it_exact_matches, it_overlapping_matches, it_main_category_matches, it_mismatches




class Node:
    def __init__(self, value, edges):
        self.value = value
        self.edges = edges
    def get_value(self):
        return self.value

    def get_edges(self):
        return self.edges #tuple of neighbors and match status with them [(neighbor, match_type)]

    def add_edges(self, new_node_edges):
        #a list of the tuples to add
        # for new_edge in new_edges:
        #     self.edges += [new_edge]
        if self.edges:
            self.edges += new_node_edges
        else:
            self.edges = new_node_edges

    def delete_edges(self, del_edges):
        #del edges = a list of the tuples to get rid of
        # print(self.edges)
        # print(del_edges)
        for d_edge in del_edges:
            if self.edges:
                d_edge_index = self.edges.index(d_edge)
                self.edges.pop(d_edge_index)
            else:
                pass


    def __eq__(self, other):
        #match on value not edges
        if not isinstance(other, Node):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.get_value() == other.get_value() #and self.get_edges() == other.get_edges()


class Graph:
    def __init__(self, ignorance_type):
        self.ignorance_type = ignorance_type
        self.head_nodes = [] #list of the headnodes of type node
        self.all_nodes_values = []

    def get_head_nodes(self):
        return self.head_nodes

    def insert_nodes(self, value, node_edges):
        #node_edges = [(edge_node, match_type)]
        # print('node edges', node_edges)
        if node_edges:
            ##all the values of nodes we have seen
            if value not in self.all_nodes_values:
                self.all_nodes_values.append(value)
            else:
                pass
                # raise Exception('VALUE ALREADY IN ALL NODE VALUES')

            for ne in node_edges:
                if ne[0].get_value() not in self.all_nodes_values:
                    self.all_nodes_values.append(ne[0].get_value())

            ##insert the node into the graph if new, otherwise add edges to the graph
            node = Node(value, node_edges)
            if not self.head_nodes:
                self.head_nodes += [node]
            else:
                all_edges = node.get_edges() #all nodes!
                # print('all_edges', all_edges)
                items_to_find = [node]
                for e in all_edges:
                    items_to_find += [e[0]] ##the nodes to find without the match types

                # items_to_find = [node] + all_edges
                # print('ITEMS TO FIND PLEASE!', items_to_find)
                ##use BFS to see if we need to add things to the nodes!
                node_connection = find_node_BFS(self.head_nodes, items_to_find)
                if node_connection == 'NEW_HEAD_NODE':
                    self.head_nodes += [node]
                else:
                    #node_connection = a node that is in the path from items_to_find!
                    #the root node of the tree we want to insert
                    if node_connection == node:
                        # print('node edges', node_edges)
                        node_connection.add_edges(node_edges) #TODO - tuples

                    ## not the root node of the tree we are trying to insert - seems good!
                    else:
                        # print('node to add', value, node_edges)
                        # for edge in node_edges:
                        #     print('EDGE', edge[0].get_value())
                        # node_connection_index = items_to_find.index(node_connection)
                        # print('index of connecting node', node_connection_index)


                        for edge in node.get_edges():
                            if edge[0] == node_connection:
                                edge_to_switch = edge #tuple with match_type
                            else:
                                pass
                        ##delete the original connection and add a new edge
                        node.delete_edges([edge_to_switch])
                        # edge_to_switch[0].add_edges([(node, edge_to_switch[1])]) #reversing the edges
                        node_connection.add_edges([(node, edge_to_switch[1])]) #add the reverse edge into the current tree using the node connection
                        # print('node connection info')
                        # print(node_connection.get_value())
                        # print(node_connection.get_edges())
                        # for edge in node_connection.get_edges():
                            # print('new_edge:', edge[0].get_value())
                            # print(edge[0].get_edges())
                            # for e in edge[0].get_edges():
                            #     print(e[0].get_value())
                        # raise Exception('MAKE SURE THE NODE CONNECTION WORKS!')
        else:
            node = Node(value, node_edges)
            self.head_nodes += [node]
            if value not in self.all_nodes_values:
                self.all_nodes_values.append(value)





def graph_matches(ignorance_type, annot_list, smallest_index, all_lc_it_dict, possible_annotators, annotation_ids_list, xml_dict, IAA_output_file):
    annotation_graph = Graph(ignorance_type)
    # print('possible annotators:',possible_annotators)
    current_annotator_list = possible_annotators[3:]
    # print('current annotators list:', current_annotator_list)
    smallest_annot = annot_list[smallest_index]
    smallest_annotator = current_annotator_list[smallest_index]
    smallest_annotation_id = annotation_ids_list[smallest_index]

    ##need to ensure that we capture everything!
    for i, a in enumerate(smallest_annot):
        current_annotation_id = smallest_annotation_id[i]
        for j, lst_annot in enumerate(annot_list):
            if j != smallest_index:
                lst_annotator = current_annotator_list[j]
                lst_annotation_id = annotation_ids_list[j]
                node_value, edges_list = fuzzy_match(a, smallest_annotator, current_annotation_id, lst_annot, lst_annotator,lst_annotation_id, all_lc_it_dict)
                # print('nodes value', node_value)
                # print('edges list', edges_list)
                # item_node = Node(node_value, edges_list)
                edge_node_list = []
                for edge_value in edges_list:
                    edge_node = Node(edge_value[0], None)
                    edge_node_list += [(edge_node, edge_value[1])]
                annotation_graph.insert_nodes(node_value, edge_node_list)
                # print('current annotation graph', annotation_graph.get_head_nodes())

    # print('annotation graph head nodes', annotation_graph.get_head_nodes())
    # head_nodes = []
    # for head_node in annotation_graph.get_head_nodes():
    #     head_nodes += [(head_node.get_value(), head_node.get_edges())]
    # print('all head nodes:', head_nodes)
    # print('all node values', annotation_graph.all_nodes_values, len(annotation_graph.all_nodes_values))

    if len(smallest_annot) != [a[0] for a in annotation_graph.all_nodes_values].count(smallest_annotator):
        raise Exception('ERROR WITH THE SMALLEST ANNOTATION LOOP!')
    else:
        pass


    ##adding lone head nodes! TODO: error here!
    for i, a in enumerate(current_annotator_list):
        if i != smallest_index:
            # print(a, len(annotation_ids_list[i]), len(annot_list[i]))
            for j, id in enumerate(annotation_ids_list[i]):
                current_annot_list = annot_list[i][j]
                if (a, id, current_annot_list) not in annotation_graph.all_nodes_values:
                    lone_head_node_value = (a, id, annot_list[i][j])
                    # if 'ELIZABETH' in lone_head_node_value and 'trend' in lone_head_node_value[-1]:
                    #     print('lone head node value', lone_head_node_value)
                    annotation_graph.insert_nodes(lone_head_node_value, None)


    ##check that all nodes are captured by the graph!
    # print('all node values', sum([len(a) for a in annot_list]), len(annotation_graph.all_nodes_values))
    # print(annotation_graph.all_nodes_values)
    if sum([len(a) for a in annot_list]) != len(annotation_graph.all_nodes_values):
        # print([len(a) for a in annot_list])
        for i, c in enumerate(current_annotator_list):
            if len(annot_list[i]) != sum([c in annot for annot in annotation_graph.all_nodes_values]):
                print('missing an annotation from:', c, len(annot_list[i]), sum([c in annot for annot in annotation_graph.all_nodes_values]))
                # print(annot_list[i])
                annot_list_copy = copy.deepcopy(annot_list[i])
                # print([c in annot for annot in annotation_graph.all_nodes_values])
                for node in annotation_graph.all_nodes_values:
                    if c in node:
                        # print(node)
                        if node[-1] in annot_list_copy:
                            # print('got here')
                            annot_list_copy.pop(annot_list_copy.index(node[-1]))
                        else:
                            pass
                print('THE MISSING PIECE!')
                print(annot_list_copy)
                for a in annot_list_copy:
                    print(a, annot_list[i].index(a))
                print(i, smallest_index)
                if i == smallest_index:
                    print('failure with smallest_index')
                else:
                    print('failure with adding lone_nodes')
            # print('elizabeth', sum(['ELIZABETH' in annot for annot in annotation_graph.all_nodes_values]))
            # print('mayla', sum(['MAYLA' in annot for annot in annotation_graph.all_nodes_values]))
        print('ERROR', sum([len(a) for a in annot_list]), len(annotation_graph.all_nodes_values))
        raise Exception('ERROR CAPTURING ALL ANNOTATIONS!')
    else:
        pass

    # print('annotation graph head nodes', annotation_graph.get_head_nodes())
    head_nodes = []
    for head_node in annotation_graph.get_head_nodes():
        head_nodes += [(head_node.get_value(), head_node.get_edges())]
    # print('all head nodes:', head_nodes)
    # print('all node values', annotation_graph.all_nodes_values, len(annotation_graph.all_nodes_values))

    ##total annotations for this ignorance type
    # it_total_annotations = len(annotation_graph.all_nodes_values) #full total annotations
    it_total_annotations = len(annotation_graph.get_head_nodes()) #the overlapping information!

    ##traverse the tree using BFS to figure out all the match types
    ##TODO: grab all the matches to be able to create xml_dict!
    # print()
    xml_dict, it_exact_matches, it_overlapping_matches, it_main_category_matches, it_mismatches = output_BFS(ignorance_type, all_lc_it_dict, annotation_graph, xml_dict, IAA_output_file)

    if it_total_annotations != sum([it_exact_matches, it_overlapping_matches, it_main_category_matches, it_mismatches]):
        print('total it annotations:', it_total_annotations)
        print(it_exact_matches, it_overlapping_matches, it_main_category_matches, it_mismatches)
        raise Exception('ERROR WITH BFS OUTPUT TOTAL SUMS!')

    return xml_dict, it_total_annotations, it_exact_matches, it_overlapping_matches, it_main_category_matches, it_mismatches


##only with 2 annotators max
def calculate_F1_IAA(article, xml_dict, c, annotators, combo_annotation_article_dicts):
    ##xml_dict: annotator -> [(ignorance_type, [annot_list])]
        ##annot_list = ['text', [(spans)]]
    # print(article)
    # print(xml_dict.keys())
    # print(c)
    two_annotators = [annotators[i] for i in c]
    # print('two annotators', two_annotators)

    # print(xml_dict)
    # print(combo_annotation_article_dicts)


    ##fuzzy match F1
    fuzzy_tp_class = 0
    fuzzy_tp_subject = 0

    ##exact match only F1
    tp_class = 0
    tp_subject = 0

    ##dict of the counts for the people annotators
    fuzzy_two_annotator_counts = {} #annotator -> counts of lone annotations
    for t in two_annotators:
        fuzzy_two_annotator_counts[t] = [0,0] #class, subject counts


    ##start by going through the xml_dict and use it to compute stuff
    for annotator in xml_dict.keys():
        # print(annotator, len(xml_dict[annotator]))
        #EXACT MATCHES
        if annotator == 'EXACT_MATCH':
            for (it, annot_list) in xml_dict[annotator]:

                if it != 'subject_scope':
                    tp_class += 1
                    fuzzy_tp_class += 1
                else:
                    tp_subject += 1
                    fuzzy_tp_subject += 1

        #FUZZY MATCHES
        elif annotator in ['OVERLAP_MAX', 'MAIN_CATEGORY']:
            # print('got here', annotator, it)
            for (it, annot_list) in xml_dict[annotator]:
                if it != 'subject_scope':
                    fuzzy_tp_class += 1
                else:
                    fuzzy_tp_subject += 1

        ##two people annotators
        elif annotator in two_annotators:
            for (it, annot_list) in xml_dict[annotator]:
                if it != 'subject_scope':
                    #class
                    fuzzy_two_annotator_counts[annotator][0] += 1
                else:
                    #subject
                    fuzzy_two_annotator_counts[annotator][1] += 1
        else:
            raise Exception('ERROR: WEIRD ANNOTATOR IN THIS SET THAT SHOULD NOT EXIST OR NEEDS TO BE ADDED!')


    ##calculate fuzzy F1
    fuzzy_full_PR_class = []
    fuzzy_full_PR_subject = []
    for t in two_annotators:
        # print(fuzzy_two_annotator_counts[t])
        # print(fuzzy_tp_class)
        try:
            fuzzy_PR_class = float(fuzzy_tp_class)/float(fuzzy_tp_class+fuzzy_two_annotator_counts[t][0])
        except ZeroDivisionError:
            fuzzy_PR_class = 0
        if t == 'PREPROCESS':
            fuzzy_PR_subject = 0
        else:
            try:
                fuzzy_PR_subject = float(fuzzy_tp_subject)/float(fuzzy_tp_subject+fuzzy_two_annotator_counts[t][1])
            except ZeroDivisionError:
                fuzzy_PR_subject = 0

        fuzzy_full_PR_class += [fuzzy_PR_class]
        fuzzy_full_PR_subject += [fuzzy_PR_subject]


    # print(fuzzy_full_PR_class)
    # print(fuzzy_full_PR_subject)
    try:
        fuzzy_F1_class = (2 * float(fuzzy_full_PR_class[0]) * float(fuzzy_full_PR_class[1])) / float(fuzzy_full_PR_class[0] + fuzzy_full_PR_class[1])
    except ZeroDivisionError:
        fuzzy_F1_class = 0

    if 'PREPROCESS' in two_annotators:
        fuzzy_F1_subject = 'NA'
    else:
        try:
            fuzzy_F1_subject = (2 * float(fuzzy_full_PR_subject[0]) * float(fuzzy_full_PR_subject[1])) / float(fuzzy_full_PR_subject[0] + fuzzy_full_PR_subject[1])
        except ZeroDivisionError:
            fuzzy_F1_subject = 0





    ##full F1 measure - only exact matches
    if fuzzy_tp_class == tp_class:
        F1_class = fuzzy_F1_class
    else:
        pass

    if fuzzy_tp_subject == tp_subject:
        F1_subject = fuzzy_tp_subject
    else:
        pass


    # print(len(combo_annotation_article_dicts))
    # print('XML DICT EXACT MATCH', xml_dict['EXACT_MATCH'])
    # print('XML DICT EXACT MATCH', len(xml_dict['EXACT_MATCH']))

    ##dict of the counts for the people annotators
    two_annotator_counts = {}  # annotator -> counts of lone annotations
    for t in two_annotators:
        two_annotator_counts[t] = [0, 0]  # class, subject counts

    for i, a in enumerate(two_annotators):
        # PR_class = 0
        # PR_subject = 0
        confirm_tp = 0

        # print(a)
        # print(combo_annotation_article_dicts[i])


        ##TODO: loop over annotations and don't count the exact matches but everything else is a mismatch
        #ignorance types
        for it in combo_annotation_article_dicts[i].keys():
            for annotations in combo_annotation_article_dicts[i][it]:
                annot_id, text, spans = annotations

                if (it, [text, spans]) in xml_dict['EXACT_MATCH']:
                    # print('exact_match', it, [text, spans])
                    confirm_tp += 1
                else:
                    if it != 'subject_scope':
                        # PR_class += 1
                        two_annotator_counts[a][0] += 1
                    else:
                        two_annotator_counts[a][1] += 1
                        # PR_subject += 1



        if confirm_tp != len(xml_dict['EXACT_MATCH']):
            raise Exception('ERROR WITH IDENTIFYING EXACT MATCHES DURING ANNOTATION LOOKOVER!')
        else:
            pass

        # print('PR info', two_annotator_counts[a])

        ##calculate full F1
        full_PR_class = []
        full_PR_subject = []
        for t in two_annotators:
            # print(two_annotator_counts[t])
            # print(tp_subject)
            try:
                PR_class = float(tp_class) / float(tp_class + two_annotator_counts[t][0])
            except ZeroDivisionError:
                PR_class = 0

            if t == 'PREPROCESS':
                PR_subject = 0
            else:
                try:
                    PR_subject = float(tp_subject) / float(tp_subject + two_annotator_counts[t][1])
                except ZeroDivisionError:
                    PR_subject = 0

            full_PR_class += [PR_class]
            full_PR_subject += [PR_subject]

        # print(full_PR_class)
        # print(full_PR_subject)
        try:
            F1_class = (2 * float(full_PR_class[0]) * float(full_PR_class[1])) / float(full_PR_class[0] + full_PR_class[1])
        except ZeroDivisionError:
            F1_class = 0

        if 'PREPROCESS' in two_annotators:
            F1_subject = 'NA'
        else:
            try:
                F1_subject = (2 * float(full_PR_subject[0]) * float(full_PR_subject[1])) / float(full_PR_subject[0] + full_PR_subject[1])

            except ZeroDivisionError:
                F1_subject = 0


    # print('fuzzy F1 class:', fuzzy_F1_class)
    # print('fuzzy F1 subject:', fuzzy_F1_subject)
    # print('F1 class', F1_class)
    # print('F1 subject', F1_subject)

    return fuzzy_F1_class, fuzzy_F1_subject, fuzzy_two_annotator_counts, fuzzy_tp_class, fuzzy_tp_subject, F1_class, F1_subject, two_annotator_counts, tp_class, tp_subject

def calculate_IAA(all_ignorance_types, all_lc_it_dict, combo_annotators, combo_annotation_article_dicts, article, IAA_output_path):
    ##annotation dict: #ignorance type -> [[annotation_id, ont_lc, [(spans) sorted by starts]]]

    ##totals!
    total_annotations_class = 0  # the set of all unique annotations between the 2 of them
    total_annotations_subject = 0

    ##exact match - class and span
    article_total_exact_match_class = 0
    article_total_exact_match_subject = 0

    ##overlapping - class and span
    article_total_overlap_match_class = 0
    article_total_overlap_match_subject = 0

    ##main category match - class and span
    article_total_main_category_match_class = 0
    article_total_main_category_match_subject = 0

    ##mismatches - class and span
    article_total_mismatches_class = 0
    article_total_mismatches_subject = 0


    string_combo_annotators = ''
    for a in combo_annotators:
        string_combo_annotators += '_%s' % a

    string_combo_annotators = string_combo_annotators[1:]
    # print('combo info', string_combo_annotators)

    ##xml creation information per article and annotators
    possible_annotators = ['EXACT_MATCH', 'OVERLAP_MAX', 'MAIN_CATEGORY']
    possible_annotators += combo_annotators
    # print(possible_annotators)
    xml_dict = {}  # annotator -> (it, annot_list)
    for pa in possible_annotators:
        xml_dict[pa] = []

    with open('%sIAA_%s_%s_%s.txt' % (IAA_output_path, article, string_combo_annotators, date.today()),
              'w+') as IAA_output_file:

        IAA_output_file.write('%s\t%s\n\n' % ('ARTICLE:', article))
        # IAA_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' %('ignorance type', 'total annotations', 'exact matches', 'overlapping matches', 'main category matches', 'mismatches', 'percent exact matches', 'percent matches'))
        # print('all ignorance types',all_ignorance_types)

        for it in all_ignorance_types:
            # if it == 'future_work': #TODO: generalize!
            # print('ignorance type:', it)

            ##check if match on ignorance type for all annotation_article_dicts for each annotator - if yes, all trues
            if_it_exists_list = [True if ad.get(it) else False for ad in combo_annotation_article_dicts]
            # print(it, if_it_exists_list)



            ##all annotators have the ignorance type
            if len(list(set(if_it_exists_list))) == 1 and list(set(if_it_exists_list))[0] == True:
                # print('GOT HERE!')
                IAA_output_file.write('%s\t%s\n' % ('CURRENT IGNORANCE TYPE:', it))

                it_info_list = []
                annotation_ids_list = []
                annot_list = []


                for c in range(len(combo_annotators)):
                    IAA_output_file.write(
                        '%s %s:\t%s\n' % ('total annotations for annotator', combo_annotators[c],
                                          len(combo_annotation_article_dicts[c][it])))

                    it_info_list += [combo_annotation_article_dicts[c][it]]
                    # print('annotation article dicts:', combo_annotation_article_dicts[c][it])
                    annotation_id, annot = split_lists(combo_annotation_article_dicts[c][it])
                    # print('starting stuff:', annotation_id, annot)

                    #annotation_article_dict = {}  # ignorance type -> [[annotation_id, ont_lc, [(spans) sorted by starts]]]
                    #annot: [ont_lc, [(spans) sorted by starts]]]

                    annotation_ids_list += [annotation_id] #annotation id
                    annot_list += [annot] #[ont_lc, (spans)]

                # print('it info list', it_info_list)
                # print('annot list', annot_list)
                # print('annotation id list', annotation_ids_list)

                ##use the smaller list to find stuff in larger list for efficiency - depends on the ignorance type - sort on number of annotations
                len_it_info_list = [len(it_info) for it_info in it_info_list]
                len_it_info_list_sorted = sorted(range(len(len_it_info_list)), key=lambda k: len_it_info_list[k])  # indicies of sorted len_it_info_list (smallest to largest)
                smallest_index = len_it_info_list_sorted[0] #the smallest list
                # print('smallest index', smallest_index)

                ###TODO: Graph structer to capture everything! - xml_dict

                xml_dict, it_total_annotations, it_exact_matches, it_overlapping_matches, it_main_category_matches, it_mismatches = graph_matches(it, annot_list, smallest_index, all_lc_it_dict, possible_annotators, annotation_ids_list, xml_dict, IAA_output_file)

                ##FULL TOTAL INFORMATION FOR SUMMARY STATS PER ARTICLE!
                ##subject!
                if it == 'subject_scope':
                    total_annotations_subject += it_total_annotations
                    article_total_exact_match_subject += it_exact_matches
                    article_total_overlap_match_subject += it_overlapping_matches
                    article_total_main_category_match_subject += it_main_category_matches
                    article_total_mismatches_subject += it_mismatches

                ##class
                else:
                    total_annotations_class += it_total_annotations
                    article_total_exact_match_class += it_exact_matches
                    article_total_overlap_match_class += it_overlapping_matches
                    article_total_main_category_match_class += it_main_category_matches
                    article_total_mismatches_class += it_mismatches



                # raise Exception('HOLD!')

            #automatic mismatch if not all annotators have it and needs to be added to everything
            elif True in if_it_exists_list:
                for c, annotator in enumerate(combo_annotators):
                    if combo_annotation_article_dicts[c].get(it):
                        # print(combo_annotation_article_dicts[c][it]) ## ignorance type -> [[annotation_id, ont_lc, [(spans) sorted by starts]]]

                        for i, lone_annotation in enumerate(combo_annotation_article_dicts[c][it]):
                            # print('lone annotation', lone_annotation)
                            ont_lc = lone_annotation[1]
                            span_info = lone_annotation[2]
                            annot_list = [ont_lc, span_info]
                            xml_dict[annotator] += [(it, annot_list)]
                            if it == 'subject_scope':
                                total_annotations_subject += 1
                                article_total_mismatches_subject += 1
                            else:
                                total_annotations_class += 1
                                article_total_mismatches_class += 1

                        # print('xml_dict', xml_dict[annotator]) ## annotator -> (it, annot_list)


                        # raise Exception('HOLD!')

            ##all false - not in any annotations
            else:
                pass

    if total_annotations_class != sum([article_total_exact_match_class, article_total_overlap_match_class, article_total_main_category_match_class, article_total_mismatches_class]):
        # print(total_annotations_class)
        # print(article_total_exact_match_class, article_total_overlap_match_class, article_total_main_category_match_class, article_total_mismatches_class)

        raise Exception('ERROR WITH ANNOTATIONS CLASSES!')
    elif total_annotations_subject != sum([article_total_exact_match_subject, article_total_overlap_match_subject, article_total_main_category_match_subject, article_total_mismatches_subject]):
        raise Exception('ERROR WITH ANNOTATIONS SUBJECT!')

    # print('xml_dict', xml_dict)
    # print('TOTALS FOR ANNOTATIONS CLASS AND SUBJECT', total_annotations_class, total_annotations_subject)
    return total_annotations_class, total_annotations_subject, article_total_exact_match_class, article_total_exact_match_subject, article_total_overlap_match_class, article_total_overlap_match_subject, article_total_main_category_match_class, article_total_main_category_match_subject, article_total_mismatches_class, article_total_mismatches_subject, xml_dict


def calculate_span_overlap_IAA(all_ignorance_types, all_lc_it_dict, combo_annotators, combo_annotation_article_dicts, article, IAA_output_path):
    #most lenient score per article!

    ##annotation dict: #ignorance type -> [[annotation_id, ont_lc, [(spans) sorted by starts]]]

    ##totals!
    binary_total_annotations_class = 0  # the set of all unique annotations between the 2 of them
    binary_total_annotations_subject = 0

    ##exact match - class and span
    binary_article_total_exact_match_class = 0
    binary_article_total_exact_match_subject = 0

    ##overlapping - class and span
    binary_article_total_overlap_match_class = 0
    binary_article_total_overlap_match_subject = 0

    ##main category match - class and span
    binary_article_total_main_category_match_class = 0
    binary_article_total_main_category_match_subject = 0

    ##mismatches - class and span
    binary_article_total_mismatches_class = 0
    binary_article_total_mismatches_subject = 0



    ##xml creation information per article and annotators
    possible_annotators = ['EXACT_MATCH', 'OVERLAP_MAX', 'MAIN_CATEGORY']
    possible_annotators += combo_annotators
    # print(possible_annotators)

    string_combo_annotators = ''
    for a in combo_annotators:
        string_combo_annotators += '_%s' % a

    string_combo_annotators = string_combo_annotators[1:]

    binary_xml_dict = {}  # annotator -> (it, annot_list)
    for pa in possible_annotators:
        binary_xml_dict[pa] = []

    ##create the list of all the binary dictionaries for each annotator in combo_annotators
    binary_combo_annotation_article_dicts = []

    binary_ignorance_types = ['ignorance', 'subject_scope']
    binary_all_lc_it_dict = {}
    # print(type(all_lc_it_dict))
    for lc in all_lc_it_dict.keys():
        if binary_all_lc_it_dict.get(lc):
            binary_all_lc_it_dict[lc] += ['ignorance']
        else:
            binary_all_lc_it_dict[lc] = ['ignorance']



    for ad in combo_annotation_article_dicts:
        ##create the binary dictionary of just ignorance (combo of all ignorance categories) or subject scope
        binary_annotation_dict = {'ignorance': [], 'subject_scope': []}  # ignorance types = class or subject_scope
        for it in all_ignorance_types:
            if ad.get(it):
                ##suject scope
                if it == 'subject_scope':
                    binary_annotation_dict['subject_scope'] += ad[it]
                ##ignorance cue
                else:
                    binary_annotation_dict['ignorance'] += ad[it]
            else:
                pass
        binary_combo_annotation_article_dicts += [binary_annotation_dict]

    # print(binary_ignorance_types)
    # raise Exception('hold binary')
    for binary_it in binary_ignorance_types:
        ##check if match on ignorance type for all annotation_article_dicts for each annotator - if yes, all trues
        if_it_exists_list = [True if bad.get(binary_it) else False for bad in binary_combo_annotation_article_dicts]
        ##all annotators have the ignorance type
        if len(list(set(if_it_exists_list))) == 1 and list(set(if_it_exists_list))[0] == True:
            it_info_list = []
            annotation_ids_list = []
            annot_list = []

            for c in range(len(combo_annotators)):
                it_info_list += [binary_combo_annotation_article_dicts[c][binary_it]]
                # print('annotation article dicts:', binary_combo_annotation_article_dicts[c][binary_it])
                annotation_id, annot = split_lists(binary_combo_annotation_article_dicts[c][binary_it])
                # print('starting stuff:', annotation_id, annot)

                # annotation_article_dict = {}  # ignorance type -> [[annotation_id, ont_lc, [(spans) sorted by starts]]]
                # annot: [ont_lc, [(spans) sorted by starts]]]

                annotation_ids_list += [annotation_id]  # annotation id
                annot_list += [annot]  # [ont_lc, (spans)]

            # print('it info list', it_info_list)
            # print('annot list', annot_list)
            # print('annotation id list', annotation_ids_list)

            ##use the smaller list to find stuff in larger list for efficiency - depends on the ignorance type - sort on number of annotations
            len_it_info_list = [len(it_info) for it_info in it_info_list]
            len_it_info_list_sorted = sorted(range(len(len_it_info_list)), key=lambda k: len_it_info_list[
                k])  # indicies of sorted len_it_info_list (smallest to largest)
            smallest_index = len_it_info_list_sorted[0]  # the smallest list
            # print('smallest index', smallest_index)


            binary_xml_dict, it_total_annotations, it_exact_matches, it_overlapping_matches, it_main_category_matches, it_mismatches = graph_matches(
                binary_it, annot_list, smallest_index, binary_all_lc_it_dict, possible_annotators, annotation_ids_list, binary_xml_dict,
                None)

            ##FULL TOTAL INFORMATION FOR SUMMARY STATS PER ARTICLE!
            ##subject!
            if binary_it == 'subject_scope':
                binary_total_annotations_subject += it_total_annotations
                binary_article_total_exact_match_subject += it_exact_matches
                binary_article_total_overlap_match_subject += it_overlapping_matches
                binary_article_total_main_category_match_subject += it_main_category_matches
                binary_article_total_mismatches_subject += it_mismatches

            ##class - ignorance
            else:
                binary_total_annotations_class += it_total_annotations
                binary_article_total_exact_match_class += it_exact_matches
                binary_article_total_overlap_match_class += it_overlapping_matches
                binary_article_total_main_category_match_class += it_main_category_matches
                binary_article_total_mismatches_class += it_mismatches

            # raise Exception('HOLD!')
        # automatic mismatch if not all annotators have it and needs to be added to everything
        elif True in if_it_exists_list:
            for c, annotator in enumerate(combo_annotators):
                if combo_annotation_article_dicts[c].get(binary_it):
                    # print(combo_annotation_article_dicts[c][it])  ## ignorance type -> [[annotation_id, ont_lc, [(spans) sorted by starts]]]

                    for i, lone_annotation in enumerate(combo_annotation_article_dicts[c][binary_it]):
                        # print('lone annotation', lone_annotation)
                        ont_lc = lone_annotation[1]
                        span_info = lone_annotation[2]
                        annot_list = [ont_lc, span_info]
                        xml_dict[annotator] += [(binary_it, annot_list)]
                        if binary_it == 'subject_scope':
                            binary_total_annotations_subject += 1
                            binary_article_total_mismatches_subject += 1
                        else:
                            binary_total_annotations_class += 1
                            binary_article_total_mismatches_class += 1

                    # print('xml_dict', xml_dict[annotator])  ## annotator -> (it, annot_list)

                    # raise Exception('HOLD!')

        ##all false - not in any annotations
        else:
            pass

    with open('%sIAA_%s_%s_%s.txt' % (IAA_output_path, article, string_combo_annotators, date.today()),
              'a+') as IAA_output_file:
        IAA_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
        'ignorance type', 'total annotations', 'exact matches', 'overlapping matches', 'main category matches',
        'mismatches', 'percent exact matches',
        'percent matches'))  # all information, total_annotations = denominator, percent matches includes overlaps and main category

        ##ignorance
        if binary_total_annotations_class != 0:
            IAA_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\n' % (
            'ignorance', binary_total_annotations_class, binary_article_total_exact_match_class, binary_article_total_overlap_match_class, binary_article_total_main_category_match_class,
            binary_article_total_mismatches_class, float(binary_article_total_exact_match_class) / float(binary_total_annotations_class),
            float(binary_article_total_exact_match_class + binary_article_total_overlap_match_class + binary_article_total_main_category_match_class) / float(
                binary_total_annotations_class)))
        else:
            IAA_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\n' % (
                'ignorance', binary_total_annotations_class, binary_article_total_exact_match_class,
                binary_article_total_overlap_match_class, binary_article_total_main_category_match_class,
                binary_article_total_mismatches_class,0,0))

        ##subject scope
        # print(binary_total_annotations_subject)
        if binary_total_annotations_subject != 0:
            IAA_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\n' % (
                'subject_scope', binary_total_annotations_subject, binary_article_total_exact_match_subject,
                binary_article_total_overlap_match_subject, binary_article_total_main_category_match_subject,
                binary_article_total_mismatches_subject,
                float(binary_article_total_exact_match_subject) / float(binary_total_annotations_subject),
                float(
                    binary_article_total_exact_match_subject + binary_article_total_overlap_match_subject + binary_article_total_main_category_match_subject) / float(
                    binary_total_annotations_subject)))
        else:
            IAA_output_file.write('%s\t%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\n' % (
                'subject_scope', binary_total_annotations_subject, binary_article_total_exact_match_subject,
                binary_article_total_overlap_match_subject, binary_article_total_main_category_match_subject,
                binary_article_total_mismatches_subject,
                0,0))


    if binary_total_annotations_class != sum([binary_article_total_exact_match_class, binary_article_total_overlap_match_class, binary_article_total_main_category_match_class, binary_article_total_mismatches_class]):
        raise Exception('ERROR WITH BINARY CLASSES TOTALS!')
    elif binary_total_annotations_subject != sum([binary_article_total_exact_match_subject, binary_article_total_overlap_match_subject, binary_article_total_main_category_match_subject, binary_article_total_mismatches_subject]):
        raise Exception('ERROR WITH BINARY SUBJECT TOTALS!')

    # print('binary total annotations class and subject:', binary_total_annotations_class, binary_total_annotations_subject)
    return binary_total_annotations_class, binary_total_annotations_subject, binary_article_total_exact_match_class, binary_article_total_exact_match_subject, binary_article_total_overlap_match_class, binary_article_total_overlap_match_subject, binary_article_total_main_category_match_class, binary_article_total_main_category_match_subject, binary_article_total_mismatches_class, binary_article_total_mismatches_subject, binary_xml_dict


if __name__ == '__main__':

    ##ontology path - TODO: change back!!!!
    all_ontology_inserted_lcs_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/1_First_Full_Annotation_Task_9_13_19/Ontologies/Ontology_Of_Ignorance.owl'

    # all_ontology_inserted_lcs_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/1_First_Full_Annotation_Task_9_13_19/Ontologies/Ontology_Of_Ignorance_5.14.21.xml'

    # all_ontology_inserted_lcs_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/1_First_Full_Annotation_Task_9_13_19/Ontologies/Ontology_Of_Ignorance_3.23.20.xml'


    ##gather all ontology cues
    all_lc_it_dict, all_ignorance_types = all_ontology_cues(all_ontology_inserted_lcs_path)




    ##add the epistemic general type and the subject scope type to the ontology types
    all_ignorance_types += ['Epistemics', 'subject_scope']

    print('all_ignorance_types', all_ignorance_types)
    # raise Exception('HOLD!')

    print('PROGRESS: all linguistic cues gathered!')

    ##Annotations/ folder for all: PMCID.nxml.gz.xml - first pass
    annotation_path_Emily = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/1_First_Full_Annotation_Task_Emily_11.6.19/'
    annotation_path_Elizabeth = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/1_First_Full_Annotation_Task_Elizabeth_11.6.19/'
    annotation_path_Mayla = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/1_First_Full_Annotation_Task_Mayla_11.5.19/'
    annotation_path_preprocess = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Preprocessed_Final/'  ##changed this!!

    ##second batch annotation - training!
    annotation_path_Katie = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/2_Second_Full_Annotation_Task_Katie_1.19.21/'
    annotation_path_Stephanie = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/2_Second_Full_Annotation_Task_Stephanie_1.19.21/'
    annotation_path_gold_standard = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/'
    annotation_path_gold_standard_v2 = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation_v2/'




    ##output for IAA information

    ##GOLD STANDARD ANNOTATION V1
    # IAA_output_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/'
    # pmc_doc_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Articles/'

    ##training output information
    # IAA_output_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/2_Training_Results_1.19.21/IAA/'
    # pmc_doc_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/2_Training_Results_1.19.21/Articles/'

    ##GOLD STANDARD ANNOTATION V2
    IAA_output_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation_v2/IAA/'
    pmc_doc_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation_v2/Articles/'

    ##articles to focus on right now - GOLD STANDARD V1
    # articles = ['PMC1474522', 'PMC3205727']  # current articles we have annotated! #12/20/19 - ontology 12.20.19
    # articles = ['PMC1247630', 'PMC2009866', 'PMC2516588', 'PMC3800883', 'PMC5501061'] #1/28/20 - ontology 12.20.19
    # articles = ['PMC4122855', 'PMC4428817', 'PMC4500436', 'PMC4653409', 'PMC4653418', 'PMC4683322'] #2/11/20 - ontology 1.28.20
    # articles = ['PMC4304064','PMC3513049','PMC3373750','PMC3313761','PMC2874300','PMC1533075','PMC6054603','PMC6033232'] #2/25/20 - ontology 2.11.20

    #run all the articles together to get the added score - NO!!!!
    # articles = ['PMC1474522', 'PMC3205727', 'PMC1247630', 'PMC2009866', 'PMC2516588', 'PMC3800883', 'PMC5501061', 'PMC4122855', 'PMC4428817', 'PMC4500436', 'PMC4653409', 'PMC4653418', 'PMC4683322', 'PMC4304064','PMC3513049','PMC3373750','PMC3313761','PMC2874300','PMC1533075','PMC6054603','PMC6033232']

    # articles = ['PMC2898025', 'PMC3279448', 'PMC3342123', 'PMC4311629'] #3/17/20 - ontology 2.26.20
    # articles = ['PMC1626394', 'PMC2265032', 'PMC3679768', 'PMC3914197', 'PMC4352710', 'PMC5143410', 'PMC5685050'] #4/6/20 - ontology 3.23.20

    # articles = ['PMC6000839', 'PMC6011374', 'PMC6022422', 'PMC6029118', 'PMC6056931'] #5/18/20 - ontology 4.21.20

    # articles = ['PMC2396486', 'PMC3427250', 'PMC4564405', 'PMC6039335'] #6/1/20 - ontology 5.21.20

    # articles = ['PMC2999828', 'PMC3348565', 'PMC4377896', 'PMC5540678']  #6/15/20 - ontology 6.4.20

    # articles = ['PMC2672462', 'PMC3933411', 'PMC4897523', 'PMC5187359'] #6/30/20 - ontology 6.18.20

    # articles = ['PMC2885310', 'PMC3915248', 'PMC4859539', 'PMC5812027'] #7/27/20 - ontology 7.3.20

    # articles = ['PMC2889879', 'PMC3400371', 'PMC4992225', 'PMC5030620']  # 8/10/20 - ontology 7.29.20

    # articles = ['PMC3272870', 'PMC4954778', 'PMC5273824']  # 8/24/20 - ontology 8.13.20

    ##TRAINING ARTICLES
    # articles = ['PMC1247630', 'PMC1474522', 'PMC2009866'] #2/1/21 - ontology 8.25.20
    # articles = ['PMC3800883', 'PMC4428817', 'PMC5501061'] #2/12/20 - ontology 8.25.20
    # articles = ['PMC6000839', 'PMC6022422'] #2/28/21 - ontology 8.25.20




    ##NEW ARTICLES FOR GOLD STANDARD V2
    # articles = ['PMC4715834', 'PMC5546866', 'PMC2727050', 'PMC3075531'] #3/23/21 - ontology 3.6.21
    # articles = ['PMC2722583', 'PMC3424155', 'PMC3470091', 'PMC4275682'] #4/12/21 - ontology 3.29.21
    ## annotating separately with Mayla as adjudicator every week
    # articles = ['PMC4973215', 'PMC5539754'] #5/2/21 - ontology 4.21.21 (run on 5/22/21)
    # articles = ['PMC5658906'] #5/7/21 - ontology 5.2.21 (run on 5/22/21)
    # articles = ['PMC3271033'] #5/14/21 - ontology 5.9.21 (run on 5/22/21)
    # articles = ['PMC5405375'] #5/21/21 - ontology 5.14.21 (run on 5/22/21)
    # articles = ['PMC4380518'] #5/28/21 - ontology 5.22.21
    # articles = ['PMC4488777', 'PMC2722408'] #6/5/21 - ontology 5.28.21
    # articles = ['PMC3828574'] #6/11/21 - ontology 6.5.21
    # articles = ['PMC3659910'] #6/18/21 - ontology 6.11.21
    # articles = ['PMC3169551', 'PMC4327187'] #7/2//21 - ontology 6.18.21
    # articles = ['PMC3710985', 'PMC5439533', 'PMC5524288'] #7/10/21 - ontology 7.2.21
    # articles = ['PMC3789799', 'PMC5240907', 'PMC5340372'] #7/16/21 - ontology 7/10/21
    # articles = ['PMC5226708', 'PMC5732505'] #7/23/21 - ontology 7.16.21 (PMC4869271 Excluded due to difficulty)
    articles = ['PMC4037583','PMC2913107','PMC4231606'] #730/21 - ontology 7.23.21








    # ##ANNOTATORS AND PATH
    # # annotators = ['EMILY', 'ELIZABETH', 'MAYLA', 'PREPROCESS']
    # annotators = ['ELIZABETH', 'MAYLA', 'PREPROCESS']
    # # all_annotation_paths = [annotation_path_Emily, annotation_path_Elizabeth, annotation_path_Mayla,annotation_path_preprocess]
    # all_annotation_paths = [annotation_path_Elizabeth, annotation_path_Mayla, annotation_path_preprocess]


    ##training annotators and paths - will do all combos
    # annotators = ['GOLD_STANDARD', 'KATIE', 'STEPHANIE']
    # all_annotation_paths = [annotation_path_gold_standard, annotation_path_Katie, annotation_path_Stephanie]

    ##GOLD STANDARD V2
    # annotators = ['KATIE', 'STEPHANIE', 'PREPROCESS']
    # all_annotation_paths = [annotation_path_Katie, annotation_path_Stephanie, annotation_path_preprocess]
    # separation = False

    ##separating annotations and calculating the IAA between each annotator and final documents
    separation = True
    annotators = ['ADJUDICATED', 'ANNOTATOR', 'PREPROCESS']
    all_annotation_paths = [annotation_path_gold_standard_v2, {'KATIE': annotation_path_Katie, 'STEPHANIE': annotation_path_Stephanie}, annotation_path_preprocess]

    # annotators_KATIE = ['KATIE', 'KATIE_MAYLA', 'PREPROCESS']
    # all_annotation_paths_KATIE = [annotation_path_Katie, annotation_path_gold_standard_v2, annotation_path_preprocess]
    #
    # annotators_STEPHANIE = ['STEPHANIE', 'STEPHANIE_MAYLA', 'PREPROCESS']
    # all_annotation_paths_STEPHANIE = [annotation_path_Stephanie, annotation_path_gold_standard_v2, annotation_path_preprocess]





    ##all combinations of the annotators
    # all_combos_IAAs = list(itertools.combinations(list(range(4)), 2))
    # all_combos_IAAs = [(0, 1, 2)] + all_combos_IAAs
    all_combos_IAAs = list(itertools.combinations(list(range(len(annotators))), 2))
    all_combos_IAAs = [(0, 1, 2)] + all_combos_IAAs
    print(all_combos_IAAs)



    ##full totals!

    ##OUTPUT PER ARTICLE IAA
    with open('%s%s_%s.txt' % (IAA_output_path, 'full_summary_IAA', date.today()), 'w+') as full_summary_output, open('%s%s_%s.txt' % (IAA_output_path, 'F1_full_summary_IAA', date.today()), 'w+') as F1_full_summary_output:

        full_summary_output.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
            'CURRENT ARTICLE', 'ALL ANNOTATIONS CLASS', 'TOTAL EXACT MATCHES CLASS', 'TOTAL OVERLAP MATCHES CLASS', 'TOTAL MAIN CATEGORY MATCHES CLASS',
            'PERCENT EXACT MATCH CLASS', 'PERCENT MATCHES CLASS',
            'ALL ANNOTATIONS SCOPE', 'TOTAL EXACT MATCHES SCOPE', 'TOTAL OVERLAP MATCHES SCOPE', 'TOTAL MAIN CATEGORY MATCHES SCOPE',
            'PERCENT EXACT MATCH SCOPE', 'PERCENT MATCHES SCOPE', 'TOTAL IGNORANCE ANNOTATIONS', 'TOTAL IGNORANCE EXACT MATCH', 'TOTAL IGNORANCE OVERLAP MATCHES', 'TOTAL IGNORANCE MAIN CATEGORY MATCHES', 'PERCENT IGNORANCE EXACT MATCHES', 'PERCENT IGNORANCE MATCHES'))

        F1_full_summary_output.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' %('CURRENT ARTICLE', 'TP CLASS', 'ANNOTATOR MISMATCHES CLASS', 'F1 CLASS (IAA)', 'TP SUBJECT', 'ANNOTATOR MISMATCHES SUBJECT', 'F1 SUBJECT (IAA)', 'FUZZY TP CLASS', 'FUZZY ANNOTATOR MISMATCHES CLASS', 'FUZZY F1 CLASS (IAA)', 'FUZZY TP SUBJECT', 'FUZZY ANNOTATOR MISMATCHES SUBJECT', 'FUZZY F1 SUBJECT (IAA)'))




        ##FOR EACH COMBO OF ANNOTATORS (INCLUDING PREPROCESSING)
        # main_annotator = None
        sole_annotator = None
        article_annotation_dict = {} #article -> sole annotator if applicaple

        for c in all_combos_IAAs:
            # print(c)

            # ##most lenient score over all articles
            span_overlap_score_dict = {}  # most lenient score that includes same span overlap: (pmcid, span) -> [list of annotators] if overlap - to be able to capture the number of annotations there



            full_summary_output.write('\n\n')
            F1_full_summary_output.write('\n\n')


            full_summary_output_dict = {} #article -> [annotators, string of output]

            ##final summary stats for all articles - closer matching on ignorance type
            full_annotations_class = 0
            full_exact_match_class = 0
            full_overlap_match_class = 0
            full_main_category_match_class = 0
            full_annotations_subject = 0
            full_exact_match_subject = 0
            full_overlap_match_subject = 0
            full_main_category_match_subject = 0

            full_annotations_class_span = 0
            full_exact_match_class_span = 0
            full_overlap_match_class_span = 0
            full_main_category_match_class_span = 0
            full_annotations_subject_span = 0
            full_exact_match_subject_span = 0
            full_overlap_match_subject_span = 0
            full_main_category_match_subject_span = 0

            # full_span_exact_match_count = 0
            # full_span_not_match_count = 0
            # full_span_overlap_count = 0
            # full_span_no_overlap_count = 0
            # full_max_annotations_count = 0

            if len(c) == 2:
                ##F1 final summary info
                full_tp_class = 0
                full_tp_subject = 0
                full_two_annotator_counts = {} #dict from annotators -> class, subject mismatches
                for t in c:
                    full_two_annotator_counts[annotators[t]] = [0,0]


                full_fuzzy_tp_class = 0
                full_fuzzy_tp_subject = 0
                full_fuzzy_two_annotator_counts = {} #dict from annotators -> class, subject mismatches
                for t in c:
                    full_fuzzy_two_annotator_counts[annotators[t]] = [0,0]


            combo_annotators = []
            for i in c:
                combo_annotators += [annotators[i]]

            print('CURRENT ANNOTATORS:', combo_annotators)

            full_summary_output.write('%s\t' %'ANNOTATORS:')
            if len(c) == 2:
                if 'PREPROCESS' in combo_annotators:
                    F1_full_summary_output.write('%s\t' %('ANNOTATORS (ONLY CLASS):'))
                else:
                    F1_full_summary_output.write('%s\t' %('ANNOTATORS:'))
            for i in c:
                # print(i)
                full_summary_output.write('%s, ' % annotators[i])
                if len(c) == 2:
                    F1_full_summary_output.write('%s, ' %annotators[i])

            full_summary_output.write('\n')
            if len(c) == 2:
                F1_full_summary_output.write('\n')

            # max_annotations_full_dict = {} #article -> [max_annotation_class, max_annotation_class]


            for article in articles:
                print('CURRENT ARTICLE:', article)
                full_summary_output_dict[article] = '' #article -> [string of output]

                combo_annotators = []
                combo_annotation_path = []
                combo_annotation_article_dicts = []

                for i in range(len(c)):
                    combo_annotators += [annotators[c[i]]]
                    combo_annotation_path += [all_annotation_paths[c[i]]]

                    # full_summary_output.write('%s %s: %s\n' % ('ANNOTATOR', i, annotators[c[i]]))
                    # full_summary_output_dict[article][0] += '%s, ' %annotators[c[i]]
                    # print('annotators', annotators[c[i]])

                    # print('MAIN ANNOTATOR:', main_annotator)
                    if article_annotation_dict.get(article):
                        sole_annotator = article_annotation_dict[article]
                    else:
                        pass

                    annotation_article_dicts, span_overlap_score_dict, sole_annotator = collect_annotations(all_annotation_paths[c[i]], article, all_lc_it_dict, span_overlap_score_dict, sole_annotator)
                    ##setting the main annotator for the situations where we have different annotators becuase of separation
                    if sole_annotator:
                        if article_annotation_dict.get(article):
                            if article_annotation_dict[article] != sole_annotator:
                                raise Exception('ERROR: Issue with sole_annotator assignment!')
                            else:
                                pass
                        else:
                            article_annotation_dict[article] = sole_annotator
                        print('SOLE_ANNOTATOR:', sole_annotator)
                    else:
                        pass



                    combo_annotation_article_dicts += [annotation_article_dicts]
                    # print('collect annotations', combo_annotation_article_dicts)

                # # if article == 'PMC1474522' or article == 'PMC3205727':
                # annotation_article_dict1 = collect_annotations(annotation_path1, article, all_lc_it_dict)
                # annotation_article_dict2 = collect_annotations(annotation_path2, article, all_lc_it_dict)

                ##RUN IAA:
                total_annotations_class, total_annotations_subject, article_total_exact_match_class, article_total_exact_match_subject, article_total_overlap_match_class, article_total_overlap_match_subject, article_total_main_category_match_class, article_total_main_category_match_subject, article_total_mismatches_class, article_total_mismatches_subject, xml_dict = calculate_IAA(all_ignorance_types, all_lc_it_dict, combo_annotators, combo_annotation_article_dicts, article, IAA_output_path)

                ##RUN MORE LENIENT IAA: add in the final scores to print out with totals for summaary!
                binary_total_annotations_class, binary_total_annotations_subject, binary_article_total_exact_match_class, binary_article_total_exact_match_subject, binary_article_total_overlap_match_class, binary_article_total_overlap_match_subject, binary_article_total_main_category_match_class, binary_article_total_main_category_match_subject, binary_article_total_mismatches_class, binary_article_total_mismatches_subject, binary_xml_dict = calculate_span_overlap_IAA(all_ignorance_types, all_lc_it_dict, combo_annotators, combo_annotation_article_dicts, article, IAA_output_path)

                ##check that the subject_scope counts are the same, the classes can be different given different overlaps: total_annotations_class != binary_total_annotations_class
                if total_annotations_subject != binary_total_annotations_subject:
                    print('ARTICLE TOTALS:', total_annotations_class, binary_total_annotations_class, total_annotations_subject, binary_total_annotations_subject)
                    raise Exception('ERROR WITH TOTALS FROM CALCULATE IAA PER ARTICLE!')


                ##TODO: use xml dict to create F1 IAA - output this!!!
                ##calculate the F1 for IAA!!!! (both fuzzy and full)
                if len(c) == 2:
                    fuzzy_F1_class, fuzzy_F1_subject, fuzzy_two_annotator_counts, fuzzy_tp_class, fuzzy_tp_subject, F1_class, F1_subject, two_annotator_counts, tp_class, tp_subject = calculate_F1_IAA(article, xml_dict, c, annotators, combo_annotation_article_dicts)


                    ##output per article:
                    annotator_mismatch_class = [two_annotator_counts[t][0] for t in combo_annotators]
                    annotator_mismatch_subject = [two_annotator_counts[t][1] for t in combo_annotators]
                    fuzzy_annotator_mismatch_class = [fuzzy_two_annotator_counts[t][0] for t in combo_annotators]
                    fuzzy_annotator_mismatch_subject = [fuzzy_two_annotator_counts[t][1] for t in combo_annotators]

                    if 'PREPROCESS' in combo_annotators:
                        if article_annotation_dict:
                            F1_full_summary_output.write('%s (%s)\t%s\t%s\t%.2f\t%s\t%s\t%s\t%s\t%s\t%.2f\t%s\t%s\t%s\n' % (
                                article, article_annotation_dict[article], tp_class, annotator_mismatch_class, F1_class, 'NA',
                                annotator_mismatch_subject, 'NA', fuzzy_tp_class,
                                fuzzy_annotator_mismatch_class, fuzzy_F1_class, 'NA',
                                fuzzy_annotator_mismatch_subject, 'NA'))
                        else:
                            F1_full_summary_output.write('%s\t%s\t%s\t%.2f\t%s\t%s\t%s\t%s\t%s\t%.2f\t%s\t%s\t%s\n' % (
                                article, tp_class, annotator_mismatch_class, F1_class, 'NA',
                                annotator_mismatch_subject, 'NA', fuzzy_tp_class,
                                fuzzy_annotator_mismatch_class, fuzzy_F1_class, 'NA',
                                fuzzy_annotator_mismatch_subject, 'NA'))
                    else:
                        if article_annotation_dict:
                            F1_full_summary_output.write(
                                '%s (%s)\t%s\t%s\t%.2f\t%s\t%s\t%.2f\t%s\t%s\t%.2f\t%s\t%s\t%.2f\n' % (
                                article, article_annotation_dict[article], tp_class, annotator_mismatch_class, F1_class, tp_subject,
                                annotator_mismatch_subject, F1_subject, fuzzy_tp_class,
                                fuzzy_annotator_mismatch_class, fuzzy_F1_class, fuzzy_tp_subject,
                                fuzzy_annotator_mismatch_subject, fuzzy_F1_subject))
                        else:
                            F1_full_summary_output.write('%s\t%s\t%s\t%.2f\t%s\t%s\t%.2f\t%s\t%s\t%.2f\t%s\t%s\t%.2f\n' % (
                                article, tp_class, annotator_mismatch_class, F1_class, tp_subject,
                                annotator_mismatch_subject, F1_subject, fuzzy_tp_class,
                                fuzzy_annotator_mismatch_class, fuzzy_F1_class, fuzzy_tp_subject,
                                fuzzy_annotator_mismatch_subject, fuzzy_F1_subject))


                    ##full summary gathering
                    full_tp_class += tp_class
                    # if 'PREPROCESS' in combo_annotators:
                    #     full_tp_subject = 'NA'
                    # else:
                    full_tp_subject += tp_subject

                    for t in c:
                        # dict from annotators -> class, subject mismatches
                        full_two_annotator_counts[annotators[t]][0] += two_annotator_counts[annotators[t]][0]
                        full_two_annotator_counts[annotators[t]][1] += two_annotator_counts[annotators[t]][1]

                    full_fuzzy_tp_class += fuzzy_tp_class
                    # if 'PREPROCESS' in combo_annotators:
                    #     full_fuzzy_tp_subject = 'NA'
                    # else:
                    full_fuzzy_tp_subject += fuzzy_tp_subject

                    for t in c:
                        # dict from annotators -> class, subject mismatches
                        full_fuzzy_two_annotator_counts[annotators[t]][0] += fuzzy_two_annotator_counts[annotators[t]][0]
                        full_fuzzy_two_annotator_counts[annotators[t]][1] += fuzzy_two_annotator_counts[annotators[t]][1]


                    # raise Exception('HOLD!')


                # max_annotations_full_dict[article] = [total_annotations_class, total_annotations_subject]

                ##Use the xml dict to xml_creation if we are not using the preprocess
                if 'PREPROCESS' not in combo_annotators:
                    xml_creation(article, pmc_doc_path, combo_annotators, xml_dict, IAA_output_path)  # xml_dict



                ##output all the IAA information

                # print(article_total_exact_match_span, article_total_overlap_match_span, max_annotations_span,max_annotations_class)

                if 'PREPROCESS' in combo_annotators:
                    if total_annotations_class != 0:
                        full_summary_output.write('%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\t%s\t%s\t%s\t%s\t%s\t' % (
                            article, total_annotations_class, article_total_exact_match_class,
                            article_total_overlap_match_class, article_total_main_category_match_class,
                            float(article_total_exact_match_class) / float(total_annotations_class),
                            float(article_total_exact_match_class + article_total_overlap_match_class + article_total_main_category_match_class) / float(
                                total_annotations_class), 'NA', 'NA', 'NA', 'NA', 'NA'))
                        # full_summary_output_dict[article] += '%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\n' % (
                        #     article, total_annotations_class, article_total_exact_match_class,
                        #     article_total_overlap_match_class, article_total_main_category_match_class,
                        #     float(article_total_exact_match_class) / float(total_annotations_class),
                        #     float(article_total_exact_match_class + article_total_overlap_match_class + article_total_main_category_match_class) / float(
                        #         total_annotations_class))
                    else:
                        full_summary_output.write('%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\t%s\t%s\t%s\t%s\t%s\t' % (
                            article, total_annotations_class, article_total_exact_match_class,
                            article_total_overlap_match_class,article_total_main_category_match_class,
                            0, 0, 'NA', 'NA', 'NA', 'NA', 'NA'))
                        # full_summary_output_dict[article] += '%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\n' % (
                        #     article, total_annotations_class, article_total_exact_match_class,
                        #     article_total_overlap_match_class, article_total_main_category_match_class,
                        #     0, 0)
                    if binary_total_annotations_class != 0:
                        full_summary_output.write('%s\t%s\t%s\t%s\t%.2f\t%.2f\n' %(binary_total_annotations_class, binary_article_total_exact_match_class, binary_article_total_overlap_match_class, binary_article_total_main_category_match_class, float(binary_article_total_exact_match_class)/float(binary_total_annotations_class), float(binary_article_total_exact_match_class+ binary_article_total_overlap_match_class + binary_article_total_main_category_match_class)/float(binary_total_annotations_class)))
                    else:
                        full_summary_output.write('%s\t%s\t%s\t%s\t%.2f\t%.2f\n' % (
                        binary_total_annotations_class, binary_article_total_exact_match_class,
                        binary_article_total_overlap_match_class, binary_article_total_main_category_match_class,
                        0, 0))




                ##not preprocess
                else:
                    if total_annotations_class != 0:

                        full_summary_output.write('%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\t' % (
                            article, total_annotations_class, article_total_exact_match_class,
                            article_total_overlap_match_class, article_total_main_category_match_class,
                            float(article_total_exact_match_class) / float(total_annotations_class),
                            float(article_total_exact_match_class + article_total_overlap_match_class + article_total_main_category_match_class) / float(
                                total_annotations_class)))

                        # full_summary_output_dict[article] += '%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\t' % (
                        #     article, total_annotations_class, article_total_exact_match_class,
                        #     article_total_overlap_match_class, article_total_main_category_match_class,
                        #     float(article_total_exact_match_class) / float(total_annotations_class),
                        #     float(article_total_exact_match_class + article_total_overlap_match_class + article_total_main_category_match_class) / float(
                        #         total_annotations_class))
                    else:
                        full_summary_output.write('%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\t' % (
                            article, total_annotations_class, article_total_exact_match_class,
                            article_total_overlap_match_class, article_total_main_category_match_class,
                            0, 0))
                        # full_summary_output_dict[article] += '%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\t' % (
                        #     article, total_annotations_class, article_total_exact_match_class,
                        #     article_total_overlap_match_class, article_total_main_category_match_class,
                        #     0, 0)

                    if total_annotations_subject != 0:

                        full_summary_output.write(
                            '%s\t%s\t%s\t%s\t%.2f\t%.2f\t' % (total_annotations_subject, article_total_exact_match_subject,article_total_overlap_match_subject, article_total_main_category_match_subject,float(article_total_exact_match_subject) / float(total_annotations_subject), float(article_total_exact_match_subject + article_total_overlap_match_subject) / float(total_annotations_subject)))

                        # full_summary_output_dict[article] += '%s\t%s\t%s\t%s\t%.2f\t%.2f\t' % (total_annotations_subject, article_total_exact_match_subject,article_total_overlap_match_subject, article_total_main_category_match_subject,float(article_total_exact_match_subject) / float(total_annotations_subject), float(article_total_exact_match_subject + article_total_overlap_match_subject) / float(total_annotations_subject))

                    else:
                        full_summary_output.write(
                            '%s\t%s\t%s\t%s\t%.2f\t%.2f\t' % (total_annotations_subject, article_total_exact_match_subject, article_total_overlap_match_subject, article_total_main_category_match_subject, 0, 0))

                        # full_summary_output_dict[article] += '%s\t%s\t%s\t%s\t%.2f\t%.2f\t' % (total_annotations_subject, article_total_exact_match_subject, article_total_overlap_match_subject, article_total_main_category_match_subject, 0, 0)

                    #'TOTAL IGNORANCE ANNOTATIONS', 'TOTAL IGNORANCE EXACT MATCH', 'TOTAL IGNORANCE OVERLAP MATCHES', 'TOTAL IGNORANCE MAIN CATEGORY MATCHES', 'PERCENT IGNORANCE EXACT MATCHES', 'PERCENT IGNORANCE MATCHES'
                    if binary_total_annotations_class != 0:
                        full_summary_output.write('%s\t%s\t%s\t%s\t%.2f\t%.2f\n' %(binary_total_annotations_class, binary_article_total_exact_match_class, binary_article_total_overlap_match_class, binary_article_total_main_category_match_class, float(binary_article_total_exact_match_class)/float(binary_total_annotations_class), float(binary_article_total_exact_match_class+ binary_article_total_overlap_match_class + binary_article_total_main_category_match_class)/float(binary_total_annotations_class)))
                    else:
                        full_summary_output.write('%s\t%s\t%s\t%s\t%.2f\t%.2f\n' % (
                        binary_total_annotations_class, binary_article_total_exact_match_class,
                        binary_article_total_overlap_match_class, binary_article_total_main_category_match_class,
                        0, 0))



                ##all the totals for percents:
                full_annotations_class += total_annotations_class
                full_exact_match_class += article_total_exact_match_class
                full_overlap_match_class += article_total_overlap_match_class
                full_main_category_match_class += article_total_main_category_match_class
                full_annotations_subject += total_annotations_subject
                full_exact_match_subject += article_total_exact_match_subject
                full_overlap_match_subject += article_total_overlap_match_subject
                full_main_category_match_subject += article_total_main_category_match_subject

                ##totals just for span information:
                full_annotations_class_span += binary_total_annotations_class
                full_exact_match_class_span += binary_article_total_exact_match_class
                full_overlap_match_class_span += binary_article_total_overlap_match_class
                full_main_category_match_class_span += binary_article_total_main_category_match_class
                full_annotations_subject_span += binary_total_annotations_subject
                full_exact_match_subject_span += binary_article_total_exact_match_subject
                full_overlap_match_subject_span += binary_article_total_overlap_match_subject
                full_main_category_match_subject_span += binary_article_total_main_category_match_subject


            # # exact match dict from: article -> (exact match count, not match count, overlap count, no overlap count)
            # span_match_count_dict = calculate_span_overlap_IAA(span_overlap_score_dict, combo_annotators, articles)
            # for article in articles:
            #     span_exact_match_count, span_not_match_count, span_overlap_count, span_no_overlap_count = span_match_count_dict[article]
            #
            #     #max_annotations_full_dict[article] = [max_annotations_class, max_annotations_span]
            #     max_annotations_count = sum(max_annotations_full_dict[article])
            #
            #     full_span_exact_match_count += span_exact_match_count
            #     full_span_not_match_count += span_not_match_count
            #     full_span_overlap_count += span_overlap_count
            #     full_span_no_overlap_count += span_no_overlap_count
            #     full_max_annotations_count += max_annotations_count
            #
            #     span_total_annotations = span_exact_match_count + span_not_match_count
            #     #'TOTAL MATCHES ON SPANS', 'TOTAL OVERLAPS ON SPAN', 'PERCENT EXACT MATCHES ON SPAN', 'PERCENT MATCHES ON SPANS')
            #     # full_summary_output.write('%s\t%s\t%.2f\t%.2f\t' %(span_exact_match_count, span_overlap_count, float(span_exact_match_count)/float(span_total_annotations), float(span_exact_match_count+span_overlap_count)/float(span_total_annotations)))
            #     # print(article, max_annotations_count)
            #
            #     if span_total_annotations < (2*span_exact_match_count) + span_overlap_count:
            #         print(max_annotations_count)
            #         print(span_exact_match_count, span_overlap_count,span_exact_match_count + span_overlap_count)
            #         print(span_total_annotations)
            #         # raise Exception('ERROR WITH DENOMINATOR FOR SPAN COUNT!')
            #
            #
            #     if max_annotations_count != 0:
            #         # full_summary_output_dict[article] += '%s\t%s\t%.2f\t%.2f\n' %(span_exact_match_count, span_overlap_count, float(span_exact_match_count)/float(max_annotations_count), float(span_exact_match_count+span_overlap_count)/float(max_annotations_count))
            #         full_summary_output_dict[article] += '%s\t%s\t%s\t%s\t%.2f\t%.2f\n' % (
            #         span_total_annotations, span_exact_match_count, span_overlap_count, span_no_overlap_count,
            #         float(span_exact_match_count) / float(max_annotations_count),
            #         float(span_exact_match_count + span_overlap_count) / float(max_annotations_count))
            #     else:
            #         full_summary_output_dict[article] += '%s\t%s\t%s\t%s\t%.2f\t%.2f\n' % (span_total_annotations, span_exact_match_count, span_overlap_count, span_no_overlap_count, 0, 0)
            #
            #     # full_summary_output.write('%s\t%s\n' %('ANNOTATOR', full_summary_output_dict[article][0][:-2]))
            #     full_summary_output.write('%s' %full_summary_output_dict[article])

            # full_summary_output.write('\n')

            ##TOTALS - TODO: add totals!

            # full_summary_output.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
            #     'FULL', 'ALL ANNOTATIONS CLASS', 'TOTAL EXACT MATCHES CLASS', 'TOTAL OVERLAP MATCHES CLASS',
            #     'PERCENT EXACT MATCH CLASS', 'PERCENT MATCHES CLASS',
            #     'ALL ANNOTATIONS SPAN', 'TOTAL EXACT MATCHES SPAN', 'TOTAL OVERLAP MATCHES SPAN',
            #     'PERCENT EXACT MATCH SPAN', 'PERCENT MATCHES SPAN', 'TOTAL MATCHES ON SPANS', 'TOTAL OVERLAPS ON SPAN', 'PERCENT EXACT MATCHES ON SPAN', 'PERCENT MATCHES ON SPANS'))

            # full_span_total_annotations = full_span_exact_match_count + full_span_not_match_count
            #
            # if full_max_annotations_count < full_span_exact_match_count + full_span_overlap_count:
            #     print(full_max_annotations_count)
            #     print(full_span_exact_match_count + full_span_overlap_count)
            #     # raise Exception('ERROR WITH FULL DENOMINATOR FOR TOTAL SPAN COUNT!')


            ##check to make sure the subject spans are the same, the classes can be different due to more overlaps: full_annotations_class != full_annotations_class_span
            if full_annotations_subject != full_annotations_subject_span:
                print('ALL TOTALS ERROR', full_annotations_class, full_annotations_class_span, full_annotations_subject, full_annotations_subject_span)
                raise Exception('ERROR WITH DENOMINATOR COUNTING FOR CLASS OR SPAN!')

            if 'PREPROCESS' in combo_annotators:
                if full_annotations_class != 0:
                    full_summary_output.write('%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\t' % (
                        'TOTAL', full_annotations_class, full_exact_match_class, full_overlap_match_class, full_main_category_match_class,
                        float(full_exact_match_class) / float(full_annotations_class),
                        float(full_exact_match_class + full_overlap_match_class + full_main_category_match_class) / float(full_annotations_class)))
                else:
                    full_summary_output.write('%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\t' % (
                        'TOTAL', full_annotations_class, full_exact_match_class, full_overlap_match_class, full_main_category_match_class,
                        0, 0))

                if full_annotations_class_span != 0:
                    full_summary_output.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\n' % (
                        'NA', 'NA', 'NA', 'NA', 'NA',full_annotations_class_span, full_exact_match_class_span, full_overlap_match_class_span, full_main_category_match_class_span, float(full_exact_match_class_span)/float(full_annotations_class_span), float(full_exact_match_class_span+full_overlap_match_class_span+full_main_category_match_class_span)/float(full_annotations_class_span)))
                else:
                    full_summary_output.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\n' % (
                        'NA', 'NA', 'NA', 'NA', 'NA', full_annotations_class_span, full_exact_match_class_span, full_overlap_match_class_span, full_main_category_match_class_span, 0,0))

            ##all annotators not preprocessed
            else:
                if full_annotations_class != 0:
                    full_summary_output.write('%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\t' % (
                        'TOTAL', full_annotations_class, full_exact_match_class, full_overlap_match_class, full_main_category_match_class,
                        float(full_exact_match_class) / float(full_annotations_class),
                        float(full_exact_match_class + full_overlap_match_class + full_main_category_match_class) / float(full_annotations_class),
                    ))
                else:
                    full_summary_output.write('%s\t%s\t%s\t%s\t%s\t%.2f\t%.2f\t' % (
                        'TOTAL', full_annotations_class, full_exact_match_class, full_overlap_match_class, full_main_category_match_class,
                        0, 0))

                if full_annotations_subject != 0:
                    full_summary_output.write('%s\t%s\t%s\t%s\t%.2f\t%.2f\t' % (
                    full_annotations_subject, full_exact_match_subject, full_overlap_match_subject, full_main_category_match_subject,
                    float(full_exact_match_subject) / float(full_annotations_subject),
                    float(full_exact_match_subject + full_overlap_match_subject + full_main_category_match_subject) / float(full_annotations_subject)))
                else:
                    full_summary_output.write('%s\t%s\t%s\t%s\t%.2f\t%.2f\t' % (
                        full_annotations_subject, full_exact_match_subject, full_overlap_match_subject, full_main_category_match_subject,0, 0))


                if full_annotations_class_span != 0:
                    full_summary_output.write('%s\t%s\t%s\t%s\t%.2f\t%.2f' % (
                    full_annotations_class_span, full_exact_match_class_span, full_overlap_match_class_span, full_main_category_match_class_span, float(full_exact_match_class_span)/float(full_annotations_class_span), float(full_exact_match_class_span+full_overlap_match_class_span+full_main_category_match_class_span)/float(full_annotations_class_span)))
                else:
                    full_summary_output.write('%s\t%s\t%s\t%s\t%.2f\t%.2f' % (full_annotations_class_span, full_exact_match_class_span, full_overlap_match_class_span, full_main_category_match_class_span, 0, 0))




            ##F1 full summary information - TODO:
            ##output total:
            if len(c) == 2:
                full_annotator_mismatch_class = [full_two_annotator_counts[t][0] for t in combo_annotators]
                full_annotator_mismatch_subject = [full_two_annotator_counts[t][1] for t in combo_annotators]
                full_fuzzy_annotator_mismatch_class = [full_fuzzy_two_annotator_counts[t][0] for t in combo_annotators]
                full_fuzzy_annotator_mismatch_subject = [full_fuzzy_two_annotator_counts[t][1] for t in combo_annotators]

                ##calculate total full F1
                total_PR_class = []
                total_PR_subject = []
                for t in combo_annotators:
                    # print(two_annotator_counts[t])
                    PR_class = float(full_tp_class) / float(full_tp_class + full_two_annotator_counts[t][0])
                    if 'PREPROCESS' in combo_annotators:
                        PR_subject = 0
                    else:
                        PR_subject = float(full_tp_subject) / float(full_tp_subject + full_two_annotator_counts[t][1])

                    total_PR_class += [PR_class]
                    total_PR_subject += [PR_subject]

                # print(total_PR_class)
                # print(total_PR_subject)
                full_F1_class = (2 * float(total_PR_class[0]) * float(total_PR_class[1])) / float(
                    total_PR_class[0] + total_PR_class[1])
                if 'PREPROCESS' in combo_annotators:
                    full_F1_subject = 'NA'
                else:
                    full_F1_subject = (2 * float(total_PR_subject[0]) * float(total_PR_subject[1])) / float(
                        total_PR_subject[0] + total_PR_subject[1])

                ##calculate total fuzzy F1
                fuzzy_total_PR_class = []
                fuzzy_total_PR_subject = []
                for t in combo_annotators:
                    # print(full_fuzzy_two_annotator_counts[t])
                    full_fuzzy_PR_class = float(full_fuzzy_tp_class) / float(full_fuzzy_tp_class + full_fuzzy_two_annotator_counts[t][0])
                    if 'PREPROCESS' in combo_annotators:
                        full_fuzzy_PR_subject = 0
                    else:
                        full_fuzzy_PR_subject = float(full_fuzzy_tp_subject) / float(full_fuzzy_tp_subject + full_fuzzy_two_annotator_counts[t][1])

                    fuzzy_total_PR_class += [full_fuzzy_PR_class]
                    fuzzy_total_PR_subject += [full_fuzzy_PR_subject]

                # print(fuzzy_total_PR_class)
                # print(fuzzy_total_PR_subject)
                full_fuzzy_F1_class = (2 * float(fuzzy_total_PR_class[0]) * float(fuzzy_total_PR_class[1])) / float(fuzzy_total_PR_class[0] + fuzzy_total_PR_class[1])

                if 'PREPROCESS' in combo_annotators:
                    full_fuzzy_F1_subject = 'NA'
                else:
                    full_fuzzy_F1_subject = (2 * float(fuzzy_total_PR_subject[0]) * float(fuzzy_total_PR_subject[1])) / float(fuzzy_total_PR_subject[0] + fuzzy_total_PR_subject[1])


                if 'PREPROCESS' in combo_annotators:
                    F1_full_summary_output.write('%s\t%s\t%s\t%.2f\t%s\t%s\t%s\t%s\t%s\t%.2f\t%s\t%s\t%s\n' % (
                        'TOTAL', full_tp_class, full_annotator_mismatch_class, full_F1_class, 'NA',
                        full_annotator_mismatch_subject, 'NA', full_fuzzy_tp_class,
                        full_fuzzy_annotator_mismatch_class, full_fuzzy_F1_class, 'NA',
                        full_fuzzy_annotator_mismatch_subject, 'NA'))
                else:
                    F1_full_summary_output.write('%s\t%s\t%s\t%.2f\t%s\t%s\t%.2f\t%s\t%s\t%.2f\t%s\t%s\t%.2f\n' % (
                    'TOTAL', full_tp_class, full_annotator_mismatch_class, full_F1_class, full_tp_subject,
                    full_annotator_mismatch_subject, full_F1_subject, full_fuzzy_tp_class,
                    full_fuzzy_annotator_mismatch_class, full_fuzzy_F1_class, full_fuzzy_tp_subject,
                    full_fuzzy_annotator_mismatch_subject, full_fuzzy_F1_subject))



            ##NEW LINE FOR THE NEXT COMBO OF ANNOTATORS
            full_summary_output.write('\n\n\n')
            if len(c) == 2:
                F1_full_summary_output.write('\n\n\n')
