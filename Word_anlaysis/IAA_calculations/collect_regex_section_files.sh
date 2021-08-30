#!/usr/bin/env bash

prenatal_document_info='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/1_First_Full_Annotation_Task_9_13_19/document_collection_pre_natal'

prenatal_document_info_round2='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/1_First_Full_Annotation_Task_9_13_19/document_collection_pre_natal_round2'

article_files='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/Articles'

output_file='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/0_Gold_Standard_Annotation/section_info_crude'



##loop through the article files and pull out the corresponding ".gz.regex-sections.annot.gz" files

for file in $article_files/*.nxml.gz.txt;
do
#    echo $file
    pmc_filename="${file##*/}" ##grab the last string after the "/"
    regex_sections='.gz.regex-sections.annot.gz'
    echo $pmc_filename

    ##check to see if the document is in the first round or the second round and copy it to the output file
    if test -f $prenatal_document_info/$pmc_filename$regex_sections; then
#        echo 'woot'
        cp $prenatal_document_info/$pmc_filename$regex_sections $output_file/
    elif test -f $prenatal_document_info_round2/$pmc_filename$regex_sections; then
#        echo '2nd round'
        cp $prenatal_document_info_round2/$pmc_filename$regex_sections $output_file
    fi
done

