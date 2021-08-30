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
from xml.dom import minidom
import multiprocessing as mp
import functools
import resource, sys
from emoji import UNICODE_EMOJI
import demoji
# demoji.download_codes()
from datetime import date
from lxml import etree
from nltk.tokenize.punkt import PunktSentenceTokenizer



##TODO: codecs for wrapping to help with parallelization



sys.setrecursionlimit(60000) #reset max recursion to be over what I need... no files are greater than 4000 cues




def is_emoji(s):
	count = 0
	for emoji in UNICODE_EMOJI:
		count += s.count(emoji)
		if count > 1:
			return False
	return count

#old one!
def all_linguistic_cues(all_ontology_inserted_lcs_path, new_lcs_paths_list):
	"""
	Gathers all the ontology inserted lexical cues for use in automatic regex annotation (preprocessing)
	:param all_ontology_inserted_lcs_path: the file path to all of the ontology inserted lexical cues
	:return: all_lcs: a list of all the ontology terms to be used in the next phases
	"""


	# all_lcs = [] #lexical cue, synonym (regex), ignorance type
	all_lcs_dict = {} #lexical cue -> [synonyms (regex), ignorance_type]
	all_its = set([])

	##added things 12/19/19 based on annotation meeting
		##cues to discard because redundant or changed
	redundant_lcs = ['have_been', 'has_been', 'few_studies', 'future_research', 'consistently'] #both the discontinuous (...) and the continuous exist(_) -

	added_lcs = [] ## new lcs to add in - future...research -
	for new_lcs_path in new_lcs_paths_list:
		with open(new_lcs_path, 'r') as new_lcs_file:
			next(new_lcs_file)
			for line in new_lcs_file:
				# added_lcs += [(line.split('\t')[0], line.split('\t')[1], line.split('\t')[2])]
				# [lc, regex, it] = line.replace('\n','').split('\t')
				lc = line.split('\t')[0]
				regex = line.split('\t')[1]
				it = line.split('\t')[2].replace('\n','')
				all_its.add(it)
				if all_lcs_dict.get(lc) and all_lcs_dict[lc] != [regex,it]:
					print(new_lcs_path)
					print(lc)
					print(regex)
					print(it)
					raise Exception('ERROR: CONFLICTING INFORMATION IN FILES!') #new lexical cues to different categories inserted - do it in order of appearence
					pass
				else:
					all_lcs_dict[lc] = [regex, it]

	##all_ontology_inserted_lcs - filtering for the redundant ones
	with open(all_ontology_inserted_lcs_path, 'r+') as all_ontology_inserted_lcs_file:
		next(all_ontology_inserted_lcs_file)
		for line in all_ontology_inserted_lcs_file:
			(lc, regex, it) = line.replace('\n', '').split('\t')
			##get rid of the redundent lcs
			if lc in redundant_lcs:
				pass
			else:
				# all_lcs += [(line.split('\t')[0], line.split('\t')[1], line.split('\t')[2].replace('\n',''))]
				if all_lcs_dict.get(lc):
					#redundancies
					pass
				else:
					all_lcs_dict[lc] = [regex, it]

				all_its.add(it)



	##combine all lcs:
	# final_lcs = all_lcs + added_lcs

	# print(all_lcs[:10])
	# return final_lcs, all_its
	return all_lcs_dict, all_its


#all ontology cues and ignorance types
def updated_ontology_cues(ontology_file_path, broad_categories):
	##Gather all lexical cues from the ontology to create
	# all_lcs_dict = {} #lexical cue -> [synonyms (regex), ignorance_type]
	# all_its = set([])

	all_lcs_dict = {}  # lexical cue -> [synonyms (regex), ignorance_type]
	all_its = set([])


	parser = etree.XMLParser(ns_clean=True, attribute_defaults=True, dtd_validation=True, load_dtd=True,
							 remove_blank_text=True, recover=True)
	ontology_of_ignorance_tree = etree.parse(ontology_file_path)
	doc_info = ontology_of_ignorance_tree.docinfo

	root = ontology_of_ignorance_tree.getroot()
	print('ROOT', root.tag)

	for subclassof in root.iter('{http://www.w3.org/2002/07/owl#}SubClassOf'):
		no_issues = True
		for i, child in enumerate(subclassof):
			if i == 0:
				lc = child.attrib['IRI'].replace('#', '').replace('0_','')
			elif i == 1:
				it = child.attrib['IRI'].replace('#', '').upper()
				if it in broad_categories:
					no_issues = False
		if no_issues:
			##disjoint cues
			if '...' in lc:
				all_lcs_dict[lc] = [None, it]
			#regular cues that have the same regex/synonym as the lc
			else:
				all_lcs_dict[lc] = [lc, it] #the regex is the same if it is not disjoint

			all_its.add(it)
		else:
			continue


	##now add the regex to the disjoint cues!

	for AnnotationAssertion in root.iter('{http://www.w3.org/2002/07/owl#}AnnotationAssertion'):
		bad_child = False
		for child in AnnotationAssertion:
			# print(child.tag, child.text)

			if child.tag.endswith('AnnotationProperty'):
				if child.attrib['IRI'] != '#hasExactSynonym':
					# print('got here fine!')
					bad_child = True
					break
				else:
					bad_child = False

			elif child.tag.endswith('IRI'):
				lc1 = child.text.replace('#','')
				#the higher epistemic categories also have synonyms are causing problems
				if lc1.upper() in all_its:
					bad_child = True
					break
				elif '0_' in lc1:
					lc1 = lc1.replace('0_','')
				else:
					pass

			elif child.tag.endswith('Literal'):
				regex1 = child.text.lower().replace(' ','_').replace("'", "")
		if bad_child:
			continue
		else:
			# print('got here')
			##update the dictionary
			# regex, it = all_lcs_dict[lc1]

			# print('exact synonym info:', lc1, regex1)
			if '...' in lc1:
				if '.{' in regex1:
					all_lcs_dict[lc1][0] = regex1
				else:
					pass

			# check that the dictionary is correct
			elif regex1 != all_lcs_dict[lc1][0]:
				print(regex1)
				print(all_lcs_dict[lc1])
				raise Exception('ERROR WITH LEXICAL CUES FROM ONTOLOGY AND CONFIRMING SYNONYMS')
			# the dictionary is correct and we continue
			else:
				pass



	##check that everything has a regex - updating so that we have something for the errors here and don't have to go back and figure it out

	##output all_lcs_dict so we have all the updated cues - with date
	with open('%s_%s.txt' % (ontology_file_path.replace('.owl', '_all_cues'), date.today()),
			  'w+') as all_lcs_output_file:
		all_lcs_output_file.write('%s\t%s\t%s\n' % ('LEXICAL CUE', 'SYNONYMS', 'IGNORANCE TYPE'))
		for lc in all_lcs_dict.keys():
			if None in all_lcs_dict[lc]:
				print(lc, all_lcs_dict[lc])
				all_lcs_dict[lc][0] = lc.replace('...', '.{0,20}')
				# raise Exception('ERROR: MISSING A REGEX FOR A CUE!')

			all_lcs_output_file.write('%s\t%s\t%s\n' %(lc, all_lcs_dict[lc][0], all_lcs_dict[lc][1]))






	# print(all_lcs_dict)
	# print(all_its)


	return all_lcs_dict, all_its



