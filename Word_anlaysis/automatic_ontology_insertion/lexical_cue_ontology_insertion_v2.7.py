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




def lexical_cue_ontology_insertion(all_linguistic_cues_full_path, ignorance_type, ontology_file_path):

	##READ IN ALL THE CUES TO ADD TO THE ONTOLOGY FILE - currently all have '_' instead of spaces

	lexical_cues_to_add = []
	with open(all_linguistic_cues_full_path,'r+') as all_linguistic_cues_full_file:
		for line in all_linguistic_cues_full_file:
			if ignorance_type in line:
				lexical_cues_to_add += [(line.replace('\n','').split('\t')[0], line.replace('\n','').split('\t')[1])]

	# print lexical_cues_to_add 
	print'CURRENT NUMBER OF CUES TO ADD:', len(lexical_cues_to_add)



	##ADD THE LEXICAL CUES TO THE ONTOLOGY FILE
	parser = etree.XMLParser(ns_clean=True, attribute_defaults=True, dtd_validation=True, load_dtd=True, remove_blank_text=True, recover=True)
	ontology_of_ignorance_tree = etree.parse(ontology_file_path)
	doc_info = ontology_of_ignorance_tree.docinfo
	
	root = ontology_of_ignorance_tree.getroot()
	print 'ROOT', root.tag



	####NEED TO CHECK IF THE NODES ALREADY EXISTS
	current_declaration_list = []
	for declaration in root.iter('{http://www.w3.org/2002/07/owl#}Declaration'):
		if '#' in declaration[0].attrib['IRI']:
			current_declaration_list += [declaration[0].attrib['IRI'].replace('#','').lower()] ##ALL LOWERCASE
	# print current_declaration_list


	final_lexical_cues_to_add = []
	for c in lexical_cues_to_add:
		if c[0] in current_declaration_list:
			# print c[0]
			pass ##TODO: FIGURE OUT WHAT TO DO WITH ONES THAT ARE ALREADY HERE: APPEND MORE INFO?
		else:
			final_lexical_cues_to_add += [c]

	print 'FINAL NUMBER OF CUES TO ADD:', len(final_lexical_cues_to_add)

	for f in final_lexical_cues_to_add: #(lexical_cue, IGNORANCE_TYPE)
	# f = final_lexical_cues_to_add[0]
	# print f
		lc = f[0]
		it = f[1]

		##get rid of regex ones like: whether.{0,206}compared, and replace with '...'
		if '{' in lc: #whether.{0,206}compared 
			lc_list = lc.split('.')
			lc = ''
			
			for l in lc_list:
				if '}' in l:
					lc += '...%s' %l.split('}')[-1]
				else:
					lc += '_%s' %l
			lc = lc[1:]
			# print lc
		else:
			lc = lc


		##Declaration
		d = etree.SubElement(root, "Declaration")
		c = etree.SubElement(d, "Class")
		c.set('IRI', "#%s" %lc)
		# print etree.tostring(root, pretty_print=True)



		##SubclassOf
		s = etree.SubElement(root, "SubClassOf")
		c1 = etree.SubElement(s, "Class")
		c1.set('IRI', "#%s" %lc)
		c2 = etree.SubElement(s, "Class")
		c2.set('IRI', "#%s" %it.lower())


		##Annotation Assertions

		##hasExactSynonym
		h = etree.SubElement(root, "AnnotationAssertion")
		h0 = etree.SubElement(h, "AnnotationProperty")
		h0.set('IRI', "#hasExactSynonym")
		h1 = etree.SubElement(h, "IRI")
		h1.text = '#%s' %lc.lower()
		h2 = etree.SubElement(h, "Literal")
		h2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
		h2.text = '%s' %lc.upper().replace('_', ' ')

		##if the cue is disjoint we want the original there
		if '{' in f[0]: 
			e = etree.SubElement(root, "AnnotationAssertion")
			e0 = etree.SubElement(e, "AnnotationProperty")
			e0.set('IRI', "#hasExactSynonym")
			e1 = etree.SubElement(e, "IRI")
			e1.text = '#%s' %lc.lower()
			e2 = etree.SubElement(e, "Literal")
			e2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
			e2.text = '%s' %f[0].upper().replace('_', ' ')

		
		##negativeExample
		n = etree.SubElement(root, "AnnotationAssertion")
		n0 = etree.SubElement(n, "AnnotationProperty")
		n0.set('IRI', "#negativeExample")
		n1 = etree.SubElement(n, "IRI")
		n1.text = '#%s' %lc.lower()
		n2 = etree.SubElement(n, "Literal")
		n2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
		n2.text = '%s' %'negative filler!\n\n\n[negative explanation]'



		##positiveExample
		p = etree.SubElement(root, "AnnotationAssertion")
		p0 = etree.SubElement(p, "AnnotationProperty")
		p0.set('IRI', "#positiveExample")
		p1 = etree.SubElement(p, "IRI")
		p1.text = '#%s' %lc.lower()
		p2 = etree.SubElement(p, "Literal")
		p2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
		p2.text = '%s' %'positive filler!\n\n\n[positive explanation]'

		


	##WRITE OUT THE NEW FILE
	
	updated_ontology_file = open('%s' %ontology_file_path.replace('.owl','_updated.xml'), "w")


	updated_ontology_of_ignorance_tree = minidom.parseString(etree.tostring(root)).toprettyxml(indent="   ")
	# updated_ontology_of_ignorance_tree = etree.tostring(root)
	updated_ontology_file.write(updated_ontology_of_ignorance_tree.encode('utf-8'))

	updated_ontology_file.close()

	##FIX THE SPACING ISSUE WHERE THERE ARE 2 BLANK LINES IN BETWEEN ALL THE OLD LINES
	with open('%s' %ontology_file_path.replace('.owl','_updated.xml'), "r") as updated_ontology_file:
		lines = [line for line in updated_ontology_file if line.strip() is not ""] #STRIP ALL THE EMPTY LINES AWAY

	with open('%s' %ontology_file_path.replace('.owl','_updated.xml'), "w") as updated_ontology_file:
		updated_ontology_file.writelines(lines) #OUTPUT ALL THE LINES WITH NO BLANK LINES






if __name__=='__main__':
	all_linguistic_cues_full_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/Pre_natal_nutrition/Prenatal_Nutrition_Python_Scripts/ALL_LINGUISTIC_CUES_FULL.txt'
	ignorance_type = 'ALTERNATIVE_OPTIONS'
	ontology_file_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/Pre_natal_nutrition/Ontologies/Ontology_Of_Ignorance.owl'



	lexical_cue_ontology_insertion(all_linguistic_cues_full_path, ignorance_type, ontology_file_path)

