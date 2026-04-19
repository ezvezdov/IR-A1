# Vector Space Model Information Retrieval System

This project implements an experimental Information Retrieval system based on the Vector Space Model (VSM). The system is designed to rank documents according to their relevance to specific topics using an inverted index. It supports both English and Czech test collections and experiments with various text pre-processing techniques, weighting schemes, and query expansion methods.

## Features
* **Text Preprocessing:** Supports lemmatization (using the MorphoDiTa tagger), case folding, Part-of-Speech based stopping, and numbers normalization.
* **Weighting Schemes:** Offers various term and document weighting schemes, including `nnn`, `nnc`, `ntn`, `ntc`, `lnn`, `lnc`, `ltn`, and `ltc`. (Note: Experimental results showed `ltn.lnc` as the best performing scheme for both English and Czech collections).
* **Query Expansion:** Includes thesaurus-based expansion using synonyms from WordNet. It uses the NLTK WordNet interface for English and the Czech WordNet 1.9 PDT for Czech.
* **Multiprocessing:** Features parallel processing capabilities to speed up the processing of large document collections.
* **Index Management:** Supports saving the constructed inverted index to disk and loading a pre-computed index to expedite iterative experimentation.

## Project Structure
* `run`: The primary executable entry point that handles command-line argument parsing and orchestrates the retrieval pipeline.
* `main.py`: Contains the core algorithmic logic for index construction, term-weighting, similarity computation, and document ranking.
* `parser.py`: Manages the ingestion and preprocessing of TREC-formatted topic files and SGML-based document collections.
* `Makefile`: Automates the project build process and environment setup.
* `process_wordnet_cs.py`: A utility script that processes the Czech WordNet dataset into a custom JSON dictionary for query expansion.
* `download_external.sh`: Automates the acquisition of external assets like MorphoDiTa models, datasets, and the `trec_eval` tool.
* `requirements.txt`: Defines the Python runtime dependencies.

## Building and Execution

### Building
The build process primarily involves setting up the Python environment and downloading external resources. 
To build the project, navigate to the project directory and run:
```bash
make
```

### Execution
The system operates via the command line using the `run` script. 

**Example of use:**
```bash
./run -q topics.xml -d documents.lst -r run -o sample.res
```

### Core Command-line Arguments
| Argument | Description |
| :--- | :--- |
| `-q` | **Required.** A file including topics in the TREC format (.xml file). |
| `-d` | **Required.** A file including document filenames (.lst file). |
| `-r` | **Required.** A string identifying the experiment run. |
| `-o` | **Required.** The output file for retrieval results (.res file). |
| `--top_k` | Number of top documents to retrieve for each query (Default: 1000). |
| `--run_0`, `--run_1`, `--run_2` | Flags to automatically apply specific baseline or constrained experimental setups. |
| `--lemmatization`, `--case_folding`, `--pos_stopping` | Flags for specific text preprocessing techniques. |
| `--doc_weights`, `--query_weights` | Specify the weighting schemes for document and query terms. |

## Pre-defined Experimental Setups
The system includes built-in configurations for standardized experiment runs:
* **Run-0 (Baseline):** Uses natural term weighting, whitespace/punctuation tokenization, and cosine similarity without any query expansion or relevance feedback.
* **Run-1 (Constrained):** Applies case folding, lemmatization, logarithmic term weighting (`ltn.lnc`), and thesaurus-based expansion (scaling factor 0.2) on topic titles.
* **Run-2 (Unconstrained):** Builds upon the Run-1 configuration by expanding the query construction to include the topic description and narrative fields.
