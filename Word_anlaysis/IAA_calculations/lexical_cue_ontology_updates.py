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
from nltk.tokenize.punkt import PunktSentenceTokenizer
from datetime import date


def add_ontology_terms(root, lexical_cue, epistemic_category, regex, positive_example, negative_example):

    ##Declaration
    d = etree.SubElement(root, "Declaration")
    c = etree.SubElement(d, "Class")
    c.set('IRI', "#%s" % lexical_cue)
    # if head_lc:
    #     c.set('IRI', "#%s" % head_lc)
    # else:
    #     c.set('IRI', "#%s" % lc)
    # print etree.tostring(root, pretty_print=True)

    ##SubclassOf
    s = etree.SubElement(root, "SubClassOf")
    c1 = etree.SubElement(s, "Class")
    c1.set('IRI', "#%s" % lexical_cue)
    # if head_lc:
    #     c1.set('IRI', "#%s" % head_lc)
    # else:
    #     c1.set('IRI', "#%s" % lc)
    c2 = etree.SubElement(s, "Class")
    c2.set('IRI', "#%s" % epistemic_category.lower())

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
    e0.set("IRI", "#%s" % "epistemicCategory")
    e1 = etree.SubElement(e, "IRI")
    e1.text = '#%s' % lexical_cue
    # if head_lc:
    #     e1.text = '#%s' % head_lc
    # else:
    #     e1.text = '#%s' % lc

    e2 = etree.SubElement(e, "Literal")
    e2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
    e2.text = '%s' % epistemic_category.lower()

    ##hasExactSynonym
    h = etree.SubElement(root, "AnnotationAssertion")
    h0 = etree.SubElement(h, "AnnotationProperty")
    h0.set('IRI', "#hasExactSynonym")
    h1 = etree.SubElement(h, "IRI")
    h1.text = '#%s' % lexical_cue.lower()
    # if head_lc:
    #     h1.text = '#%s' % head_lc.lower()
    # else:
    #     h1.text = '#%s' % lc.lower()
    h2 = etree.SubElement(h, "Literal")
    h2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
    h2.text = '%s' % lexical_cue.upper().replace('0_','').replace('_', ' ').replace('...', ' ')

    ##if the cue is disjoint we want the original there - #CHANGED!!!
    if regex:  # TODO
        e = etree.SubElement(root, "AnnotationAssertion")
        e0 = etree.SubElement(e, "AnnotationProperty")
        e0.set('IRI', "#hasExactSynonym")
        e1 = etree.SubElement(e, "IRI")
        e1.text = '#%s' % lexical_cue.lower()
        e2 = etree.SubElement(e, "Literal")
        e2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
        e2.text = '%s' % regex.upper().replace('_', ' ')

    ##positiveExample
    p = etree.SubElement(root, "AnnotationAssertion")
    p0 = etree.SubElement(p, "AnnotationProperty")
    p0.set('IRI', "#positiveExample")
    p1 = etree.SubElement(p, "IRI")
    p1.text = '#%s' % lexical_cue.lower()
    # if head_lc:
    #     p1.text = '#%s' % head_lc.lower()
    # else:
    #     p1.text = '#%s' % lc.lower()
    p2 = etree.SubElement(p, "Literal")
    p2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
    p2.text = '%s' % positive_example

    ##negativeExample
    if negative_example:
        n = etree.SubElement(root, "AnnotationAssertion")
        n0 = etree.SubElement(n, "AnnotationProperty")
        n0.set('IRI', "#negativeExample")
        n1 = etree.SubElement(n, "IRI")
        n1.text = '#%s' % lexical_cue.lower()

        n2 = etree.SubElement(n, "Literal")
        n2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
        n2.text = '%s' % negative_example

    return root

