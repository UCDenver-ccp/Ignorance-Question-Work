import requests
import json
import os
import xml
import xml.etree.ElementTree as ET
import gzip


def get_list_of_pmcids(article_path):
    pmc_filename_list = [] #list of all pmc files to grab for section info

    for root, directories, filenames in os.walk(article_path):
        for filename in sorted(filenames):
            if filename.endswith('.nxml.gz.txt') and filename.startswith('PMC'):
                pmc_filename = filename.split('.nxml')[0]
                pmc_filename_list += [pmc_filename]



    return pmc_filename_list



def get_all_BioC_section_files(api_url_base, format, encoding, pmc_filename_list, save_xml_path):

    ## loop over each pmc article and grab the BioC format of the full text article local
    for pmc_article in pmc_filename_list:
        ##https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_[format]/[ID]/[encoding]
        full_url = api_url_base + format + pmc_article + encoding


        #save the resulting xml file to BioC_section_info

        with open('%s%s%s%s.xml' %(save_xml_path, pmc_article, '.nxml.gz.txt', '.BioC-full_text'), 'w') as BioC_full_text:
            #PMC1247630.nxml.gz.txt.gz.regex-sections.annot

            response = requests.get(full_url) ##full text (xml string)
            BioC_full_text.write(response.text)


def process_BioC_section_file(BioC_xml_path, pmc_filename_list, possible_section_names_dict):
    ##get the starts of each section

    ##loop over each pmc file to get BioC stuff
    for i, pmc_filename in enumerate(pmc_filename_list):
        pmc_section_dict = {} ##dictionary for each pmc article: section_name -> start (the first occurance)


        # if i < 3:
        print(pmc_filename)
        BioC_file = '%s%s%s.xml' %(BioC_xml_path, pmc_filename, '.nxml.gz.txt.BioC-full_text')
        tree = ET.parse(BioC_file)
        root = tree.getroot()

        section_type = ''
        offset = ''
        ##loop over each passage and provide the section type and offset (span start of the passage)
        for passage in root.iter('passage'):
            for child in passage:
                if child.tag == 'infon':
                    if child.attrib['key'] == 'section_type':
                        section_type = child.text
                    else:
                        pass
                elif child.tag == 'offset':
                    offset = child.text

                else:
                    pass

            # print(section_type, offset)
            if section_type and offset:
                if pmc_section_dict.get(section_type):
                    pass
                else:
                    pmc_section_dict[section_type] = int(offset)


            else:
                raise Exception('ERROR: POSSIBLE ERROR WITH SECTION TYPE INFORMATION!')


        # print(pmc_section_dict)

        ##output the pmc_section_dict to use for section info for gold standard stuff
        with gzip.open('%s%s%s%s.gz' % (BioC_xml_path, pmc_filename, '.nxml.gz.txt.gz', '.BioC-sections.annot'),
                       'wt+') as final_section_file:
            for section, start in pmc_section_dict.items():
                if section in possible_section_names_dict.keys():
                    final_section_file.write('%s\t%s %s\t%s\t%s\n' %(pmc_filename + '.nxml.gz.txt', 'BioC', 'XML', possible_section_names_dict[section], start))




if __name__ == '__main__':

    ##get the article names we need to grab from BioC API
    article_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Articles/'

    pmc_filename_list = get_list_of_pmcids(article_path)


    ##Get the BioC format section info
    ##https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_[format]/[ID]/[encoding]
    api_url_base = 'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_'
    format = 'xml/'
    encoding = '/unicode'
    save_xml_path = '/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/section_info_BioC/'

    # get_all_BioC_section_files(api_url_base, format, encoding, pmc_filename_list, save_xml_path)


    ##process the BioC full text files to grab out the section information
    ##section names
    possible_section_names_dict = {'TITLE':'title', 'ABSTRACT':'abstract', 'INTRO':'introduction', 'METHODS':'methods', 'RESULTS':'results', 'DISCUSS':'discussion', 'CONCL':'conclusion'}
    process_BioC_section_file(save_xml_path, pmc_filename_list, possible_section_names_dict)
