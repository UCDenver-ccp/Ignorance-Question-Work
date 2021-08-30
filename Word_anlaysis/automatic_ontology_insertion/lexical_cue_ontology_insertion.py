import os
import re
import gzip
import argparse
import numpy as np
import nltk.data
import sys
import string
import xml.etree.ElementTree as ET
from lxml import etree
# from owlready2 import * #python 3
from xml.dom import minidom


def intersection(lst1, lst2):
	return list(set(lst1) & set(lst2))


def update_full_linguistic_cues(all_linguistic_cues_full_path, it_dict):
	with open(all_linguistic_cues_full_path.replace('_FULL.txt','_FULL_UPDATED.txt'), 'w+') as updated_all_cues:
		updated_all_cues.write('%s\t%s\n' %('FULL_LEXICAL_CUE', 'UPDATED_IGNORANCE_TYPE'))

		with open(all_linguistic_cues_full_path, 'r') as all_cues:
			next(all_cues) #first line is the headers
			for line in all_cues:
				cue = line.split('\t')[0]
				it = line.strip('\n').split('\t')[1]
				if it in it_dict.keys():
					new_it = it_dict[it]
				else:
					new_it = it

				updated_all_cues.write('%s\t%s\n' %(cue, new_it))






##run in python2 because the rules of mapping a function changed
def retrieve_guideline_examples(all_linguistic_cues_full_path, guideline_example_path, ignorance_types, it_dict):
	"""retrieve the lexical cue (uppercase) - connect it to the other files - and the positive (< >) and negative examples
	 	goal: dictionary from lexical cue to positive and negative examples"""

	##READ IN ALL THE CUES TO ADD TO THE ONTOLOGY FILE - currently all have '_' instead of spaces


	lexical_cues_to_add = {}
	with open(all_linguistic_cues_full_path, 'r+') as all_linguistic_cues_full_file:
		for line in all_linguistic_cues_full_file:
			# print(line)
			all_lcs = [True if i == line.split('\t')[-1].replace('\n','') else False for i in ignorance_types]
			# print(all_lcs)
			if all_lcs.count(True) > 1:
				print(line)
				raise Exception('ERROR WITH IGNORANCE TYPES THAT A LINE HAS MORE THAN ONE')


			if True in all_lcs:
				original_lc = line.replace('\n', '').split('\t')[0]
				##get rid of regex ones like: whether.{0,206}compared, and replace with '...'
				new_lc = ''
				if '{' in original_lc:  # whether.{0,206}compared
					lc_list = original_lc.split('.')

					for l in lc_list:
						if '}' in l:
							new_lc += '...%s' % l.split('}')[-1]
						else:
							new_lc += '_%s' % l
					new_lc = new_lc[1:]
				else:
					new_lc = original_lc

				if "'" in original_lc:
					new_lc = original_lc.replace("'",'')

					# print(original_lc)



				##UPDATE THE IGNORANCE TYPE BASED ON THE DICTIONARY AT THE FRONT
				original_it = line.replace('\n', '').split('\t')[1]
				# if original_it in it_dict.keys():
				# 	new_it = it_dict[original_it]
				# else:
				# 	new_it = original_it


				##all lowercase, except for original_it
				lexical_cues_to_add[(new_lc, original_it)] = [[original_lc],[],[]] #synonyms '{}', positive examples, negative examples
				# if 'could' in original_lc:
				# 	print(original_lc, new_lc, new_it)

				# if 'rct' in new_lc:
				# 	print(new_lc)

	##EXPLICIT QUESTION ADD: WHICH/ WHEN; INCOMPLETE EVIDENCE ADD: evidence...weaker
	added_lcs = [('which', 'EXPLICIT_QUESTION'), ('when', 'EXPLICIT_QUESTION'), ('evidence...weaker', 'INCOMPLETE_EVIDENCE'), ('lack_of_rigor', 'INCOMPLETE_EVIDENCE'), ('not_been_studied','FULL_UNKNOWN'), ('feasible','PROBABLE_UNDERSTANDING'), ('are_warranted', 'FUTURE_WORK'), ('is_warranted','FUTURE_WORK'), ('further_testing', 'FUTURE_WORK'), ('further_trials','FUTURE_WORK'), ('further_consideration', 'FUTURE_WORK'), ('research_in_this_area','FUTURE_WORK'), ('more_studies','FUTURE_WORK'), ('until', 'FUTURE_WORK'), ('ominous', 'URGENT_CALL_TO_ACTION'), ('must...be', 'URGENT_CALL_TO_ACTION'), ('counterintuitive','UNEXPECTED_OBSERVATION'), ('rather', 'CONTROVERSY'), ('supposed_to', 'CONTROVERSY')]

	for alcs in added_lcs:
		if alcs[1] in it_dict.keys():
			lexical_cues_to_add[(alcs[0], it_dict[alcs[1]])] = [[alcs[0]], [], []]
		else:
			lexical_cues_to_add[(alcs[0], alcs[1])] = [[alcs[0]],[],[]]
			# print('GOT HERE')



	tough_lcs = {'LACK_OF_DATA': 'LACK_OF...DATA', 'ARE': 'IS', 'RECENTLY...Δ': 'RECENTLY', 'ABSENCE_OF_EVIDENCE':'ABSENCE_OF...EVIDENCE', 'DATA_IS_SPARSE': 'DATA...IS_SPARSE', 'IS_SCARCE_EVIDENCE':'EVIDENCE...IS_SCARCE', 'IS_SCARCE...EVIDENCE':'EVIDENCE...IS_SCARCE', 'EVIDENCE_IS_SCARCE':'EVIDENCE...IS_SCARCE', 'LIMITED...EVIDENCE':'EVIDENCE...LIMITED', 'INFORMATION_IS_SCARCE':'INFORMATION...IS_SCARCE', 'NEED_TO_IDENTIFY':'NEED_TO...IDENTIFY', 'REMAINS_UNDERSTUDIED':'REMAINS_UNDER-STUDIED', 'UNDER...STUDIED':'UNDER-STUDIED','EVIDENCE...BASED':'EVIDENCE-BASED', 'DATA_ARE_SPARSE':'DATA...ARE_SPARSE', 'PREVIOUS_STUDIES':'PREVIOUS...STUDIES', 'PARTIALLY...REMAINS':'REMAINS...PARTIALLY', 'COULD...ANDOR':'COULD...AND_OR', 'INTER...RELATIONSHIPS':'INTER-RELATIONSHIPS', 'LONGITUDINAL_STUDIES_ARE_NEEDED': 'LONGITUDINAL_STUDIES...ARE_NEEDED', 'RCT_IS_NEEDED':'RCT_IS...NEEDED', 'RCT...IS_NEEDED':'RCT_IS...NEEDED', 'LONGER_TERM_FOLLOWUP_IS_NEEDED':'LONGER_TERM_FOLLOW-UP_IS_NEEDED','NEED_TO_BE_REEVALUATED':'NEED_TO_BE_RE-EVALUATED', 'NEED_TO_DEVELOP_STRATEGIES': 'NEED_TO_DEVELOP...STRATEGIES', 'LONGTERM_STUDIES':'LONG-TERM_STUDIES', 'HARD...TO...REACH':'HARD-TO-REACH', 'REMAIN_A_PROBLEM':'REMAIN_A...PROBLEM', 'HAS_BEEN_CHALLENGED':'HAS_BEEN...CHALLENGED'}

	##GATHER ALL EXAMPLES PER FILE
	for root, directories, filenames in os.walk(guideline_example_path):
		for filename in sorted(filenames):
			if filename.endswith('_examples.txt'):
				# print(filename)
				print(filename.split('_examples.txt')[0].upper())

				if filename.split('_examples.txt')[0].upper() in ignorance_types: #specific ignorance type
					filename_path = os.path.join(root,filename)
					missing_count = 0
					with open(filename_path, 'r+') as file:

						missing_cue_file_temp = open(root+filename.replace('_examples.txt','_temp_missing.txt'), 'w+')
						for line in file:
							##keep only the lines with positive and negative examples in them
							if line[0].isdigit() and '“EXAMPLE” [EXAMPLE]' not in line and '[' in line:
								# print(line.strip('\n'))

								full_example = line.strip('\n')[line.index(')')+2:].split('” [') ##sentence + explanation split up

								##ERROR THAT THE FULL EXAMPLE SPLIT IS NOT WORKING - ALWAYS SHOULD BE AT LEAST 2 AND GENERALLY ONLY 2 BECAUSE SENTENCE AND EXPLANATION
								if len(full_example) < 2:
									print('PROBLEM WITH THE FULL EXAMPLE READING IN THE FILE')
									print(full_example)
									print(len(full_example))
									raise Exception('PROBLEM WITH THE FULL EXAMPLE READING IN THE FILE')

								example_sentence = full_example[0] + '”'
								example_sentence_split = example_sentence.split(' ')
								example_explanation = '[' + full_example[1]


								# if 'RCT' in example_sentence:
								# 	print(example_sentence)


								# print(example_sentence)
								# print(example_sentence.split(' '))

								lc_indicies = []
								for w in range(len(example_sentence_split)):
									if example_sentence_split[w].isupper():
										lc_indicies += [w]

									elif len(''.join(c for c in example_sentence_split[w] if c.isupper())) > 1:
										lc_indicies += [w] #TODO: see if this works or not in general as a rule of thumb


									else:

										pass #no uppercase included

								# print(lc_indicies)


								##retrieve just the cue out of the sentence based on upper case:
								# final_upper_case_lc = ''
								if len(lc_indicies) > 1:
									upper_case_lc = ''.join(c for c in example_sentence_split[lc_indicies[0]] if c.isalpha() and c.isupper())

									# print(upper_case_lc)
									# print('upper case lc: ',example_sentence_split[lc_indicies[0]])


									for i in range(1, len(lc_indicies)):
										current_i = ''.join(c for c in example_sentence_split[lc_indicies[i]] if c.isalpha() and c.isupper())
										# print(current_i)
										# print(lc_indicies)

										##LOWERCASE IN THE WORD - DEFAULT TO BE "..." AND WILL BE CHANGED LATER TO SEE
										# if len([c for c in example_sentence_split[lc_indicies[i]] if c.islower()]) > 0:

										if lc_indicies[i] == lc_indicies[i-1] + 1 and len([c for c in example_sentence_split[lc_indicies[i-1]] if c.islower()]) == 0:   #consecutive
											# print('GOT HERE!')

											upper_case_lc += '_%s' %(current_i)

											# print(upper_case_lc)
										else:
											upper_case_lc += '...%s' %(current_i)
											# print('GOT HERE!')
											# print(upper_case_lc)
									# final_upper_case_lc = upper_case_lc
								else:
									# print(example_sentence_split[lc_indicies[0]])




									#issue is: NOn-EXISTing -> NO_EXIST is the goal
									# print(example_sentence_split)
									# print(example_sentence_split[lc_indicies[0]])
									if len(example_sentence_split[lc_indicies[0]].split('-')) > 1:
										upper_case_lc = ''
										for e in example_sentence_split[lc_indicies[0]].split('-'):
											if not e.islower(): ##get rid of the lower case ones: "cross-VALIDATION"
												upper_case_lc += '...%s' %''.join(c for c in e if c.isalpha() and c.isupper())

										# print(example_sentence_split[lc_indicies[0]].split('-'))
										upper_case_lc = upper_case_lc[3:]
										# print('final upper case lc: ', final_upper_case_lc)

									else:
										upper_case_lc = ''.join(c for c in example_sentence_split[lc_indicies[0]] if c.isalpha() and c.isupper())
										# print('upper case lc: ', upper_case_lc)
										# final_upper_case_lc = upper_case_lc

								# print(upper_case_lc)

								# upper_case_lc = upper_case_lc
								# 	print('upper case lc: ',example_sentence_split[lc_indicies[0]])

								##positive examples
								if '<' in example_sentence and '>' in example_sentence:
									# print('positive example')
									sentence_type = 1


								##negative examples
								else:
									sentence_type = 2



								##CONNECT THE LCs TOGETHER TO COMPLETE THE DICTIONARY LEXICAL_CUES_TO_ADD


								# if 'RCT' in upper_case_lc:
								# 	print(upper_case_lc)

								if lexical_cues_to_add.get((upper_case_lc.lower(), filename.replace('_examples.txt','').upper())):
									# print('GOT HERE')
									if 'LIMITED_DATA' == upper_case_lc:
										lexical_cues_to_add[
											(upper_case_lc.lower().replace('_', '...'), filename.replace('_examples.txt', '').upper())][
											sentence_type] += ['%s\n\n%s' % (example_sentence, example_explanation)]
									elif 'PREVIOUS_STUDIES' == upper_case_lc:
										lexical_cues_to_add[
											(upper_case_lc.lower().replace('_', '...'),
											 filename.replace('_examples.txt', '').upper())][
											sentence_type] += ['%s\n\n%s' % (example_sentence, example_explanation)]
									else:

										lexical_cues_to_add[(upper_case_lc.lower(), filename.replace('_examples.txt', '').upper())][sentence_type] += ['%s\n\n%s' %(example_sentence, example_explanation)]
									# print(upper_case_lc.lower(), filename.replace('.txt', '').upper(), example_sentence, example_explanation)


								##multiple lexical cues in one sentence that should end up in both - walking through the split up of "..."
								# elif len(upper_case_lc.split('...')) > 1:
								# 	for u in upper_case_lc.split('...'):
								# 		if lexical_cues_to_add.get((u.lower(), filename.replace('.txt', '').upper())):
								# 			lexical_cues_to_add[
								# 				(u.lower(), filename.replace('.txt', '').upper())][
								# 				sentence_type] += ['%s\n\n%s' % (example_sentence, example_explanation)]



								elif len(upper_case_lc.split('_')) > 1 and lexical_cues_to_add.get(
											(upper_case_lc.replace('_','...').lower(), filename.replace('_examples.txt', '').upper())):
									# if lexical_cues_to_add.get(
									# 		(upper_case_lc.replace('_','...').lower(), filename.replace('_examples.txt', '').upper())):
									# print('GOT HERE')


									lexical_cues_to_add[
										(upper_case_lc.replace('_','...').lower(), filename.replace('_examples.txt', '').upper())][
										sentence_type] += ['%s\n\n%s' % (example_sentence, example_explanation)]

								elif len(upper_case_lc.split('...')) > 1 and lexical_cues_to_add.get(
										(upper_case_lc.replace('...', '_').lower(),
										 filename.replace('_examples.txt', '').upper())):

									lexical_cues_to_add[
										(upper_case_lc.replace('...', '_').lower(),
										 filename.replace('_examples.txt', '').upper())][
										sentence_type] += ['%s\n\n%s' % (example_sentence, example_explanation)]


								elif 'LACK_OF_RIGOR' in upper_case_lc:
									lexical_cues_to_add[
										('LACK_OF_RIGOR'.lower(),
										 filename.replace('_examples.txt', '').upper())][
										sentence_type] += ['%s\n\n%s' % (example_sentence, example_explanation)]


								#MOVED FROM NON_URGENT_RECOMMENDATION TO OTHER CATEGORIES - NEED TO RESET IT
								elif lexical_cues_to_add.get((upper_case_lc.lower(), 'NON_URGENT_RECOMMENDATION')):
									lexical_cues_to_add[(upper_case_lc.lower(), filename.replace('_examples.txt', '').upper())] =  [lexical_cues_to_add[(upper_case_lc.lower(), 'NON_URGENT_RECOMMENDATION')][0],[],[]]

									# print('GOT HERE!!')
									# print(upper_case_lc, filename)

									lexical_cues_to_add[(upper_case_lc.lower(), filename.replace('_examples.txt', '').upper())][sentence_type] += ['%s\n\n%s' % (example_sentence, example_explanation)]


								##SPECIFIC ONES THAT ARE DIFFICULT IN A DICTIONARY
								elif tough_lcs.get(upper_case_lc):
									lexical_cues_to_add[
										(tough_lcs[upper_case_lc].lower(),
										 filename.replace('_examples.txt', '').upper())][
										sentence_type] += ['%s\n\n%s' % (example_sentence, example_explanation)]





								else:
									missing_cue_file_temp.write('%s\t%s\n' %(example_sentence, example_explanation))
									# print('NOT HERE YET!', upper_case_lc) #TODO: FIGURE OUT HOW TO ADD THESE IN EVEN IF NOT A MATCH YET

									# print(example_sentence, example_explanation)
									missing_count +=1
									pass


						missing_cue_file_temp.close()
					print('NUMBER OF LEXICAL CUES MISSING: ', missing_count) #TODO: GOAL IS TO GET THIS TO 0

	return lexical_cues_to_add