def remove_terms_from_ontology(root, terms_to_remove):

    ##remove declaration and subclassof
    classes_to_delete = ['Declaration', 'SubClassOf']
    for cd in classes_to_delete:
        term_deleted = False
        terms_deleted = 0
        for elem in root.iter('{http://www.w3.org/2002/07/owl#}%s' %cd):
            if term_deleted:
                break
            else:
                for child in elem:
                    if child.attrib['IRI'].replace('#', '').lower() in terms_to_remove:
                        root.remove(elem)
                        terms_deleted += 1
                        if term_deleted == len(terms_to_remove):
                            term_deleted = True
                        break
                    else:
                        continue

    ##remove the annotationassertions like epistemicCategory, hasExactSynonym, negativeExample, positiveExample
    for annotationassertion in root.iter('{http://www.w3.org/2002/07/owl#}AnnotationAssertion'):
        for child in annotationassertion:
            if str(child.text).replace('#','').lower() in terms_to_remove and str(child.tag).endswith('IRI'):
                # print(child.text)
                # print(child.tag)
                root.remove(annotationassertion)

    return root

def change_ontology_term_name(root, original_term, new_term, regex, positive_example, negative_example):
    #terms are always lowercase


    classes = ['Declaration', 'SubClassOf']
    #declaration and Subclassof
    for c in classes:
        for elem in root.iter('{http://www.w3.org/2002/07/owl#}%s' % c):
            for child in elem:
                if original_term in child.attrib['IRI'].lower() and new_term not in child.attrib['IRI'].lower():
                    #keep the lexical cue of the old cue
                    if '0_' in child.attrib['IRI'].lower():
                        # print('HERE ALSO!')
                        update_old_cue = child.attrib['IRI'].lower().replace('0_','')
                        child.set('IRI', update_old_cue)
                        if c != 'SubClassOf':
                            break #do not change anymore
                        else:
                            pass
                    #update everything else to the new name
                    else:
                        full_new_term = str(child.attrib['IRI']).replace(original_term, new_term)
                        child.set('IRI', full_new_term)


    #AnnotationAssertions
    for annotationassertion in root.iter('{http://www.w3.org/2002/07/owl#}AnnotationAssertion'):
        for child in annotationassertion:
            if str(child.tag).endswith('AnnotationProperty'):
                if child.attrib['IRI'].endswith('epistemicCategory'):
                    change_epistemic_category = True
                else:
                    change_epistemic_category = False

            if original_term in str(child.text).lower() and (str(child.tag).endswith('IRI') or str(child.tag).endswith('Literal')) and new_term not in str(child.text).lower():
                #keep the lexical cue of the old cue
                if '0_' in str(child.text).lower():
                    # print('GOT HERE!')
                    update_old_cue = str(child.text).replace('0_','') #update the old cue to just be a lexical cue getting rid of the 0_
                    child.text = update_old_cue
                    if change_epistemic_category:
                        pass
                    else:
                        break #do not change anymore
                #update everything else to the new name
                else:
                    full_new_term = str(child.text).replace(original_term, new_term)
                    child.text = full_new_term



    lexical_cue = '0_%s' %new_term

    ##Add a lexical cue for the new name if we have a positive example
    if positive_example:
        root = add_ontology_terms(root, lexical_cue, new_term, regex, positive_example, negative_example)
    else:
        pass


    return root



def change_ontology_terms(root, terms_to_change):
    for terms in terms_to_change.keys():
        # change the name of a ontology category
        if type(terms) == str:
            new_term, regex, positive_example, negative_example = terms_to_change[terms]
            root = change_ontology_term_name(root, terms, new_term, regex, positive_example, negative_example)

        # combine 2 categories
        else:
            # print(terms)
            # print(terms_to_change[terms])
            broader_category_to_delete = terms[1]
            all_terms = terms[0]
            new_term, regex, positive_example, negative_example = terms_to_change[terms]
            for term in all_terms:
                root = change_ontology_term_name(root, term, new_term, regex, positive_example, negative_example)

            ##remove the duplicates of the declarations from the combination of things and replacing all not just one!
            removed_duplicates = False
            for i in range(len(terms)-1):
                for elem in root.iter('{http://www.w3.org/2002/07/owl#}Declaration'):
                    for child in elem:
                        if child.attrib['IRI'].replace('#', '').lower() == new_term:
                            root.remove(elem)
                            removed_duplicates = True
                        else:
                            continue
                    if removed_duplicates:
                        break

            ##remove the extra sublcass of the broader categories
            removed_duplicates = False
            all_removed = False
            for i in range(len(terms)-1):
                for elem in root.iter('{http://www.w3.org/2002/07/owl#}SubClassOf'):
                    if len(list(elem)) == 2:
                        for child in elem:
                            if child.attrib['IRI'].replace('#', '').lower() == new_term:
                                removed_duplicates = True
                            elif removed_duplicates and child.attrib['IRI'].replace('#','') == broader_category_to_delete:
                                root.remove(elem)
                                all_removed = True
                            else:
                                removed_duplicates = False
                        if all_removed:
                            break

    return root




