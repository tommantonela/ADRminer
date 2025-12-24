from tqdm.notebook import tqdm
from pythonjsonlogger.json import JsonFormatter
from typing import Dict, Tuple
import logging
import sys


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
