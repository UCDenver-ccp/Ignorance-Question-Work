import os
import re
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
from datetime import date


def new_lexical_cues(gold_standard_annotations_path, articles, ignorance_types, IAA_output_path):
    ##read in the ontology file from the gold_standard annotations

    new_lexical_cues = [] #lexical cue, synonym (regex), ignorance type

    for root, directories, filenames in os.walk(gold_standard_annotations_path):
        for filename in sorted(filenames):
            if filename.split('.nxml.gz.xml')[0] in articles:
                print('CURRENT ARTICLE:', filename)

                parser = etree.XMLParser(ns_clean=True, attribute_defaults=True, dtd_validation=True, load_dtd=True,
                                         remove_blank_text=True, recover=True)
                annotations_tree = etree.parse(gold_standard_annotations_path+filename)
                doc_info = annotations_tree.docinfo

                root = annotations_tree.getroot()
                # print('ROOT', root.tag)


                ##grab the annotations
                for annotation in root.iter('annotation'):
                    annot_id = annotation.attrib['id'] #save the id so you can find it later
                    child_tag = False
                    span_starts = []
                    span_ends = []
                    current_lc = []
                    for child in annotation:
                        if child.tag == 'class':
                            if child.attrib['id'].upper() in ignorance_types:
                                current_it = child.attrib['id'].upper()
                            else:
                                break
                        elif child.tag == 'span':
                            child_tag = True
                            current_lc += [child.text.lower().rstrip()]
                            span_ends += [int(child.attrib['end'])]
                            span_starts += [int(child.attrib['start'])]

                    ##a good annotation with spans and everything
                    if child_tag:

                        ##discontinuous lexical cue
                        if len(span_ends) > 1:
                            regex = ''
                            new_lc = ''
                            for i in range(len(span_ends)-1):
                                discont_length = span_starts[i+1]-span_ends[i]
                                regex += '%s.{0,%s}' %(current_lc[i].replace(' ', '_'), discont_length)
                                new_lc += '%s...' %(current_lc[i].replace(' ', '_'))
                            regex += '%s' %current_lc[-1].replace(' ', '_')
                            new_lc += '%s' %current_lc[-1].replace(' ', '_')

                        ##continous lexical cue
                        else:
                            new_lc = current_lc[0].replace(' ', '_') #get rid of spaces
                            regex = new_lc

                        overall_start = min(span_starts)
                        overall_end = max(span_ends)




                        # print('new_lc', new_lc, regex, current_it)
                        new_lexical_cues += [(new_lc, regex, current_it, annot_id, overall_start, overall_end)] #lexical cue, synonym (regex), ignorance type



                    else:
                        ##empty annotation! TODO: weird!

                        pass


    ##output the new annotations
    with open('%s%s_%s.txt' %(IAA_output_path, 'new_annotations', date.today()), 'w') as new_annot_file:
        new_annot_file.write('%s\t%s\t%s\t%s\t%s\t%s\n' %('LEXICAL_CUE', 'SYNONYM (ORIGINAL REGEX)', 'IGNORANCE_TYPE', 'ANNOTATION_ID','SPAN_START', 'SPAN_END'))
        for nlc in new_lexical_cues:
            new_annot_file.write('%s\t%s\t%s\t%s\t%s\t%s\n' %(nlc[0], nlc[1], nlc[2], nlc[3], nlc[4], nlc[5]))






if __name__=='__main__':
    ##GOLD_STANDARD V1
    # gold_standard_annotations_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Annotations/'

    ##GOLD_STANDARD V2
    gold_standard_annotations_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation_v2/Annotations/'

    ###GOLD STANDARD V1
    # articles = ['PMC1474522', 'PMC3205727']
    # articles = ['PMC1247630', 'PMC2009866', 'PMC2516588', 'PMC3800883', 'PMC5501061']
    # articles = ['PMC4122855', 'PMC4428817', 'PMC4500436', 'PMC4653409', 'PMC4653418', 'PMC4683322']
    # articles = ['PMC4304064', 'PMC3513049', 'PMC3373750', 'PMC3313761', 'PMC2874300', 'PMC1533075', 'PMC6054603','PMC6033232']
    # articles = ['PMC2898025', 'PMC3279448', 'PMC3342123', 'PMC4311629']

    # articles = ['PMC1626394', 'PMC2265032', 'PMC3679768', 'PMC3914197', 'PMC4352710', 'PMC5143410', 'PMC5685050']
    # articles = ['PMC6000839', 'PMC6011374', 'PMC6022422', 'PMC6029118', 'PMC6056931']

    # articles = ['PMC2396486', 'PMC3427250', 'PMC4564405', 'PMC6039335']

    # articles = ['PMC2999828', 'PMC3348565', 'PMC4377896', 'PMC5540678']

    # articles = ['PMC2672462', 'PMC3933411', 'PMC4897523', 'PMC5187359']

    # articles = ['PMC2885310', 'PMC3915248', 'PMC4859539', 'PMC5812027']

    # articles = ['PMC2889879', 'PMC3400371', 'PMC4992225', 'PMC5030620']

    # articles = ['PMC3272870', 'PMC4954778', 'PMC5273824']

    ##TRAINING ARTICLES TO UPDATE
    # articles = ['PMC1247630','PMC1474522','PMC2009866','PMC3800883','PMC4428817','PMC5501061','PMC6000839','PMC6022422']

    ##GOLD STANDARD V2
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
    # articles = ['PMC5226708', 'PMC5732505']  #(PMC4869271 Excluded due to difficulty)
    articles = ['PMC4037583', 'PMC2913107', 'PMC4231606']


    # ignorance_types = ['FULL_UNKNOWN', 'EXPLICIT_QUESTION', 'ALTERNATIVE_OPTIONS', 'INCOMPLETE_EVIDENCE',
    #                    'PROBABLE_UNDERSTANDING', 'SUPERFICIAL_RELATIONSHIP',
    #                    'FUTURE_WORK', 'FUTURE_PREDICTION', 'URGENT_CALL_TO_ACTION',
    #                    'ANOMALY_CURIOUS_FINDING', 'DIFFICULT_TASK', 'PROBLEM_COMPLICATION',
    #                    'CONTROVERSY', 'QUESTION_ANSWERED_BY_THIS_WORK']

    ignorance_types = ['FULL_UNKNOWN', 'EXPLICIT_QUESTION', 'ALTERNATIVE_OPTIONS_CONTROVERSY', 'INCOMPLETE_EVIDENCE',
                       'PROBABLE_UNDERSTANDING', 'SUPERFICIAL_RELATIONSHIP',
                       'FUTURE_WORK', 'FUTURE_PREDICTION', 'IMPORTANT_CONSIDERATION',
                       'ANOMALY_CURIOUS_FINDING', 'DIFFICULT_TASK', 'PROBLEM_COMPLICATION',
                       'QUESTION_ANSWERED_BY_THIS_WORK']

    IAA_output_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Annotation_IAA_11.27.19/new_lexical_cues/'

    new_lexical_cues(gold_standard_annotations_path, articles, ignorance_types, IAA_output_path)
