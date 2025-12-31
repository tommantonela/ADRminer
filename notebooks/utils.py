from tqdm.notebook import tqdm
from pythonjsonlogger.json import JsonFormatter
from typing import Dict, Tuple
import logging
import sys
import json
import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

formatter = JsonFormatter(fmt='%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler = logging.StreamHandler(sys.stdout)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)


def get_documents(org_projects: Tuple[str, str, str], adrs_dict: Dict, field='both', verbose=False):
    # Extract documents from the ADRs based on the specified field
    docs = {} # []
    for org, project in org_projects:
        if verbose:
            logger.info("===", org, project)  # Added print statement for verbose output
        adrs = adrs_dict[org][project]
        for adr in adrs.keys():
            if verbose:
                logger.info(adr)
            doc=""
            if field == 'content':
                doc = adrs[adr].get_content_no_code_str()
            elif field == 'title':
                doc = adrs[adr].get_title()
            elif field == 'both':
                doc = adrs[adr].get_title() + " " + adrs[adr].get_content_no_code_str()
            elif field == 'raw':
                doc = adrs[adr].get_full_raw_content()
            elif field == 'decision':
                doc = "* ADR Title: " + adrs[adr].get_title() + '\n' + \
                      "* ADR Decision: " + adrs[adr].get_decision()
            if verbose:
                logger.info(doc)
            docs[(org, project, adr)] = doc
    if verbose:
        logger.info("===")
    return docs

def get_documents_by_key(org_project: Tuple[str, str, str], adrs_dict: Dict, field='content', verbose=False) -> Dict[str, str]:
    docs = get_documents([org_project], adrs_dict, field=field, verbose=verbose)
    return {adr: docs[(org, project, adr)] for org, project, adr in docs}

def get_document(org: str, project: str, adr: str, adrs_dict: Dict, field='content', verbose=False) -> str:
    docs = get_documents([(org, project)], adrs_dict, field=field, verbose=verbose)
    return docs.get((org, project, adr), "")

def process_projects(dict_adrs: Dict, min_adrs_per_project: int = 5, min_adr_length: int = 500):
    # Check projects and ADRs and filter out those that do not have enough ADRs or ADRs that are too short
    valid_projects = set()
    filtered_projects = set()
    all_projects = set()
    for org in tqdm(dict_adrs, "organizations"): 
        for project in dict_adrs[org]:
            all_projects.add((org, project))
            # print(dict_adrs[org][project].keys())
            if len(dict_adrs[org][project]) < min_adrs_per_project:
                filtered_projects.add((org, project))
                continue
            valid = 0
            for adr_ in dict_adrs[org][project]: # TODO: Queremos que tenga más de 5 adrs con 500 chars o las dos condiciones se evalúan por separado?
                s = dict_adrs[org][project][adr_].get_content_no_code_str()
                if (len(s) >= min_adr_length) and not s.isspace() :
                    valid += 1
            if valid < min_adrs_per_project:
                filtered_projects.add((org, project))
                continue
            # print("Valid project: ", org, project)
            valid_projects.add((org, project))
    
    logger.info("all orgs+projects: ", len(all_projects))
    logger.info("filtered projects: ", len(filtered_projects))
    logger.info("valid projects: ", len(valid_projects))
    return {
        "all_projects": list(all_projects),
        "filtered_projects": list(filtered_projects),
        "valid_projects": list(valid_projects)
    }

def convert_sample_to_examples(df: pd.DataFrame, filename: str, adr_column='text', category_column='human') -> dict:
    df = df.dropna(subset=[category_column, adr_column])
    list_dicts = []
    for index, row in df.iterrows():
        # print(f"ADR: {row['text']}\nCategory: {row['human']}")
        list_dicts.append({'ADR': row[adr_column].strip("'"), 'Category': row[category_column]})
    # Save the dictionary to the JSON file
    if filename is not None:
        with open(filename, "w") as f:
            json.dump(list_dicts, f, indent=4) # Using 'indent=4' makes the file human-readable
    return list_dicts

def prune_corpus(docs: dict) -> tuple[list[str], list[str]]:
    """
    Prune the corpus of documents by removing spurious strings (if any)
    :param docs: dictionary with the documents
    :return: pruned corpus
    """    
    all_adr_keys = list(docs.keys())

    # Get the corpus of documents for topic modeling
    logger.info("Corpus (before):", len(docs))

    # Removing spurious strings (if any)
    corpus = [docs[(org, project, adr)] for org, project, adr in all_adr_keys]
    corpus = [s for s in corpus if (len(s) > 0) and not s.isspace()]

    keys_to_remove = []
    for k in all_adr_keys:
        candidate_adr = docs[k]
        if candidate_adr not in corpus:
            logger.info("Removing spurious ADR:", k)
            keys_to_remove.append(k)
    all_adr_keys = [k for k in all_adr_keys if k not in keys_to_remove] # Update the keys (for further reference)
    logger.info("Corpus (after):", len(corpus))

    return corpus, all_adr_keys