def regex_annotations(all_lcs_dict, pmc_doc_path, possible_section_names, section_info_per_doc, abstract_end):
	"""
	Using the regular expressions of the lexical cues to find all occurrences in the PMC file and output for the next step of automatically creating the xml file

	:param all_lcs: a list of all the linguistic cues inserted into the ontology from the previous script all_linguistic_cues()
	:param pmc_doc_path: the file path to one pmc document at a time to run
	:return: all_occurrence_dict: a dictionary from (ontology_cue, ignorance_type) -> [regex, occurrences_list] to be used in the creation of the xml files automatically next
	"""
	print('CURRENT DOCUMENT: ', pmc_doc_path.split('/')[-1])
	pmc_full_text_file = open(pmc_doc_path, 'r+')
	pmc_full_text = pmc_full_text_file.read() #the whole pmc file text - all lowercase


	# if demoji.findall(pmc_full_text):
	# 	emoji_dict = demoji.findall(pmc_full_text)
	# 	print(emoji_dict)
	#
	# 	for d in emoji_dict:
	# 		print(len(d))
	# 		print(len(d.encode('utf-8')))
	# 		print(pmc_full_text.count(d))
	#
	# 	raise Exception('ERROR WITH UNICODE CHARACTERS!')


	emoji_info = [] #emoji start index
	neutral_emoji = u"\U0001F610"

	if neutral_emoji in pmc_full_text:
		# print(pmc_full_text.count(neutral_emoji))
		emoji_count = pmc_full_text.count(neutral_emoji)
		emoji_start = 0

		for i in range(emoji_count):
			emoji_info += [pmc_full_text.index(neutral_emoji, emoji_start)]
			emoji_start = emoji_info[-1] + 1
		# print(emoji_info)

		# print(demoji.findall(pmc_full_text))
		# print(type(pmc_full_text))
		# print(u"\U0001F610".encode('utf-8'))
		# print(len(u"\U0001F610".encode('utf-8')))
		# print(pmc_full_text[pmc_full_text.index(u"\U0001F610"):pmc_full_text.index(u"\U0001F610")+ 100])
		# emoji_info +=
		# raise Exception('ERROR WITH UNICODE CHARACTERS!')


	##SECTION INFORMATION: starts specifically helpful #TODO: USE THE XML FILE TO FIND THE SECTION TAGS - JATS standard - in the .nxml.gz files (sec-type and sec-meta)
	# section_info_per_doc = [None for s in possible_section_names]

	for s in range(1, len(possible_section_names)):
		section_name = possible_section_names[s]
		section_name_regex = re.compile('%s.{0,20}\s' %(section_name))

		# try:
		if section_name in pmc_full_text.lower():

			section_name_regex_results = section_name_regex.search(pmc_full_text.lower(), abstract_end)
			if section_name_regex_results:
				# print('GOT HERE:', section_name)
				proxy_section_start = section_name_regex_results.start() #None if not there
				section_info_per_doc[s] = proxy_section_start


				# if proxy_section_start:
				# 	section_info_per_doc[s] = proxy_section_start


		# except:
		# 	raise Exception('ERROR AT SECTIONS STUFF')


	# ##SAVE THE OCCURRENCES PER ONTOLOGY TERM
	# all_occurrence_dict = {} #(ontology_cue, ignorance_type) -> [regex, occurrences_list]

	all_occurrence_ontology_cue = []
	all_occurrence_ignorance_type = []
	all_occurrence_regex_cue = []
	all_occurrence_cue_occurrence_list = []

	for lc in all_lcs_dict.keys():
		# if '{' in cue_info[1]: #check just the disjoint ones


		ontology_cue = lc
		regex_cue = all_lcs_dict[lc][0]
		ignorance_type = all_lcs_dict[lc][1]
		# print('regex information:', ontology_cue, regex_cue, ignorance_type)

		# print('CUE: ', regex_cue.replace('_', ' '))

		##find the start, end of the cue
		# print([regex_cue])
		if '?' in regex_cue:
			regex_cue = '\?' #? is a special character and so we need to escape it

		cue_occurrence_list = [(m.start(), m.end()) for m in re.finditer(regex_cue.replace('_',' ').lower(), pmc_full_text.lower())]
		##all lowercase - a list of tuples: [(492, 501), (660, 669), (7499, 7508), (13690, 13699), (17158, 17167), (20029, 20038), (20219, 20228), (20279, 20288), (28148, 28157)]




		# print('OCCURRENCES: ', cue_occurrence_list)

		##PREPROCESS THE CUE_OCCURRENCE_LIST
		updated_cue_occurrence_list = []



		for span_num in cue_occurrence_list:
			start = span_num[0]
			end = span_num[1]

			adding_count = 0
			##check to make sure it has the correct information:
			if emoji_info:
				for e in emoji_info:
					if start > e:
						adding_count += 1
					else:
						break

			start += adding_count
			end += adding_count



			##TODO: UPDATE HERE FOR PREPROCESSING!
			# if adding_count == 0:
			##A) IS/OR/IF/HERE/HOW/EVEN WITHIN A WORD: GET RID OF IT
			#or 'is'==regex_cue or 'if'==regex_cue  or 'even' in regex_cue  or 'here' == regex_cue or 'how' == regex_cue or 'can' == regex_cue or 'weight' == regex_cue or 'issue' == regex_cue or 'view' == regex_cue
			if '}or' in regex_cue or '_or' in regex_cue or '}if' in regex_cue or 'here.' in regex_cue or regex_cue in ['is', 'if', 'even', 'here', 'how', 'can', 'weight', 'issue', 'view', 'call', 'other', 'lack', 'further', 'question', 'less', 'tend', 'differ', 'or', 'new', 'only', 'effect', 'fits', 'as', 'as_in', 'but', 'require', 'do', 'issues', 'rough', 'say', 'mediate', 'some', 'are', 'no', 'so']:
				if regex_cue in ['or', 'weight', 'is', 'are']:
					pass

				elif pmc_full_text[start-1-adding_count].isalpha() or pmc_full_text[end-adding_count].isalpha(): #end index not included
					# print(regex_cue, ' WITHIN ',pmc_full_text[start-5:end+5])
					pass
				else:
					updated_cue_occurrence_list += [(start, end)]
			else:
				updated_cue_occurrence_list += [(start, end)]

		##one entry for each occurrence
		for span_info in updated_cue_occurrence_list:
			# print(span_info)
			all_occurrence_ontology_cue += [ontology_cue]
			all_occurrence_ignorance_type += [ignorance_type]
			all_occurrence_regex_cue += [regex_cue]
			all_occurrence_cue_occurrence_list += [span_info]


		# all_occurrence_dict[(ontology_cue, ignorance_type)] = [regex_cue, updated_cue_occurrence_list]



	# return all_occurrence_dict

	##CHECK THAT THEY ARE ALL THE SAME LENGTH LIKE A DICTIONARY

	if len(all_occurrence_cue_occurrence_list) != len(all_occurrence_ignorance_type) or len(all_occurrence_ignorance_type) != len(all_occurrence_ontology_cue) or len(all_occurrence_ontology_cue) != len(all_occurrence_regex_cue):
		raise Exception('ERROR WITH OCCURRENCE LISTS FOR ONLY TAKING THE LARGEST SPAN!!')


	return all_occurrence_ontology_cue, all_occurrence_ignorance_type, all_occurrence_regex_cue, all_occurrence_cue_occurrence_list, section_info_per_doc



