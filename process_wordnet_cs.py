import xml.etree.ElementTree as ET
import json
import re
from collections import defaultdict
import argparse

def extract_synonyms_to_json(xml_file, output_file):
    with open(xml_file, 'r', encoding='ISO-8859-2') as f:
        content = f.read()

    # Fix the missing root element issue
    if content.startswith('<?xml'):
        end_of_decl = content.find('?>') + 2
        valid_xml_string = content[:end_of_decl] + "<ROOT>" + content[end_of_decl:] + "</ROOT>"
    else:
        valid_xml_string = "<ROOT>" + content + "</ROOT>"

    # Parse the valid XML from our string in memory
    root = ET.fromstring(valid_xml_string)

    # Dictionary to hold the word as the key, and a set of synonyms as the value
    synonyms_map = defaultdict(set)

    # Loop through each SYNSET block
    for synset in root.findall('SYNSET'):
        synonym_node = synset.find('SYNONYM')
        if synonym_node is not None:
            
            # Extract all words within the same synset
            words_in_synset = []
            for literal in synonym_node.findall('LITERAL'):
                word = literal.text.strip() if literal.text else ""

                # Remove any ^number annotations and trim whitespace
                word = re.sub(r'\^\d+', '', word).strip()

                # Don't add multi-word words
                word = word if len(word.split()) == 1 else ""

                if word:
                    words_in_synset.append(word)
            
            # Map each word to its other synonyms in the group
            for word in words_in_synset:
                for syn in words_in_synset:
                    if word == syn: continue

                    synonyms_map[word].add(syn)

    # Convert sets to lists so they can be saved as JSON
    final_json_dict = {}
    for word, syns in sorted(synonyms_map.items()):
        if syns:
            final_json_dict[word] = sorted(list(syns))

    # Write the dictionary to a JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_json_dict, f, ensure_ascii=False, indent=4)
                
    print(f"Extraction complete! Saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract synonyms from an XML file and save to JSON.")
    parser.add_argument('--xml_file', type=str, default='utils/wordnet/nas_anotacni_slovnik.xml', help='Path to the input XML file containing synonyms.')
    parser.add_argument('--output_file', type=str, default='utils/wordnet/synonyms_cs.json', help='Path to the output JSON file to save the synonyms dictionary.')
    args = parser.parse_args()

    # Run the extraction
    extract_synonyms_to_json(args.xml_file, args.output_file)