def lexical_cue_ontology_insertion(lexical_cues_to_add, ontology_file_path, guideline_example_path, ignorance_types, all_linguistic_cues_full_path):



	##ADD THE LEXICAL CUES TO THE ONTOLOGY FILE
	parser = etree.XMLParser(ns_clean=True, attribute_defaults=True, dtd_validation=True, load_dtd=True, remove_blank_text=True, recover=True)
	ontology_of_ignorance_tree = etree.parse(ontology_file_path)
	doc_info = ontology_of_ignorance_tree.docinfo
	
	root = ontology_of_ignorance_tree.getroot()
	print('ROOT', root.tag)



	####NEED TO CHECK IF THE NODES ALREADY EXISTS
	current_declaration_list = []
	for declaration in root.iter('{http://www.w3.org/2002/07/owl#}Declaration'):
		if '#' in declaration[0].attrib['IRI']:
			current_declaration_list += [declaration[0].attrib['IRI'].replace('#','').lower()] ##ALL LOWERCASE
	# print(current_declaration_list)

	##REMOVE THE EXCLUDED LC'S FILE FOR THIS IGNORANCE TYPE
	for ignorance_type in ignorance_types:
		try:
			os.remove('%s%s_excluded_LCs.txt' %(guideline_example_path,ignorance_type))
		except:
			print("EXCLUDED LC's FILE DOES NOT EXIST YET!")




	##LEXICAL_CUES_TO_ADD: (new_lc, original_it) -> [[synonyms '{}'], [positive examples], [negative examples]]
	##count of how many cues:
	final_cue_count = 0

	##FILE OUTPUT OF ALL CUES WITH IGNORANCE TYPE PUT INTO THE ONTOLOGY: LEXICAL_CUE, SYNONYMS, IGNORANCE_TYPE
	lc_full_output = open('%s' %all_linguistic_cues_full_path.replace('ALL_LINGUISTIC_CUES_FULL.txt', 'ALL_ONTOLOGY_INSERTED_LCS.txt'), 'w+')
	lc_full_output.write('%s\t%s\t%s\n' %('LEXICAL_CUE','SYNONYM (ORIGINAL REGEX)', 'IGNORANCE_TYPE'))

	for (lc, it) in sorted(lexical_cues_to_add.keys()): #lc = lowercase, it = uppercase
		# if lc == "don't_know":
		# 	print(lexical_cues_to_add[(lc,it)])
		# print(lexical_cues_to_add[(lc,it)])


		##WE NEED EVERYTHING TO BE ADDED!!
		if lc in current_declaration_list:
			print('LC ALREADY IN DECLARATION LIST!', lc)
			head_lc = '0_' + lc ##PADDING THE SAME TERMS WITH A 0 BUT DOES NOT HAPPEN IN THE OUTPUT FILE

		else:
			head_lc = None


		##NEED TO BE POSITIVE EXAMPLES!
		if len(lexical_cues_to_add[(lc,it)][1]) > 0:
			final_cue_count += 1

			##ADD THE INSERTED LC INTO THE OUTPUT FILE
			lc_full_output.write('%s\t%s\t%s\n' %(lc.lower(), lexical_cues_to_add[(lc,it)][0][0], it))



			# print('LC,IT: ', lc, it)
			##Declaration
			d = etree.SubElement(root, "Declaration")
			c = etree.SubElement(d, "Class")
			if head_lc:
				c.set('IRI', "#%s" % head_lc)
			else:
				c.set('IRI', "#%s" % lc)
			# print etree.tostring(root, pretty_print=True)



			##SubclassOf
			s = etree.SubElement(root, "SubClassOf")
			c1 = etree.SubElement(s, "Class")
			if head_lc:
				c1.set('IRI', "#%s" % head_lc)
			else:
				c1.set('IRI', "#%s" % lc)
			c2 = etree.SubElement(s, "Class")
			c2.set('IRI', "#%s" % it.lower())

			##Annotation Assertions

			##epistemicCategory
			"""<AnnotationAssertion>
        <AnnotationProperty IRI="#epistemicCategory"/>
        <IRI>#0_unexpected_observation</IRI>
        <Literal datatypeIRI="http://www.w3.org/2001/XMLSchema#string">anomaly_curious_finding</Literal>
    </AnnotationAssertion>
			"""

			e = etree.SubElement(root, "AnnotationAssertion")
			e0 = etree.SubElement(e, "AnnotationProperty")
			e0.set("IRI", "#%s" %"epistemicCategory")
			e1 = etree.SubElement(e, "IRI")
			if head_lc:
				e1.text = '#%s' %head_lc
			else:
				e1.text = '#%s' %lc

			e2 = etree.SubElement(e, "Literal")
			e2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
			e2.text = '%s' %it.lower()


			##hasExactSynonym
			h = etree.SubElement(root, "AnnotationAssertion")
			h0 = etree.SubElement(h, "AnnotationProperty")
			h0.set('IRI', "#hasExactSynonym")
			h1 = etree.SubElement(h, "IRI")
			if head_lc:
				h1.text = '#%s' % head_lc.lower()
			else:
				h1.text = '#%s' % lc.lower()
			h2 = etree.SubElement(h, "Literal")
			h2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
			h2.text = '%s' % lc.upper().replace('_', ' ').replace('...',' ')

			##if the cue is disjoint we want the original there - #CHANGED!!!
			if '{' in lexical_cues_to_add[(lc,it)][0][0] or "'" in lexical_cues_to_add[(lc,it)][0][0]:
				e = etree.SubElement(root, "AnnotationAssertion")
				e0 = etree.SubElement(e, "AnnotationProperty")
				e0.set('IRI', "#hasExactSynonym")
				e1 = etree.SubElement(e, "IRI")
				e1.text = '#%s' % lc.lower()
				e2 = etree.SubElement(e, "Literal")
				e2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
				e2.text = '%s' % lexical_cues_to_add[(lc,it)][0][0].upper().replace('_', ' ')


			##positiveExample
			for pe in lexical_cues_to_add[(lc,it)][1]:
				p = etree.SubElement(root, "AnnotationAssertion")
				p0 = etree.SubElement(p, "AnnotationProperty")
				p0.set('IRI', "#positiveExample")
				p1 = etree.SubElement(p, "IRI")
				if head_lc:
					p1.text = '#%s' % head_lc.lower()
				else:
					p1.text = '#%s' % lc.lower()
				p2 = etree.SubElement(p, "Literal")
				p2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
				p2.text = '%s' %pe

			##negativeExample
			for ne in lexical_cues_to_add[(lc,it)][2]:
				n = etree.SubElement(root, "AnnotationAssertion")
				n0 = etree.SubElement(n, "AnnotationProperty")
				n0.set('IRI', "#negativeExample")
				n1 = etree.SubElement(n, "IRI")
				if head_lc:
					n1.text = '#%s' % head_lc.lower()
				else:
					n1.text = '#%s' % lc.lower()
				n2 = etree.SubElement(n, "Literal")
				n2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
				n2.text = '%s' %ne


		##NO POSITIVE EXAMPLES:
		elif len(lexical_cues_to_add[(lc,it)][2]) > 0:
			print('NO POSITIVE EXAMPLES BUT ONLY NEGATIVES', lc, it)
			print(lexical_cues_to_add[(lc,it)])
			raise Exception('NO POSITIVE EXAMPLES BUT ONLY NEGATIVE EXAMPLES - CHECK WORD DOCUMENT SENTENCES!!')



		##the lexical cue is not in our annotation guidelines in the end
		else:
			with open('%s%s_excluded_LCs.txt' %(guideline_example_path, it), 'a+') as excluded_lcs:
				excluded_lcs.write('%s\t%s\n' %(lc.lower(), it))

	lc_full_output.close()
	print('PROGRESS: ALL_ONTOLOGY_INSERTED_LCS.txt done!!')


	##WRITE OUT THE NEW OWL FILE TO ADD TO THE ANNOTATION ONTOLOGY FILE

	updated_ontology_file = open('%s' %ontology_file_path.replace('.owl','_%s.xml' %'updated'), "w")


	updated_ontology_of_ignorance_tree = minidom.parseString(etree.tostring(root)).toprettyxml(indent="   ")
	# updated_ontology_of_ignorance_tree = etree.tostring(root)
	updated_ontology_file.write(updated_ontology_of_ignorance_tree)

	updated_ontology_file.close()

	##FIX THE SPACING ISSUE WHERE THERE ARE 2 BLANK LINES IN BETWEEN ALL THE OLD LINES
	with open('%s' %ontology_file_path.replace('.owl','_%s.xml' %'updated'), "r") as updated_ontology_file:
		lines = [line for line in updated_ontology_file if line.strip() is not ""] #STRIP ALL THE EMPTY LINES AWAY

	with open('%s' %ontology_file_path.replace('.owl','_%s.xml' %'updated'), "w") as updated_ontology_file:
		updated_ontology_file.writelines(lines) #OUTPUT ALL THE LINES WITH NO BLANK LINES



	print('FINAL CUE COUNT: ', final_cue_count)