def recurse_largest_span(sorted_indicies_of_occurrence_list, all_occurrence_cue_occurrence_list, indicies_to_keep, max_index, sem_tag):

	"""

	:param sorted_indicies_of_occurrence_list: indicies that would sort the list by the start value
	:param all_occurrence_cue_occurrence_list: a list of tuples of start and end: [(start, end)]
	:param indicies_to_keep: initially an empty list that will grow if it passes the tests and be output at the end
	:param max_index: the maximum value that an index should be to ensure I don't go over
	:param sem_tag: 's', 'e', or 'm' for where to focus the recurrsion on start, end or middle respectively
	:return: indicies_to_keep: a list of the indicies of the largest spans
	"""
	##return the list of indicies to keep
	# print('INDICIES TO KEEP:', indicies_to_keep)

	##recursive (see notes)
	# print(all_occurrence_cue_occurrence_list[sorted_indicies_of_occurrence_list[0]])
	# print(sorted_indicies_of_occurrence_list)

	##there is only one cue so we are good to keep it all!
	if len(sorted_indicies_of_occurrence_list) == 1:
		return sorted_indicies_of_occurrence_list

	##multiple cues to check!
	else:

		##ALWAYS TRUE FOR ALL SEM_TAGs
		start1 = all_occurrence_cue_occurrence_list[sorted_indicies_of_occurrence_list[0]][0]
		end1 = all_occurrence_cue_occurrence_list[sorted_indicies_of_occurrence_list[0]][1]
		length1 = end1-start1

		start2 = all_occurrence_cue_occurrence_list[sorted_indicies_of_occurrence_list[1]][0]
		end2 = all_occurrence_cue_occurrence_list[sorted_indicies_of_occurrence_list[1]][1]
		length2 = end2-start2


		if len(indicies_to_keep) > 1 and max(indicies_to_keep) > max_index + 1:
			print(max(indicies_to_keep))
			print(max(sorted_indicies_of_occurrence_list))
			raise Exception('ERROR WITH INDICIES TO KEEP GOING OVER MAXIMUM!!')

		# print('CHECKIN!',len(sorted_indicies_of_occurrence_list))
		# print(max(sorted_indicies_of_occurrence_list))
		# if len(indicies_to_keep) > 1:
		# 	print(max(indicies_to_keep))

		# print('STARTS', start1, start2)
		# print('LENGTH OF ITERATING', len(sorted_indicies_of_occurrence_list))

		# print(sorted_indicies_of_occurrence_list)
		if sem_tag == 's':
			##BASE CASE
			if len(sorted_indicies_of_occurrence_list) == 2:

				##focusing on starts

				if start1 != start2:
					# print('starts not equal at the end', sorted_indicies_of_occurrence_list)
					indicies_to_keep += sorted_indicies_of_occurrence_list
				else:
					if length1 >= length2:
						indicies_to_keep += [sorted_indicies_of_occurrence_list[0]]
					else:
						indicies_to_keep += [sorted_indicies_of_occurrence_list[1]]

				# print('MADE IT HERE!!')
				# print(indicies_to_keep)
				# print(start1, start2)
				# print(sorted_indicies_of_occurrence_list)
				# print(indicies_to_keep)
				return indicies_to_keep


			##RECURSION - starts currently
			elif start1 != start2:
				indicies_to_keep += [sorted_indicies_of_occurrence_list[0]]

				# print('SORTED_LIST:', sorted_indicies_of_occurrence_list[1:])
				# print(len(sorted_indicies_of_occurrence_list[1:]))

				return recurse_largest_span(sorted_indicies_of_occurrence_list[1:], all_occurrence_cue_occurrence_list, indicies_to_keep, max_index, sem_tag)

			else:
				if length1 >= length2:
					# print('got here')
					# print(sorted_indicies_of_occurrence_list[0:10])
					# print(start1, start2)
					# print([sorted_indicies_of_occurrence_list[0]])
					# print(sorted_indicies_of_occurrence_list[2:10])
					# print(type(sorted_indicies_of_occurrence_list))
					# print('updated to recurse', [list(sorted_indicies_of_occurrence_list)[0]]+list(sorted_indicies_of_occurrence_list)[2:10])
					# print('DONE HERE!')

					return recurse_largest_span([sorted_indicies_of_occurrence_list[0]]+sorted_indicies_of_occurrence_list[2:], all_occurrence_cue_occurrence_list, indicies_to_keep, max_index, sem_tag)
				else:
					# print('and here')
					return recurse_largest_span([sorted_indicies_of_occurrence_list[1]] + sorted_indicies_of_occurrence_list[2:], all_occurrence_cue_occurrence_list, indicies_to_keep, max_index, sem_tag)

		##focusing on ends
		elif sem_tag == 'e':

			##BASE CASE
			if len(sorted_indicies_of_occurrence_list) == 2:
				if end1 != end2:
					indicies_to_keep += sorted_indicies_of_occurrence_list
				else:
					if length1 >= length2:
						indicies_to_keep += [sorted_indicies_of_occurrence_list[0]]
					else:
						indicies_to_keep += [sorted_indicies_of_occurrence_list[1]]
				return indicies_to_keep

			##RECURSION
			elif end1 != end2:
				indicies_to_keep += [sorted_indicies_of_occurrence_list[0]]
				return recurse_largest_span(sorted_indicies_of_occurrence_list[1:], all_occurrence_cue_occurrence_list, indicies_to_keep, max_index, sem_tag)

			else:
				if length1 >= length2:
					return recurse_largest_span(
						[sorted_indicies_of_occurrence_list[0]] + sorted_indicies_of_occurrence_list[2:],
						all_occurrence_cue_occurrence_list, indicies_to_keep, max_index, sem_tag)
				else:
					# print('and here')
					return recurse_largest_span(
						[sorted_indicies_of_occurrence_list[1]] + sorted_indicies_of_occurrence_list[2:],
						all_occurrence_cue_occurrence_list, indicies_to_keep, max_index, sem_tag)

		##focusing on middles
		elif sem_tag == 'm':
			##BASE CASE
			if len(sorted_indicies_of_occurrence_list) == 2:
				if not (start2 > start1 and end1 > end2):
					indicies_to_keep += sorted_indicies_of_occurrence_list
				else:
					if length1 >= length2:
						indicies_to_keep += [sorted_indicies_of_occurrence_list[0]]
					else:
						indicies_to_keep += [sorted_indicies_of_occurrence_list[1]]
				return indicies_to_keep

			##RECURSION
			elif not (start2 > start1 and end1 > end2):
				indicies_to_keep += [sorted_indicies_of_occurrence_list[0]]
				return recurse_largest_span(sorted_indicies_of_occurrence_list[1:], all_occurrence_cue_occurrence_list,
											indicies_to_keep, max_index, sem_tag)

			else:
				if length1 >= length2:
					return recurse_largest_span(
						[sorted_indicies_of_occurrence_list[0]] + sorted_indicies_of_occurrence_list[2:],
						all_occurrence_cue_occurrence_list, indicies_to_keep, max_index, sem_tag)
				else:
					# print('and here')
					return recurse_largest_span(
						[sorted_indicies_of_occurrence_list[1]] + sorted_indicies_of_occurrence_list[2:],
						all_occurrence_cue_occurrence_list, indicies_to_keep, max_index, sem_tag)

		else:
			raise Exception('SEM_TAG CAN ONLY BE s, e or m AND NOTHING ELSE. WRONG TAG ENTERED.')


