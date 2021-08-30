import os

def split_pmc_files(general_pmcoa_folder, pmc_filename):
    #the delimiter: ================================= PMC6941137 is at the end of the file
    ###.text file
    all_temp_lines = []
    with open('%s%s' %(general_pmcoa_folder, pmc_filename), 'r+') as pmc_full_file:
        for line in pmc_full_file:
            ##output the pmc_file
            if line.startswith('================================= PMC'):
                pmc_article = line.strip('\n').split('= ')[-1]
                with open('%s%s.txt' %(general_pmcoa_folder, pmc_article), 'w+') as pmc_article_file:
                    for l in all_temp_lines:
                        pmc_article_file.write(l)

                ##reset
                all_temp_lines = []

            else:
                all_temp_lines += [line]





    ###.bionlp file equivalent
    bionlp_temp_lines = []

    pmc_bionlp_file = pmc_filename.replace('.text', '.bionlp')
    with open('%s%s' %(general_pmcoa_folder, pmc_bionlp_file), 'r+') as bionlp_full_file:
        for line in bionlp_full_file:
            ##output the pmc_file
            if line.startswith('================================= PMC'):
                pmc_article = line.strip('\n').split('= ')[-1]
                with open('%s%s.bionlp' %(general_pmcoa_folder, pmc_article), 'w+') as pmc_bionlp_file:
                    for b in bionlp_temp_lines:
                        pmc_bionlp_file.write(b)

                ##reset
                bionlp_temp_lines = []

            else:
                bionlp_temp_lines += [line]







if __name__ == '__main__':
    general_pmcoa_folder = '/Users/mabo1182/epistemic_classification/Output_Folders/Evaluation_Files/General_PMCOA_Articles/'

    for root, directories, filenames in os.walk('%s' % (general_pmcoa_folder)):
        for filename in sorted(filenames):
            if filename.startswith('concept-annotations_pmc_PMC_SUBSET_') and filename.endswith('.text'):
                split_pmc_files(general_pmcoa_folder, filename)


