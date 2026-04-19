#!/bin/bash

# Update
git clone https://github.com/ezvezdov/IR-A1.git                                                             
mv -f IR-A1/* .                                                                                                
rm -rf IR-A1

############################################################################################################
# Download documents, topics, qrels and evaluation script
############################################################################################################
wget --user npfl103 --password npfl103 http://ufal.mff.cuni.cz/~pecina/courses/npfl103/data/A1.tgz
tar xf A1.tgz
mv A1/README.md task.md
tar -xzvf A1/trec_eval-9.0.7.tar.gz && mv trec_eval-9.0.7 eval
mv A1/topics-* .
mv A1/documents_* .
mv A1/qrels-* .
rm -r A1 A1.tgz


############################################################################################################
# Download Morphodita models
############################################################################################################
mkdir -p utils/morphodita

curl -o "czech-morfflex2.0-pdtc1.0-220710.zip" "https://lindat.mff.cuni.cz/repository/server/api/core/bitstreams/handle/11234/1-4794/czech-morfflex2.0-pdtc1.0-220710.zip"
unzip -q "czech-morfflex2.0-pdtc1.0-220710.zip" -d "utils/morphodita"
mv utils/morphodita/czech-morfflex2.0-pdtc1.0-220710/czech-morfflex2.0-pdtc1.0-220710.tagger "utils/morphodita/"
rm -rf utils/morphodita/czech-morfflex2.0-pdtc1.0-220710
rm czech-morfflex2.0-pdtc1.0-220710.zip

curl -o "english-morphium-wsj-140407.zip" "https://lindat.mff.cuni.cz/repository/server/api/core/bitstreams/handle/11858/00-097C-0000-0023-68D9-0/english-morphium-wsj-140407.zip"
unzip -q "english-morphium-wsj-140407.zip" -d "utils/morphodita"
mv utils/morphodita/english-morphium-wsj-140407/english-morphium-wsj-140407.tagger "utils/morphodita/"
rm -rf utils/morphodita/english-morphium-wsj-140407
rm english-morphium-wsj-140407.zip


############################################################################################################
# Download & Process Czech Wordnet
############################################################################################################
mkdir -p utils/wordnet

curl -o "Czech_WordNet_1.9_PDT.zip" "https://lindat.mff.cuni.cz/repository/server/api/core/bitstreams/handle/11858/00-097C-0000-0001-4880-3/Czech_WordNet_1.9_PDT.zip"
unzip -q "Czech_WordNet_1.9_PDT.zip" -d "utils/wordnet"
source .venv/bin/activate
python3 process_wordnet_cs.py --xml_file utils/wordnet/nas_anotacni_slovnik.xml --output_file utils/wordnet/synonyms_cs.json
rm utils/wordnet/nas_anotacni_slovnik.xml Czech_WordNet_1.9_PDT.zip

mkdir -p saves/

