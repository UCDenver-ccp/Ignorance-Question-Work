#!/bin/bash

original_doc_path='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/First_Full_Annotation_Task_9_13_19/document_collection_pre_natal_round2/*.nxml.gz.txt.gz'
output_doc_path='/Users/MaylaB/Dropbox/Documents/0_Thesis_stuff-Larry_Sonia/First_Full_Annotation_Task_9_13_19/Articles/'



##ORIGINAL DOCS: NEED TO DECOMPRESS THE .NXML.GZ.TXT.GZ FILES - ##remove the .gz
for f in $original_doc_path
    do
        #echo $f
        search_string="PMC" ##should be 131
        search_string2="BMJ"

        if [[ "$f" == *"$search_string"* ]]; then
            final_search_string=$search_string
        else
            final_search_string=$search_string2
        fi


        ##separate out the doc to save separately in our articles file for knowtator

        rest=${f#*$final_search_string}

        doc_index=$(( ${#f} - ${#rest} - ${#final_search_string} ))
        #echo $doc_index
        doc=${f:$doc_index}
        #echo DOCUMENT $doc


        ##UNZIP ALL THE TXT FILES
        gunzip -c $f > $output_doc_path${doc%.*}
    done


echo "FINISHED OUTPUTTING TEXT DOCUMENTS INTO ARTICLES FOR KNOWTATOR PROCESSING"