def lexical_cue_ontology_insertion(new_lcs_path, articles_path, articles, ignorance_types_update_dict, ontology_file_path):



    ##ADD THE LEXICAL CUES TO THE ONTOLOGY FILE
    parser = etree.XMLParser(ns_clean=True, attribute_defaults=True, dtd_validation=True, load_dtd=True,
                             remove_blank_text=True, recover=True)
    ontology_of_ignorance_tree = etree.parse(ontology_file_path)
    doc_info = ontology_of_ignorance_tree.docinfo

    root = ontology_of_ignorance_tree.getroot()
    print('ROOT', root.tag)

    ##UPDATE THE ONTOLOGY WITH ALL THE CHANGES DISCUSSED IN ADJUDICATION PROCESS
    print('PROGRESS: UPDATING ONTOLOGY WITH CURRENT CHANGES!')
    # 3/20/20 UPDATE
    # remove terms
    terms_to_remove = ['is', 'than']  # 3/20/20
    root = remove_terms_from_ontology(root, terms_to_remove)

    # change or combine ontology terms:
    # terms to change dict: old ontology term -> (new_term, regex, positive_example, negative_example)
    terms_to_change = {'urgent_call_to_action': ('important_consideration', None,
                                                 '“<For maintenance therapy after first-line treatment, the choice of approach should be individualized, with cost being an IMPORTANT CONSIDERATION within Asia>.\n[urgent call to consider the cost within Asia for maintenance therapy after first_line_treatement]”',
                                                 '“During the last decade, we noticed an IMPORTANT CONSIDERATION and a huge number of publications related to the medical and surgical treatment of this disease.\n[a statement about what researchers noticed, not a statement that lays out a specific call to action that needs immediate attention]”'),
                       (('alternative_options', 'controversy'),'Levels_Of_Evidence'): ('alternative_options_controversy', None, None, None)}
    # terms_to_combine = [('alternative_options','controversy'), 'alternative_options_controversy']
    # root = change_ontology_terms(root, terms_to_change) #3/20/20 change



    ####NEED TO CHECK IF THE NODES ALREADY EXISTS
    ##current_declaration_dict - loop through the already existing lexical cues and categories
    current_declaration_dict = {}
    for subclassof in root.iter('{http://www.w3.org/2002/07/owl#}SubClassOf'):
        for i, child in enumerate(subclassof):
            if i == 0:
                lc = child.attrib['IRI'].replace('#', '')
            elif i == 1:
                it = child.attrib['IRI'].replace('#', '')
        current_declaration_dict[lc] = it



    ##LEXICAL_CUES_TO_ADD: new_lcs_path read in
    lc_info_to_add = [] #[[lc, regex, it, annotation_id, span_start, span_end]]
    with open(new_lcs_path, 'r') as new_lcs_file:
        next(new_lcs_file)
        for line in new_lcs_file:
            # print(line.replace('\n', '').split('\t'))
            lc_info_to_add += [line.replace('\n', '').split('\t')]

            new_lc = line.split('\t')[0]
            regex = line.split('\t')[1]
            ignorance_type = line.split('\t')[2]
            ##update the ignorance type to the current ones!
            if ignorance_type in ignorance_types_update_dict.keys():
                ignorance_type = ignorance_types_update_dict[ignorance_type]
            else:
                pass

            annot_id = line.split('\t')[3] #pmc.nxml.gz-
            span_start = int(line.split('\t')[4])
            span_end = int(line.split('\t')[5])

            ##gather sentence from article -
            with open('%s%s.txt' %(articles_path, annot_id.split('-')[0]), 'r') as article_file:
                article_text = article_file.read()
                for start, end in PunktSentenceTokenizer().span_tokenize(article_text):
                    if end >= span_end:
                        sentence_start, sentence_end = start, end
                        break
                    else:
                        pass
                positive_sentence = article_text[sentence_start:sentence_end].lower()

                ##update the sentence to only be one line/sentence if multiple lines there
                if len(positive_sentence.split('\n')) > 1:
                    for s in positive_sentence.split('\n'):
                        for n in new_lc.replace('_', ' ').split('...'):
                            if n not in s:
                                break
                            else:
                                positive_sentence = s
                else:
                    pass


                ##capitalize the lexical cue in the sentence:
                for n in new_lc.replace('_', ' ').split('...'):
                    n_index = positive_sentence.index(n)
                    positive_sentence = positive_sentence[:n_index] + positive_sentence[n_index:n_index+len(n)].upper() + positive_sentence[n_index+len(n):]



                # print('new_lc', new_lc)
                # print([final_positive_sentence])



                ##insert into ontology
                ##an existing concept that we are adding exceptions to or adding information to
                if current_declaration_dict.get(new_lc.lower()):
                    ##updated discontinuity parameters but same ignorance type
                    if current_declaration_dict[new_lc] == ignorance_type.lower():
                        ##add an explanation #[a new cue added from the annotation process with a positive example from the article and the scope is the whole sentence automatically]
                        final_positive_sentence = '"<' + positive_sentence + '>"' + ' [another positive example to an updated lexical cue from an article in the annoation process with the scope as the whole sentence]'
                        # print(new_lc, ignorance_type, current_declaration_dict[new_lc])

                        ##update the synonyms to have the correct regex expression - regex
                        for literal in root.iter('{http://www.w3.org/2002/07/owl#}Literal'):
                            # print(literal.text)
                            if '{' in literal.text and set([s.upper() in literal.text for s in new_lc.split('...')]) == {True}:
                                literal.text = regex
                            else:
                                pass

                        ##positiveExample - added in
                        p = etree.SubElement(root, "AnnotationAssertion")
                        p0 = etree.SubElement(p, "AnnotationProperty")
                        p0.set('IRI', "#positiveExample")
                        p1 = etree.SubElement(p, "IRI")
                        p1.text = '#%s' % new_lc.lower()
                        # if head_lc:
                        #     p1.text = '#%s' % head_lc.lower()
                        # else:
                        #     p1.text = '#%s' % lc.lower()
                        p2 = etree.SubElement(p, "Literal")
                        p2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
                        p2.text = '%s' % final_positive_sentence

                    ##same term but different ignorance type = exception!
                    else:
                        ##add an explanation
                        final_positive_sentence = '"<' + positive_sentence + '>"' + ' [a rare exception of the cue to a different epistemic category from the annotation process with an example from the article and the scope is the whole sentence automatically]'
                        ##exceptionEpistemicCategory
                        """<AnnotationAssertion>
                    <AnnotationProperty IRI="#exceptionEpistemicCategory"/>
                    <IRI>#0_unexpected_observation</IRI>
                    <Literal datatypeIRI="http://www.w3.org/2001/XMLSchema#string">anomaly_curious_finding</Literal>
                </AnnotationAssertion>
                        """

                        e = etree.SubElement(root, "AnnotationAssertion")
                        e0 = etree.SubElement(e, "AnnotationProperty")
                        e0.set("IRI", "#%s" % "exceptionEpistemicCategory")
                        e1 = etree.SubElement(e, "IRI")
                        e1.text = '#%s' % new_lc
                        # if head_lc:
                        #     e1.text = '#%s' % head_lc
                        # else:
                        #     e1.text = '#%s' % lc

                        e2 = etree.SubElement(e, "Literal")
                        e2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
                        e2.text = '%s' % ignorance_type.lower()


                        ##exceptionExample

                        p = etree.SubElement(root, "AnnotationAssertion")
                        p0 = etree.SubElement(p, "AnnotationProperty")
                        p0.set('IRI', "#exceptionExample")
                        p1 = etree.SubElement(p, "IRI")
                        p1.text = '#%s' % new_lc.lower()
                        # if head_lc:
                        #     p1.text = '#%s' % head_lc.lower()
                        # else:
                        #     p1.text = '#%s' % lc.lower()
                        p2 = etree.SubElement(p, "Literal")
                        p2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
                        p2.text = '%s' % final_positive_sentence

                ##a fully new concept
                else:
                    ##add an explanation
                    final_positive_sentence = '"<' + positive_sentence + '>"' + ' [a new cue added from the annotation process with a positive example from the article and the scope is the whole sentence automatically]'
                    ##Declaration
                    d = etree.SubElement(root, "Declaration")
                    c = etree.SubElement(d, "Class")
                    c.set('IRI', "#%s" %new_lc)
                    # if head_lc:
                    #     c.set('IRI', "#%s" % head_lc)
                    # else:
                    #     c.set('IRI', "#%s" % lc)
                    # print etree.tostring(root, pretty_print=True)

                    ##SubclassOf
                    s = etree.SubElement(root, "SubClassOf")
                    c1 = etree.SubElement(s, "Class")
                    c1.set('IRI', "#%s" %new_lc)
                    # if head_lc:
                    #     c1.set('IRI', "#%s" % head_lc)
                    # else:
                    #     c1.set('IRI', "#%s" % lc)
                    c2 = etree.SubElement(s, "Class")
                    c2.set('IRI', "#%s" % ignorance_type.lower())

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
                    e0.set("IRI", "#%s" % "epistemicCategory")
                    e1 = etree.SubElement(e, "IRI")
                    e1.text = '#%s' %new_lc
                    # if head_lc:
                    #     e1.text = '#%s' % head_lc
                    # else:
                    #     e1.text = '#%s' % lc

                    e2 = etree.SubElement(e, "Literal")
                    e2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
                    e2.text = '%s' % ignorance_type.lower()

                    ##hasExactSynonym
                    h = etree.SubElement(root, "AnnotationAssertion")
                    h0 = etree.SubElement(h, "AnnotationProperty")
                    h0.set('IRI', "#hasExactSynonym")
                    h1 = etree.SubElement(h, "IRI")
                    h1.text = '#%s' %new_lc.lower()
                    # if head_lc:
                    #     h1.text = '#%s' % head_lc.lower()
                    # else:
                    #     h1.text = '#%s' % lc.lower()
                    h2 = etree.SubElement(h, "Literal")
                    h2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
                    h2.text = '%s' % new_lc.upper().replace('_', ' ').replace('...', ' ')

                    ##if the cue is disjoint we want the original there - #CHANGED!!!
                    if '{' in regex or "'" in regex: #TODO
                        e = etree.SubElement(root, "AnnotationAssertion")
                        e0 = etree.SubElement(e, "AnnotationProperty")
                        e0.set('IRI', "#hasExactSynonym")
                        e1 = etree.SubElement(e, "IRI")
                        e1.text = '#%s' % new_lc.lower()
                        e2 = etree.SubElement(e, "Literal")
                        e2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
                        e2.text = '%s' % regex.upper().replace('_', ' ')

                    ##positiveExample

                    p = etree.SubElement(root, "AnnotationAssertion")
                    p0 = etree.SubElement(p, "AnnotationProperty")
                    p0.set('IRI', "#positiveExample")
                    p1 = etree.SubElement(p, "IRI")
                    p1.text = '#%s' %new_lc.lower()
                    # if head_lc:
                    #     p1.text = '#%s' % head_lc.lower()
                    # else:
                    #     p1.text = '#%s' % lc.lower()
                    p2 = etree.SubElement(p, "Literal")
                    p2.set("datatypeIRI", "http://www.w3.org/2001/XMLSchema#string")
                    p2.text = '%s' % final_positive_sentence

    print('PROGRESS: ALL_ONTOLOGY_INSERTED_LCS.txt done!!')


    # ##UPDATE THE ONTOLOGY WITH ALL THE CHANGES DISCUSSED IN ADJUDICATION PROCESS
    # print('PROGRESS: UPDATING ONTOLOGY WITH CURRENT CHANGES!')
    # #3/20/20 UPDATE
    # #remove terms
    # terms_to_remove = ['is', 'than'] #3/20/20
    # root = remove_terms_from_ontology(root, terms_to_remove)
    #
    # #change or combine ontology terms:
    # # terms to change dict: old ontology term -> (new_term, regex, positive_example, negative_example)
    # terms_to_change = {'urgent_call_to_action':('important_consideration', None, '“<For maintenance therapy after first-line treatment, the choice of approach should be individualized, with cost being an IMPORTANT CONSIDERATION within Asia>.\n[urgent call to consider the cost within Asia for maintenance therapy after first_line_treatement]”', '“During the last decade, we noticed an IMPORTANT CONSIDERATION and a huge number of publications related to the medical and surgical treatment of this disease.\n[a statement about what researchers noticed, not a statement that lays out a specific call to action that needs immediate attention]”'),
    #                    ('alternative_options','controversy'): ('alternative_options_controversy', None, None, None)}
    # # terms_to_combine = [('alternative_options','controversy'), 'alternative_options_controversy']
    # root = change_ontology_terms(root, terms_to_change)


    print('PROGRESS: OUTPUTTING NEW ONTOLOGY!')
    ##WRITE OUT THE NEW OWL FILE TO ADD TO THE ANNOTATION ONTOLOGY FILE

    updated_ontology_file = open('%s' % ontology_file_path.replace('.owl', '_%s_%s.xml' %('updated', date.today())), "w")

    updated_ontology_of_ignorance_tree = minidom.parseString(etree.tostring(root)).toprettyxml(indent="   ")
    # updated_ontology_of_ignorance_tree = etree.tostring(root)
    updated_ontology_file.write(updated_ontology_of_ignorance_tree)

    updated_ontology_file.close()

    ##FIX THE SPACING ISSUE WHERE THERE ARE 2 BLANK LINES IN BETWEEN ALL THE OLD LINES
    with open('%s' % ontology_file_path.replace('.owl', '_%s_%s.xml' %('updated', date.today())), "r") as updated_ontology_file:
        lines = [line for line in updated_ontology_file if line.strip() is not ""]  # STRIP ALL THE EMPTY LINES AWAY

    with open('%s' % ontology_file_path.replace('.owl', '_%s_%s.xml' %('updated', date.today())), "w") as updated_ontology_file:
        updated_ontology_file.writelines(lines)  # OUTPUT ALL THE LINES WITH NO BLANK LINES

    # print('FINAL CUE COUNT: ', final_cue_count)


