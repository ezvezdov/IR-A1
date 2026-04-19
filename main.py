import re
import json
import math
import pathlib
import argparse
import heapq
import multiprocessing as mp
from collections import Counter

import tqdm
import nltk
from nltk.corpus import wordnet as wn
from ufal.morphodita import Tagger, Forms, TaggedLemmas, TokenRanges

from parser import parse_topics, get_file_content
import parser

# MorphoDiTa tagger (global variable to be initialized in main and worker processes)
tagger = None

# Download WordNet data if not already present
nltk.download('wordnet')
synonyms_cs = None

# Structures for inverted index and document norms
inverted_index = dict()
doc_norms = dict()



morphodita_tagger = {
    "cs": "utils/morphodita/czech-morfflex2.0-pdtc1.0-220710.tagger",
    "en": "utils/morphodita/english-morphium-wsj-140407.tagger"
}

def get_synonyms(word, language_code):
    """
    Extracts synonyms for a given word using NLTK WordNet.
    """
    synonyms = set()
    
    # Get synsets for word
    for synset in wn.synsets(word, lang=language_code):
        
        # Extract lemmas
        for lemma_name in synset.lemma_names(language_code):
            
            # Skip the original word itself
            if lemma_name == word: continue

            # Only consider single-word synonyms to avoid complications
            if len(lemma_name.split('_')) == 1: synonyms.add(lemma_name)
        
    return list(synonyms)