if __name__=='__main__':
	all_linguistic_cues_full_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/Pre_natal_nutrition/Prenatal_Nutrition_Python_Scripts/ALL_LINGUISTIC_CUES_FULL.txt'

	##NEW IGNORANCE CATEGORIES DICTIONARY
	it_dict = {'POSSIBLE_UNDERSTANDING': 'INCOMPLETE_EVIDENCE', 'CURIOUS_FINDING': 'ANOMALY_CURIOUS_FINDING',
			   'UNEXPECTED_OBSERVATION': 'ANOMALY_CURIOUS_FINDING', 'PROBLEMS_COMPLICATIONS': 'PROBLEM_COMPLICATION',
			   'QUESTIONS_ANSWERED_BY_THIS_WORK': 'QUESTION_ANSWERED_BY_THIS_WORK'}

	update_full_linguistic_cues(all_linguistic_cues_full_path, it_dict)
	print('PROGRESS: finished updating lexical cues to new ignorance types, output: ALL_LINGUISTIC_CUES_FULL_UPDATED.txt')

	##LOOP OVER ALL IGNORANCE TYPES ONE AT A TIME
	# ignorance_type = 'ALTERNATIVE_OPTIONS'
	# ignorance_type = 'FULL_UNKNOWN'
	# ignorance_type = 'EXPLICIT_QUESTION'


	##NON_URGENT_RECOMMENDATION = FUTURE WORK
	# ignorance_types_full = ['FULL_UNKNOWN', 'EXPLICIT_QUESTION', 'ALTERNATIVE_OPTIONS', 'INCOMPLETE_EVIDENCE', 'POSSIBLE_UNDERSTANDING', 'PROBABLE_UNDERSTANDING', 'SUPERFICIAL_RELATIONSHIP', 'FUTURE_WORK', 'NON_URGENT_RECOMMENDATION', 'FUTURE_PREDICTION', 'URGENT_CALL_TO_ACTION', 'CURIOUS_FINDING', 'UNEXPECTED_OBSERVATION', 'DIFFICULT_TASK', 'PROBLEMS_COMPLICATIONS', 'CONTROVERSY', 'QUESTIONS_ANSWERED_BY_THIS_WORK']

	##as of 9/10/19 - non_urgent_recommendation stays because it is moved into other categories
	ignorance_types = ['FULL_UNKNOWN', 'EXPLICIT_QUESTION', 'ALTERNATIVE_OPTIONS', 'INCOMPLETE_EVIDENCE',
						'PROBABLE_UNDERSTANDING', 'SUPERFICIAL_RELATIONSHIP',
						'FUTURE_WORK', 'NON_URGENT_RECOMMENDATION', 'FUTURE_PREDICTION', 'URGENT_CALL_TO_ACTION',
						'ANOMALY_CURIOUS_FINDING', 'DIFFICULT_TASK', 'PROBLEM_COMPLICATION',
						'CONTROVERSY', 'QUESTION_ANSWERED_BY_THIS_WORK']

	ontology_file_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/Pre_natal_nutrition/Ontologies/Ontology_Of_Ignorance.owl'

	guideline_example_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/Pre_natal_nutrition/Prenatal_Nutrition_Python_Scripts/automatic_ontology_insertion/annotation_guidelines_examples/'

	lexical_cues_to_add = retrieve_guideline_examples(all_linguistic_cues_full_path.replace('_FULL.txt','_FULL_UPDATED.txt'), guideline_example_path, ignorance_types, it_dict)

    #
	lexical_cue_ontology_insertion(lexical_cues_to_add, ontology_file_path, guideline_example_path, ignorance_types, all_linguistic_cues_full_path)