def only_take_largest_span(all_occurrence_ontology_cue, all_occurrence_ignorance_type, all_occurrence_regex_cue, all_occurrence_cue_occurrence_list, pmc_doc_path):



	pmc_full_text_file = open(pmc_doc_path, 'r+')
	pmc_full_text = pmc_full_text_file.read().lower()  # the whole pmc file text - all lowercase

	##SAVE THE OCCURRENCES PER ONTOLOGY TERM
	all_occurrence_dict = {}  # (ontology_cue, ignorance_type, index_to_keep) -> [regex, occurrences_list]

	# print(all_occurrence_cue_occurrence_list)
	only_start_occurrences = [s for (s,e) in all_occurrence_cue_occurrence_list]
	sorted_indicies_of_occurrence_list_starts = np.argsort(only_start_occurrences).tolist()  # indicies that would sort the list by the start value
	only_end_occurrences = [e for (s,e) in all_occurrence_cue_occurrence_list]
	sorted_indicies_of_occurrence_list_ends = np.argsort(only_end_occurrences).tolist() #indices that would sort the list by the end values


	# print(type(sorted_indicies_of_occurrence_list))


	# sorted_occurrence_list = [only_start_occurrences[i] for i in sorted_indicies_of_occurrence_list]
	# print('SORTED LIST', sorted_occurrence_list)

	# print(len(sorted_indicies_of_occurrence_list))
	# print('SORTED INDICIES LIST', sorted_indicies_of_occurrence_list[0:10])


	##RECURSE TO GET THE LARGEST SPAN!
	indicies_to_keep_starts = []
	indicies_to_keep_ends = []
	indicies_to_keep_middles = []

	# print(sorted_indicies_of_occurrence_list)
	max_index = max(sorted_indicies_of_occurrence_list_starts)
	# print('TOTAL OCCURRENCES BEFORE RECURSION:', max_index)
	# print([all_occurrence_ontology_cue[a] for a in sorted_indicies_of_occurrence_list][:15])

	##recurse over start, end and middle to get rid of these
	# print(sorted_indicies_of_occurrence_list_starts)
	indicies_to_keep_starts = recurse_largest_span(sorted_indicies_of_occurrence_list_starts, all_occurrence_cue_occurrence_list, indicies_to_keep_starts, max_index, 's')
	# print('STARTS DONE:', len(indicies_to_keep_starts))
	indicies_to_keep_ends = recurse_largest_span(sorted_indicies_of_occurrence_list_ends, all_occurrence_cue_occurrence_list, indicies_to_keep_ends, max_index, 'e')
	# print('ENDS DONE:', len(indicies_to_keep_ends))
	indicies_to_keep_middles = recurse_largest_span(sorted_indicies_of_occurrence_list_starts, all_occurrence_cue_occurrence_list, indicies_to_keep_middles, max_index, 'm')
	# print('MIDDLES DONE:', len(indicies_to_keep_middles))

	# print('made it here!')

	# print('INDICIES TO KEEP LENGTH', len(indicies_to_keep))
	# print([all_occurrence_ontology_cue[b] for b in indicies_to_keep][:15])
	# print('MAX',max(sorted_indicies_of_occurrence_list))


	#
	##PUT EVERYTHING BACK INTO THE DICTIONARY FORMAT
	#
	# print(type(indicies_to_keep))
	# print(max(indicies_to_keep))

	indicies_to_keep = list(set(indicies_to_keep_starts) & set(indicies_to_keep_ends) & set(indicies_to_keep_middles))
	# print('INDICIES TO KEEP DONE:', len(indicies_to_keep))
	print('PROGRESS: finished recursion!', len(indicies_to_keep))

	for k in indicies_to_keep:
		# print(k)
		# print(len(all_occurrence_ontology_cue))
		# print(len(all_occurrence_ignorance_type))
		# print(all_occurrence_ontology_cue[k])
		# print(all_occurrence_ignorance_type[k])
		# print(all_occurrence_regex_cue[k])
		# print(all_occurrence_cue_occurrence_list[k])

		if all_occurrence_dict.get((all_occurrence_ontology_cue[k], all_occurrence_ignorance_type[k], k)):
			raise Exception('HUGE ERROR WITH DICTIONARY THAT IS OVERWRITING!')

		all_occurrence_dict[(all_occurrence_ontology_cue[k], all_occurrence_ignorance_type[k], k)] = [all_occurrence_regex_cue[k], all_occurrence_cue_occurrence_list[k]]

	return all_occurrence_dict