def tokenize_lemmatize(text, language, lemmatization, pos_stopping, current_tagger):
    morpho = current_tagger.getMorpho()
    forms = Forms()
    lemmas = TaggedLemmas()
    tokens = TokenRanges()
    
    # Create tokenizer
    tokenizer = current_tagger.newTokenizer()
    tokenizer.setText(text)

    final_tokens = []

    # Iterate through sentences and tag them
    while tokenizer.nextSentence(forms, tokens):
        current_tagger.tag(forms, lemmas)
        
        for i in range(len(lemmas)):
            lemma = morpho.rawLemma(lemmas[i].lemma) # Use raw lemma
            pos_tag = lemmas[i].tag

            new_token = lemma if lemmatization else forms[i]

            if pos_stopping:
                # # Lexicon-based
                # if lemma in stopwords:
                #     continue
                
                # POS-based
                if language == "en" and pos_tag not in {'NN', 'NNS', 'NNP', 'NNPS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'JJ', 'JJS', 'RB', 'CD', 'FW'}:
                    continue
                elif language == "cs" and pos_tag[0] not in {'A', 'C', 'D', 'I', 'N', 'V', 'X', 'B', 'F'}:
                    continue

            final_tokens.append(new_token)
                     
    return final_tokens

def tokenize_simple(text):
    # Whitespaces and Punctuations are removed by default
    tokens = [token for token in re.split(r'\W+', text) if token]
    
    return tokens




def process_text(text, args):
    if args.lemmatization or args.pos_stopping:
        tokens = tokenize_lemmatize(text, args.language, args.lemmatization, args.pos_stopping, tagger)
    else:
        tokens = tokenize_simple(text)

        if args.case_folding:
            tokens = [token.lower() for token in tokens]
    
    if args.number_normalization:
        tokens = [token if not token.isdigit() else '<num>' for token in tokens]

    return tokens







# --- Multiprocessing Worker Setup ---
worker_tagger = None
worker_args = None

def init_worker(args_obj):
    """Initializes the tagger globally ONLY for the worker process."""
    global worker_tagger, worker_args
    worker_args = args_obj
    if args_obj.lemmatization:
        worker_tagger = Tagger.load(morphodita_tagger[args_obj.language])


def process_file(doc_path):
    """Worker function to parse and tokenize a single document file."""
    global worker_tagger, worker_args
    results = []
    
    for doc in parser.go_through_file(doc_path, worker_args.language):
        document_text = doc.merge_all()

        tokens = process_text(document_text, worker_args)
        
        # We return the doc_no and a Counter of tokens to keep data transfer small
        results.append((doc.doc_no, Counter(tokens)))
        
    return results
# ------------------------------------

def create_inverted_index(args):
    documents_lst_path = pathlib.Path(args.documents)
    documents_paths = get_file_content(documents_lst_path).splitlines()
    documents_paths = [documents_lst_path.parent / documents_lst_path.stem / document for document in documents_paths]

    print(f"Starting parallel processing using {args.cpu_n} cores...")
    
    # create multiprocessing pool
    with mp.Pool(processes=args.cpu_n, initializer=init_worker, initargs=(args,)) as pool:
        all_results = list(tqdm.tqdm(
            pool.imap_unordered(process_file, documents_paths), 
            total=len(documents_paths), 
            desc="Parsing & Tokenizing", 
            unit="file"
        ))
    
    print("Merging results into inverted index...")
    for file_results in tqdm.tqdm(all_results, desc="Merging"):
        for doc_no, frequency_list in file_results:
            if not frequency_list:
                continue
            for token, tf_d in frequency_list.items():
                if inverted_index.get(token, None) is None:
                    inverted_index[token] = dict()

                doc_weight = None
                if args.doc_weights.startswith('n'):
                    doc_weight = tf_d
                elif args.doc_weights.startswith('l'):
                    doc_weight = 1 + math.log10(tf_d)

                inverted_index[token][doc_no] = doc_weight

                # Accumulate the square of the weight for this document's norm
                doc_norms[doc_no] = doc_norms.get(doc_no, 0.0) + (doc_weight * doc_weight)

            if args.doc_weights[2] == 'n':
                doc_norms[doc_no] = 1
            elif args.doc_weights[2] == 'c':
                doc_norms[doc_no] = math.sqrt(doc_norms[doc_no])


    # Document frequency weighting    
    if args.doc_weights[1] == 'n':
        pass
    elif args.doc_weights[1] == 't':
        tmp_norms = dict()
        TOTAL_DOCUMENTS = len(doc_norms)
        for token, doc_dict in inverted_index.items():
            df_t = len(doc_dict)
            idf_t = math.log10(TOTAL_DOCUMENTS / df_t)

            for doc_no, weight in doc_dict.items():
                final_weight = weight * idf_t
                inverted_index[token][doc_no] = final_weight
                
                # Accumulate the square of the weight for this document's norm
                tmp_norms[doc_no] = tmp_norms.get(doc_no, 0.0) + (final_weight * final_weight)
        
        # Calculate the final norms for each document
        if args.doc_weights[2] == 'c':
            for doc_no, sum_of_squares in tmp_norms.items():
                doc_norms[doc_no] = math.sqrt(sum_of_squares)

def query_expansion(doc_query_sim, original_frequency, args):
    global synonyms_cs

    synonym_frequency = Counter()
    synonyms_added = []
    
    # We iterate over original_frequency to exclude doubling synonyms for the same word
    for token in original_frequency.keys(): 
        if args.language == 'en':
            synonims = get_synonyms(token, 'eng')
        elif args.language == 'cs':
            synonims = synonyms_cs.get(token, [])

        synonyms_added.extend(synonims)

    if synonyms_added:
        synonym_tokens = process_text(" ".join(synonyms_added), args)
        synonym_frequency = Counter(synonym_tokens)

    # SYNONYM_PENALTY = 0.2
    SYNONYM_PENALTY = args.thesaurus_w

    for token, tf_q in synonym_frequency.items():
        query_weight = None
        if args.query_weights[0] == 'l':
            query_weight = 1 + math.log10(tf_q)
        elif args.query_weights[0] == 'n':
            query_weight = tf_q
        
        if args.query_weights[1] == 'n':
            query_weight = query_weight * 1
        elif args.query_weights[1] == 't':
            if token not in inverted_index: continue
            N = len(doc_norms)
            df_t = len(inverted_index[token])
            idf_t = math.log10(N / df_t)
            query_weight *= idf_t
        
        
        # Apply the penalty!
        query_weight *= SYNONYM_PENALTY
        
        # Skip adding synonym weights to query_norm (works better)


        if token in inverted_index:
            for doc_no, doc_weight in inverted_index[token].items():
                doc_query_sim[doc_no] = doc_query_sim.get(doc_no, 0) + (doc_weight * query_weight)


def retrieve_documents(args):

    # Clear the output file before writing results
    with open(args.output_file, 'w') as file:
            file.write("")

    # Go through queries and calculate similarity with documents
    print("Retrieving documents for queries...")
    for query in parse_topics(args.queries):
        
        
        # Set query text based on whether we want to use description or just title
        if args.use_query_description:
            query_text = query.merge_all()
        else:
            query_text = query.title

        print("Query:", query_text)

        tokens = process_text(query_text, args)
        

        # Keep original tokens separate
        original_frequency = Counter(tokens)
        original_frequency_title = Counter(process_text(query.title, args))
        
        query_norm = 0
        doc_query_sim = dict()
        for token, tf_d in original_frequency.items():
            query_weight = None
            if args.query_weights[0] == 'l':
                query_weight = 1 + math.log10(tf_d)
            elif args.query_weights[0] == 'n':
                query_weight = tf_d
            
            
            if args.query_weights[1] == 'n':
                query_weight = query_weight * 1
            elif args.query_weights[1] == 't':
                if token not in inverted_index: continue
                N = len(doc_norms)
                df_t = len(inverted_index[token])
                idf_t = math.log10(N / df_t)

                query_weight = query_weight * idf_t
            
            # Accumulate the square of the weight for the query norm
            query_norm += query_weight * query_weight

            if token in inverted_index:
                for doc_no in inverted_index[token].keys():
                    doc_query_sim[doc_no] = doc_query_sim.get(doc_no, 0) + (inverted_index[token][doc_no] * query_weight)

        # Query expansion
        print(args.thesaurus_w)
        if args.thesaurus_w > 0:
            query_expansion(doc_query_sim, original_frequency_title, args)

        # Vector normalization
        if args.query_weights[2] == 'c':
            query_norm = math.sqrt(query_norm)
        elif args.query_weights[2] == 'n':
            query_norm = 1

        # Generate top-k documents
        all_docs = []
        for doc_no, sim in doc_query_sim.items():
            doc_query_sim[doc_no] = sim / (query_norm * doc_norms[doc_no])
            all_docs.append((doc_query_sim[doc_no], doc_no))
        top_docs = heapq.nlargest(args.top_k, all_docs)

        # Write results to output file
        with open(args.output_file, 'a') as file:
            for i in range(len(top_docs)):
                docno = top_docs[i][1]
                sim = top_docs[i][0]
                file.write(f"{query.num} 0 {docno} {i} {sim} {args.run_id}\n")

def init_index(args):
    '''Initializes the inverted index and document norms, either by loading from disk or by creating them from the documents.'''


    if args.load_index:
        global inverted_index, doc_norms

        with open(f'saves/inverted_index_{args.language}.json', 'r', encoding='utf-8') as f:
            inverted_index = json.load(f)
        with open(f'saves/doc_norms_{args.language}.json', 'r', encoding='utf-8') as f:
            doc_norms = json.load(f)
    else:
        create_inverted_index(args)

        # Save the inverted index and norms
        if args.save_index:
            with open(f'saves/inverted_index_{args.language}.json', 'w', encoding='utf-8') as f:
                json.dump(inverted_index, f, ensure_ascii=False, indent=2)
            with open(f'saves/doc_norms_{args.language}.json', 'w', encoding='utf-8') as f:
                json.dump(doc_norms, f, ensure_ascii=False, indent=2)

    

def init(args):
    # Set args.language
    if args.d.endswith('cs.lst'):
        args.language = 'cs'
    elif args.d.endswith('en.lst'):
        args.language = 'en'
    else:
        raise ValueError("Unsupported language. The document list file should end with 'cs.lst' or 'en.lst'.")

    args.queries = args.q
    args.documents = args.d
    args.run_id = args.r
    args.output_file = args.o

    # Set number of CPU cores to use
    if args.cpu_n == -1:
        args.cpu_n = mp.cpu_count()
    else:
        args.cpu_n = min(args.cpu_n, mp.cpu_count())

    # Set default settings based on run_0, run_1, run_2 flags
    if args.run_0:
        print("Running run_0")
        args.doc_weights = 'nnc'
        args.query_weights = 'nnn'
        args.thesaurus_w = 0
    elif args.run_1:
        print("Running run_1")
        args.doc_weights = 'ltn'
        args.query_weights = 'lnc'

        args.lemmatization = True
        # args.pos_stopping = True

        args.thesaurus_w = 0.2

    elif args.run_2:
        print("Running run_2")
        args.doc_weights = 'ltn'
        args.query_weights = 'lnc'

        args.lemmatization = True
        # args.pos_stopping = True

        # args.thesaurus_w = 0.2

        args.use_query_description = True
    else:
        print("Running with custom settings")

    
    if args.thesaurus_w > 0 and args.language == 'cs':
        global synonyms_cs
        with open('utils/wordnet/synonyms_cs.json', 'r', encoding='utf-8') as f:
            synonyms_cs = json.load(f)        

    # Init lemmatizer/POS tagger
    global tagger
    tagger = Tagger.load(morphodita_tagger[args.language])
    

    return args

def main(args):
    # Initialization
    args = init(args)

    # Create/Load inverted index and document norms
    init_index(args)
    print(f"Inverted index and document norms initialized. Vocabulary size: {len(inverted_index)}, Number of documents: {len(doc_norms)}")

    # Retrieve documents for queries and write results to output file
    retrieve_documents(args)


if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("-q", required=True, type=str, help="A file including topics in the TREC format (.xml file).")
    args_parser.add_argument("-d", required=True, type=str, help="A file including document filenames (.lst file).")
    args_parser.add_argument("-r", required=True, type=str, help="A string identifying the experiment")
    args_parser.add_argument("-o", required=True, type=str, help="An output file (.res file).")
    args_parser.add_argument("--top_k", type=int, default=1_000, help="Number of top documents to retrieve for each query.")
    args_parser.add_argument("--run_0", default=False, action="store_true", help="run-0 setup")
    args_parser.add_argument("--run_1", default=False, action="store_true", help="run-1 setup")
    args_parser.add_argument("--run_2", default=False, action="store_true", help="run-2 setup")
    args_parser.add_argument("--lemmatization", default=False, action="store_true", help="Lemmatize tokens using MorphoDiTa.")
    args_parser.add_argument("--pos_stopping", default=False, action="store_true", help="Apply POS-based stopping.")
    args_parser.add_argument("--case_folding", default=False, action="store_true", help="Apply case folding to tokens.")
    args_parser.add_argument("--number_normalization", default=False, action="store_true", help="Normalize numbers to a common token.")
    args_parser.add_argument("--doc_weights", type=str, choices=['nnn', 'nnc', 'ntn', 'ntc', 'lnn', 'lnc', 'ltn', 'ltc'], help="Weighting scheme for document terms.")
    args_parser.add_argument("--query_weights", type=str, choices=['nnn', 'nnc', 'ntn', 'ntc', 'lnn', 'lnc', 'ltn', 'ltc'], help="Weighting scheme for query terms.")
    args_parser.add_argument("--use_query_description", default=False, action="store_true", help="Flag to expand the query using the topic <desc> and <narr> fields")
    args_parser.add_argument("--thesaurus_w", type=float, default=0, help="Weight for the thesaurus synonyms.")
    args_parser.add_argument("--cpu_n", type=int, default=-1, help="Number of CPU cores to use [-1 for all].")
    args_parser.add_argument("--save_index", default=True, action="store_true", help="Save the computed inverted index and norms to saves/.")
    args_parser.add_argument("--load_index", default=False, action="store_true", help="Load precomputed inverted index and norms from saves/ instead of parsing documents.")

    args = args_parser.parse_args()
    
    main(args)