if __name__ == '__main__':
    ##GOLD STANDARD V1
    # gold_standard_articles_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Articles/'

    ##GOLD STANDARD V2
    gold_standard_articles_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation_v2/Articles/'


    ##GOLD STANDARD V1

    # articles = ['PMC1474522', 'PMC3205727']
    # articles = ['PMC1247630', 'PMC2009866', 'PMC2516588', 'PMC3800883', 'PMC5501061']
    # articles = ['PMC4122855', 'PMC4428817', 'PMC4500436', 'PMC4653409', 'PMC4653418', 'PMC4683322']
    # articles = ['PMC4304064', 'PMC3513049', 'PMC3373750', 'PMC3313761', 'PMC2874300', 'PMC1533075', 'PMC6054603',
    #             'PMC6033232']

    # articles = ['PMC2898025', 'PMC3279448', 'PMC3342123', 'PMC4311629']

    # articles = ['PMC1626394', 'PMC2265032', 'PMC3679768', 'PMC3914197', 'PMC4352710', 'PMC5143410', 'PMC5685050']
    # articles = ['PMC6000839', 'PMC6011374', 'PMC6022422', 'PMC6029118', 'PMC6056931']
    # articles = ['PMC2396486', 'PMC3427250', 'PMC4564405', 'PMC6039335']

    # articles = ['PMC2999828', 'PMC3348565', 'PMC4377896', 'PMC5540678']

    # articles = ['PMC2672462', 'PMC3933411', 'PMC4897523', 'PMC5187359']

    # articles = ['PMC2885310', 'PMC3915248', 'PMC4859539', 'PMC5812027']

    # articles = ['PMC2889879', 'PMC3400371', 'PMC4992225', 'PMC5030620']

    # articles = ['PMC3272870', 'PMC4954778', 'PMC5273824']

    ##TRAINING UPDATES
    # articles = ['PMC1247630', 'PMC1474522', 'PMC2009866', 'PMC3800883', 'PMC4428817', 'PMC5501061', 'PMC6000839',
    #             'PMC6022422']

    ##GOLD STANDARD V2 - TODO!
    # articles = ['PMC4715834', 'PMC5546866', 'PMC2727050', 'PMC3075531']
    # articles = ['PMC2722583', 'PMC3424155', 'PMC3470091', 'PMC4275682']
    # articles = ['PMC4973215', 'PMC5539754']
    # articles = ['PMC5658906']
    # articles = ['PMC3271033']
    # articles = ['PMC5405375']
    # articles = ['PMC4380518']
    # articles = ['PMC4488777', 'PMC2722408']
    # articles = ['PMC3828574']
    # articles = ['PMC3659910']
    # articles = ['PMC3169551', 'PMC4327187']
    # articles = ['PMC3710985', 'PMC5439533', 'PMC5524288']
    # articles = ['PMC3789799', 'PMC5240907', 'PMC5340372']
    # articles = ['PMC5226708', 'PMC5732505']  # (PMC4869271 Excluded due to difficulty)
    articles = ['PMC4037583', 'PMC2913107', 'PMC4231606']


    ignorance_types = ['FULL_UNKNOWN', 'EXPLICIT_QUESTION', 'ALTERNATIVE_OPTIONS', 'INCOMPLETE_EVIDENCE',
                       'PROBABLE_UNDERSTANDING', 'SUPERFICIAL_RELATIONSHIP',
                       'FUTURE_WORK', 'FUTURE_PREDICTION', 'URGENT_CALL_TO_ACTION',
                       'ANOMALY_CURIOUS_FINDING', 'DIFFICULT_TASK', 'PROBLEM_COMPLICATION',
                       'CONTROVERSY', 'QUESTION_ANSWERED_BY_THIS_WORK']

    #update 3/20/20
    ignorance_types_update_dict = {'URGENT_CALL_TO_ACTION':'IMPORTANT_CONSIDERATION', 'ALTERNATIVE_OPTIONS':'ALTERNATIVE_OPTIONS_CONTROVERSY', 'CONTROVERSY':'ALTERNATIVE_OPTIONS_CONTROVERSY'}

    new_lcs_12_20_19_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2019-12-20.txt'
    new_lcs_1_28_20_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2020-01-28.txt'

    new_lcs_2_11_20_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2020-02-11.txt'
    new_lcs_2_26_20_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2020-02-26.txt'

    new_lcs_3_20_20_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2020-03-20.txt'

    new_lcs_4_21_20_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2020-04-21.txt'

    new_lcs_5_21_20_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2020-05-21.txt'


    #new_annotations_2020-06-04
    new_lcs_6_4_20_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2020-06-04.txt'


    new_lcs_6_18_20_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2020-06-18.txt'

    new_lcs_7_3_20_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2020-07-03.txt'


    new_lcs_7_29_20_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2020-07-29.txt'

    new_lcs_8_13_20_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2020-08-13.txt'


    new_lcs_8_25_20_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2020-08-25.txt'



    ##TRAINING UPDATES!
    new_lcs_3_6_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-03-06.txt'

    ##GOLD STANDARD V2 - TODO!!
    new_lcs_3_29_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-03-29.txt'

    new_lcs_4_21_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-04-21.txt'

    new_lcs_5_2_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-05-02.txt'

    new_lcs_5_9_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-05-09.txt'

    new_lcs_5_14_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-05-14.txt'

    new_lcs_5_22_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-05-22.txt'

    new_lcs_5_28_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-05-28.txt'

    new_lcs_6_5_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-06-05.txt'

    new_lcs_6_11_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-06-11.txt'

    new_lcs_6_18_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-06-18.txt'

    new_lcs_7_2_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-07-02.txt'

    new_lcs_7_10_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-07-02.txt'

    new_lcs_7_16_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-07-16.txt'

    new_lcs_7_23_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-07-23.txt'

    new_lcs_7_30_21_file = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/new_annotations_2021-07-30.txt'

    ##ontology output file
    ontology_file_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/1_First_Full_Annotation_Task_9_13_19/Ontologies/Ontology_Of_Ignorance.owl'



    ##TODO: change this for the right date!!!
    lexical_cue_ontology_insertion(new_lcs_7_30_21_file, gold_standard_articles_path, articles, ignorance_types_update_dict, ontology_file_path)