def xml_creation(pmc_doc_path, all_occurrence_dict, xml_output_path, weird_lcs):
	"""
	Create a new xml file of annotations based on the regex automatic preprocessing for one document at a time to paralellize
	:param pmc_doc_path: pmc file path to know what document we have and how to name the annotation file:
	:param all_occurrence_dict: a dictionary from (ontology_cue, ignorance_type) -> [regex, occurrences_list] to be used in the creation of the xml files automatically
	:param xml_output_path: the output file path for the xml files (ideally to the Annotations folder for knowtator)
	:param all_lcs: a list of all the linguistic cues inserted into the ontology from the previous script all_linguistic_cues()
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
	pmc_output_name = pmc_doc_path.split('/')[-1].replace('.txt', '')
	# print(pmc_output_name)


	##THE FULL TEXT DOCUMENT
	pmc_full_text_file = open(pmc_doc_path, 'r+')
	pmc_full_text = pmc_full_text_file.read()  # the whole pmc file text - all lowercase



	##CREATE THE XML FILE WITH HEADERS AND STRUCTURE
	##TODO: need to add the encoding and standalone as node declarations!!!


		#SET THE ELEMENTS OF THE TREE:


	knowtator_project = ET.Element('knowtator-project') #root element
	doc_element = ET.SubElement(knowtator_project, 'document')

		##WITHIN THE DOCUMENT SET ALWAYS






	##ADD IN EACH ANNOTATION - MAKING SURE TO TAKE ONLY ONES WITH OCCURRENCES OF LCS
		# PUT IN TEXT - SET = ADDING AN ATTRIBUTE
		# all_occurrence_dict[(ontology_cue, ignorance_type)] = [regex_cue, cue_occurrence_list]



	doc_element.set('id', '%s' %(pmc_output_name))
	doc_element.set('text-file', '%s' %(pmc_output_name+'.txt'))

	##loop over all occurrences to get them all under the documents: # (ontology_cue, ignorance_type, index_to_keep) -> [regex, occurrences_list]
	iterator = 1
	for lc_it_k in all_occurrence_dict.keys():
		lexical_cue = lc_it_k[0]
		ignorance_type = lc_it_k[1]
		kept_index = lc_it_k[2]
		regex_cue = all_occurrence_dict[lc_it_k][0]
		cue_occurrence_list = all_occurrence_dict[lc_it_k][1]
		# print(cue_occurrence_list)

		if len(cue_occurrence_list) > 0:
			# print(cue_occurrence_list)
			# for span_nums in cue_occurrence_list:
			# 	# print(span_nums)

			# start = span_nums[0]
			# end = span_nums[1]

			start = cue_occurrence_list[0]
			end = cue_occurrence_list[1]


			##HANDLING DISJOINT CUES

			if '...' in lexical_cue:
				if lexical_cue.replace('...', ' ') == pmc_full_text[start:end]:
					# print('GOT HERE!!')
					all_starts = [start]
					all_ends = [end]


				else:
					disjoint_cue = lexical_cue.split('...') #list of the disjointness
					all_starts = [None for i in range(len(disjoint_cue))]
					all_ends = [None for i in range(len(disjoint_cue))]

					for d in range(len(disjoint_cue)):
						if d == 0:
							disjoint_start = start
							disjoint_end = start + len(disjoint_cue[d])
						elif d != len(disjoint_cue)-1:
							disjoint_start = pmc_full_text.lower().index(disjoint_cue[d], start, end) ##added start+1
							disjoint_end = disjoint_start + len(disjoint_cue[d])
						else: #at the end of the disjoint cue
							disjoint_start = end - len(disjoint_cue[d]) #-1
							disjoint_end = end

						all_starts[d] = disjoint_start
						all_ends[d] = disjoint_end






			else:
				all_starts = [start]
				all_ends = [end]




			annotation = ET.SubElement(doc_element, 'annotation')
			class_id = ET.SubElement(annotation, 'class')





			annotation.set('annotator', 'Default')
			annotation.set('id', '%s-%s' %(pmc_output_name, iterator))
			annotation.set('type', 'identity')


			##if there is duplicate names we have the weird lcs with "0_" to help with this
			if lexical_cue in weird_lcs:
				class_id.set('id', '0_%s' % (lexical_cue))
			else:
				class_id.set('id', '%s' %(lexical_cue))

			iterator += 1

			# print(pmc_full_text[start:end])
			# print(all_starts)
			# print(all_ends)

			for s in range(len(all_starts)):
				span = ET.SubElement(annotation, 'span')

				start_final = all_starts[s]
				end_final = all_ends[s]
				span.set('end', '%s' %(end_final))
				span.set('id', '%s-%s' %(pmc_output_name, iterator))
				span.set('start', '%s' %(start_final))
				span.text = '%s' %pmc_full_text[start_final:end_final]





				iterator += 1







	##OUTPUT THE XML FILE TO THE ANNOTATIONS FILE

	xml_annotations_file = minidom.parseString(ET.tostring(knowtator_project)).toprettyxml(indent="   ")
	with open(xml_output_path + '%s' %(pmc_output_name+'.xml'), "w") as file_output:
		file_output.write(xml_annotations_file)







if __name__=='__main__':
	# all_ontology_inserted_lcs_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Development_Pre_natal_nutrition/Prenatal_Nutrition_Python_Scripts/ALL_ONTOLOGY_INSERTED_LCS.txt'
	#


	##grab everything from the newest ontology
	ontology_file_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/1_First_Full_Annotation_Task_9_13_19/Ontologies/Ontology_Of_Ignorance.owl'

	broad_categories = ['EPISTEMICS', 'BARRIERS', 'LEVELS_OF_EVIDENCE']
	all_lcs_dict, all_its = updated_ontology_cues(ontology_file_path, broad_categories)
	print(all_its)

	print('PROGRESS: all linguistic cues gathered to start automatic regex annotation preprocessing steps!')

	# raise Exception('HOLD!')

	pmc_doc_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/1_First_Full_Annotation_Task_9_13_19/Articles/'

	xml_output_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/1_First_Full_Annotation_Task_9_13_19/Annotations/'

	output_summary_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Development_Pre_natal_nutrition/Prenatal_Nutrition_Python_Scripts/automatic_ontology_insertion/'

	##COLLECT ALL THE PMC FILENAMES TO PARALLELIZE OVER
	all_pmc_articles_list = []

	# weird_lcs = ['unexpected_observation', 'controversy', 'difficult_task', 'urgent_call_to_action', 'alternative_options', 'claim', 'model', 'possible_understanding']

	weird_lcs = ['unexpected_observation', 'difficult_task', 'important_considerations', 'claim', 'model', 'possible_understanding']

	possible_section_names = ['abstract', 'introduction', 'background', 'method', 'results', 'conclusion', 'discussion']
		##PMC6029118.nxml.gz.txt.gz.meta	PMC XML	abstract	[222..2657]

	abstract_info_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/1_First_Full_Annotation_Task_9_13_19/document_collection_pre_natal/'


	##LINEAR LOOP FOR EACH FILE
	f = 0 ##total number of files prerprocessing with at least one cue identified
	info_per_doc = {} #pmc_id -> [num_cues_per_doc, num_unique_ignorance_types, list of unique_ignorance_types, num_cues_per_section, unique_ignorance_types_per_section]
	all_ignorance_types = list(all_its)
	# doc_counts_all_its = {}
	# for it in all_ignorance_types:
	# 	doc_counts_all_its[it] = 0



	for root, directories, filenames in os.walk(pmc_doc_path):
		for filename in sorted(filenames):
			##TODO: segmentation fault 11 error with file PMC4896250
			if filename.endswith('.nxml.gz.txt') and 'PMC4896250' not in filename:
				#and 'PMC2595955.nxml.gz.txt' in filename:

				# print(root + filename)
				# if f < 15:
				# if 'PMC4990268' in filename:
				# print('MADE IT HERE')
				# print(root+filename)

				# if 'PMC3205727' in filename:
				all_pmc_articles_list += [root+filename]

				##collect the abstract information
				section_info_per_doc = [None for s in possible_section_names]


				##not all files have a meta-section.annot.gz file but they all have a -sections.annot.gz file

				try:
					abstract_info_file = gzip.open(abstract_info_path + filename + '.gz.meta-sections.annot.gz', 'rt+')

				except FileNotFoundError:
					abstract_info_file = gzip.open(abstract_info_path + filename + '.gz-sections.annot.gz', 'rt+')


				abstract_start = 0
				abstract_end = 0
				for line in abstract_info_file:
					# print(type(line))
					if 'abstract' in line:
						abstract_start = int(line.split('\t')[-1].split('..')[0].replace('[', ''))
						abstract_end = int(line.split('\t')[-1].split('..')[1].replace(']', ''))
						break
					else:

						pass


				abstract_info_file.close()

				section_info_per_doc[0] = abstract_start


				##LOOP OVER EACH FILE

				(all_occurrence_ontology_cue, all_occurrence_ignorance_type, all_occurrence_regex_cue, all_occurrence_cue_occurrence_list, section_info_per_doc) = regex_annotations(all_lcs_dict, root + filename, possible_section_names, section_info_per_doc, abstract_end)


				##SAVE THE SECTION STARTS WITH THE DOCUMENT FILES:
				updated_section_info_per_doc = [] #tuples of the section and start
				with gzip.open(abstract_info_path+filename+'.gz.regex-sections.annot.gz', 'wt+') as pmc_section_info_file:
					for s in range(len(section_info_per_doc)):
						if section_info_per_doc[s]:
							pmc_section_info_file.write('%s\t%s\t%s\t%s\n' %(filename, 'PMC XML', possible_section_names[s], section_info_per_doc[s]))
							updated_section_info_per_doc += [(possible_section_names[s], section_info_per_doc[s])]


				final_section_info_per_doc = sorted(updated_section_info_per_doc, key=lambda x: x[1])
				# print('GOT HERE!')
				# print(final_section_info_per_doc)
				##ISSUES WITH RECURSION MAX WHICH SEEMED TO BE FIXED BUT WANT TO CATCH THEM IF AN ISSUE IN THE FUTURE (CURRENT MAX IS 4000)
				try:
					##has to have at least one cue in it
					if len(all_occurrence_regex_cue):
						# print(len(all_occurrence_regex_cue))
						# print(all_occurrence_regex_cue)
						# print(all_occurrence_cue_occurrence_list)
						## (ontology_cue, ignorance_type, index_to_keep) -> [regex, occurrences_list]
						all_occurrence_dict = only_take_largest_span(all_occurrence_ontology_cue, all_occurrence_ignorance_type, all_occurrence_regex_cue, all_occurrence_cue_occurrence_list, root + filename)



						xml_creation(root+filename, all_occurrence_dict, xml_output_path, weird_lcs)





						##SUMMARY STUFF FROM PREPROCESSING: use all_occurrence_dict
						f += 1
						num_cues_per_section = [0 for p in final_section_info_per_doc]
						unique_ignorance_types_per_section = [set([]) for p in final_section_info_per_doc]


						# num_cues_per_doc += [(filename.replace('.nxml.gx.txt',''), len(all_occurrence_dict.keys()))]
						unique_ignorance_types = set([])
						for a in all_occurrence_dict.keys():
							if len(unique_ignorance_types) == len(all_ignorance_types):
								pass #if all are added no need to add anymore
							else:
								unique_ignorance_types.add(a[1]) #add the ignorance type


							##collect information about sections
							# print(final_section_info_per_doc)
							# print(final_section_info_per_doc[-1])
							# print(final_section_info_per_doc[-1][1])
							if final_section_info_per_doc and all_occurrence_dict[a][1][1] > final_section_info_per_doc[-1][1]:
								num_cues_per_section[-1] += 1
								unique_ignorance_types_per_section[-1].add(a[1])
							elif final_section_info_per_doc:
								for s in range(len(final_section_info_per_doc)):
									section_start = final_section_info_per_doc[s][1] #start of the section


									if all_occurrence_dict[a][1][1] < section_start: #the end of the cue - added <= (not just greater)
										num_cues_per_section[max(0,s-1)] += 1 #the cue is in the section prior - TODO: will error if its in the title before the abstract or if an abstract doesn't exist
										unique_ignorance_types_per_section[max(0, s-1)].add(a[1]) #add the ignorance type to see if new
										break

									else:
										pass







						#check if the sections are correct:
						if len(final_section_info_per_doc) > 0 and sum(num_cues_per_section) != len(all_occurrence_dict.keys()):
							print(num_cues_per_section)
							print(sum(num_cues_per_section))
							print(len(all_occurrence_dict.keys()))
							raise Exception("ERROR WITH SECTION GATHERING AND MATCHING NUMBERS!")



						info_per_doc[filename.replace('.nxml.gx.txt','')] = [len(all_occurrence_dict.keys()), len(list(unique_ignorance_types)), list(unique_ignorance_types), final_section_info_per_doc, num_cues_per_section, unique_ignorance_types_per_section]


					else: ##no cues in it at all
						with open('%sfiles_with_no_lexical_cues_%s.txt' %(output_summary_path,date.today()), 'a+') as no_cues_file:
							no_cues_file.write('%s\n' % (root + filename)) #2 files with just the title in them



				##recursion limit is 1000
				except RecursionError:

					with open('%srecursion_error_files_%s.txt' %(output_summary_path, date.today()), 'a+') as recursion_errors:
						recursion_errors.write('%s\t%s\n' %(root+filename, len(all_occurrence_regex_cue)))


					print('RECURSION ERROR!')
					print(root + filename)
					print(len(all_occurrence_regex_cue))
					print(set(all_occurrence_regex_cue))
					# raise Exception('HOLD!')

				# else:
				# 	break



	with open('%spreprocess_summary_info_%s.txt' %(output_summary_path, date.today()), 'w+') as preprocess_summary_file:
		preprocess_summary_file.write('%s\n' %'SUMMARY FILE FOR PREPROCESS USING REGULAR EXPRESSIONS')
		preprocess_summary_file.write('\t%s\n' %('preprocess rules to get rid of: or, is, if, even, here, how  in the middle of a sentence'))
		preprocess_summary_file.write('\t%s\n\n' %'preprocess rules to only keep the largest span if the starts are the same')

		preprocess_summary_file.write('%s\n' %('SUMMARY INFORMATION:'))
		preprocess_summary_file.write('\t%s\t%s\n\n' %('total number of preprocessed documents (docs with cues):',f))



		##pmc_id -> [num_cues_per_doc, num_unique_ignorance_types, list of unique_ignorance_types, num_cues_per_section, unique_ignorance_types_per_section]

		preprocess_summary_file.write('%s\t%s\t%s\t%s\t%s\n' %('FILENAME', 'NUMBER OF CUES PER DOCUMENT', 'NUMBER OF UNIQUE IGNORANCE TYPES PER DOCUMENT','LIST OF UNIQUE IGNORANCE TYPES', 'PER SECTION INFORMATION BELOW'))
		for doc in info_per_doc.keys():
			preprocess_summary_file.write('%s\t%s\t%s\t%s\n' %(doc, info_per_doc[doc][0], info_per_doc[doc][1], info_per_doc[doc][2]))

			##section info
			for p in range(len(info_per_doc[doc][3])):
				preprocess_summary_file.write('\t%s' % info_per_doc[doc][3][p][0])
			preprocess_summary_file.write('\n')

			##number of cues per section
			for p in range(len(info_per_doc[doc][3])):
				preprocess_summary_file.write('\t%s' % info_per_doc[doc][4][p])
			preprocess_summary_file.write('\n')

			# number of unique ignorance types per section
			for p in range(len(info_per_doc[doc][3])):
				preprocess_summary_file.write('\t%s' % len(info_per_doc[doc][5][p]))
			preprocess_summary_file.write('\n')


			# for p in range(len(possible_section_names)):
			# 	if info_per_doc[doc][3][p]:
			# 		preprocess_summary_file.write('\t%s' %possible_section_names[p])
			# preprocess_summary_file.write('\n')
			#
			#
			# ##number of cues per section
			# for p in range(len(possible_section_names)):
			# 	if info_per_doc[doc][3][p]:
			# 		preprocess_summary_file.write('\t%s' % info_per_doc[doc][4][p])
			# preprocess_summary_file.write('\n')
			#
			#
			# #number of unique ignorance types per section
			# for p in range(len(possible_section_names)):
			# 	if info_per_doc[doc][3][p]:
			# 		preprocess_summary_file.write('\t%s' %len(info_per_doc[doc][5][p]))
			# preprocess_summary_file.write('\n')




	# ##TODO: ERROR WITH PARALLELIZING - SUPER UNCLEAR!!
	# # Step 1: Init multiprocessing.Pool()
	# pool = mp.Pool(mp.cpu_count())
	# func = functools.partial(regex_annotations, all_lcs)
	# print(pool.map(func, all_pmc_articles_list))
	# output = pool.map(func, all_pmc_articles_list)
	# pool.close()
	# pool.join()
	# # print(output)


	##ONE FILE PROCESS!

	# one_pmc_doc_path = 'PMC6056931.nxml.gz.txt'
	#
	#
	# all_occurrence_dict = regex_annotations(all_lcs, pmc_doc_path+one_pmc_doc_path)
	#
	# xml_creation(pmc_doc_path+one_pmc_doc_path, all_occurrence_dict, xml_output_path)





