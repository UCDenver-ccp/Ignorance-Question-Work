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



def all_excluded_LCs(guideline_example_path,):
    with open('%s' % (guideline_example_path + 'ALL_EXCLUDED_LCS.txt'), 'w+') as outfile:
        for root, directories, filenames in os.walk(guideline_example_path):
            for filename in sorted(filenames):
                if filename.endswith('_excluded_LCs.txt'):
                    print(filename)
                    with open('%s' %(guideline_example_path+filename), 'r') as infile:
                        outfile.write(infile.read())






if __name__=='__main__':
    guideline_example_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/Pre_natal_nutrition/Prenatal_Nutrition_Python_Scripts/automatic_ontology_insertion/annotation_guidelines_examples/'

    all_excluded_LCs(guideline_example_path)