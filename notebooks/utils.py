from tqdm.notebook import tqdm
from pythonjsonlogger.json import JsonFormatter
from typing import Dict, Tuple
import logging
import sys
import json
import pandas as pd
import numpy as np

import seaborn as sns # Optional: for a visual heatmap
import matplotlib.pyplot as plt # Optional: for plotting

from sklearn.preprocessing import normalize
from sklearn.preprocessing import LabelEncoder

from itertools import cycle, islice

from umap import UMAP

from statsmodels.graphics.mosaicplot import mosaic

from matplotlib.patches import Patch
import matplotlib.colors as mcolors

import itertools
from collections import deque


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

# -- Visualization --

def show_classification_report(report_dict: dict, title="", figsize=(8, 6), cmap="rocket_r"):
    plt.figure(figsize=figsize)
    sns.heatmap(pd.DataFrame(report_dict).iloc[:-1, :].T, annot=True, cmap=cmap)
    plt.title(title, fontsize=14)
    plt.show()


def show_confusion_matrix(confusion_df: pd.DataFrame, cmap='Greens', title="", figsize=(8,6), normalized=False):
    plt.figure(figsize=figsize)
    if not normalized:
        sns.heatmap(confusion_df, annot=True, cmap=cmap, fmt='d')
        plt.title(title, fontsize=16)
    else:
        normalized_cm = normalize(confusion_df, axis=1, norm="l1")
        normalized_df = pd.DataFrame(normalized_cm, index=confusion_df.columns, columns=confusion_df.columns)
        sns.heatmap(normalized_df, annot=True, cmap=cmap)
        plt.title(title+" [normalized]", fontsize=16)
    
    plt.ylabel('Actual (True) Label', fontsize=14)
    plt.xlabel('Predicted Label', fontsize=14)
    plt.show()


def show_target_frequencies(target_values: pd.Series, color_dict: dict[str, str]=None, title="Frequencies of Categories (Target)", figsize=(7, 4), width=0.6):
    
    relative_frequencies = target_values.value_counts(normalize=True).sort_index(ascending=True) # embeddings_df['target'].value_counts(normalize=True)
    
    unique_target_values = target_values.sort_values(ascending=True).unique()
    if color_dict is not None:
        labels = unique_target_values
        sorted_color_dict = dict(sorted(color_dict.items()))
        my_colors = [c for k,c in sorted_color_dict.items() if k in labels]
    else:
        labels = unique_target_values
        n_colors = len(labels)
        my_cmap = plt.get_cmap('Set3', n_colors)
        my_colors = [mcolors.to_hex(c) for c in my_cmap.colors]
        color_dict = {lb:c for lb,c in zip(relative_frequencies.keys(),my_colors)}
    
    # cmap = mcolors.ListedColormap(my_colors)
    # my_colors = list(islice(cycle(['b', 'r', 'g', 'y', 'k']), None, len(labels)))

    # if encoding is not None:
    #     reordered_colors = [my_colors[i] for i in encoding]
    # else:
    #     reordered_colors = my_colors

    plt.figure(figsize=figsize)
    ax = relative_frequencies.plot(kind='barh', title=title, color=my_colors, width=width)
    for p in ax.patches:
        rounded_string = "{:.2f}".format(p.get_width()*100)
        ax.annotate(rounded_string+'%', (p.get_width() * 1.02, p.get_y() * 1.05))
    plt.xlabel('Frequency')
    plt.ylabel('Category')
    plt.xlim(0, 1.0)
    plt.show()

    return color_dict


def show_umap_projection(target_values: pd.Series, embeddings, color_dict: dict[str, str]=None, figsize=(8, 8), title="", s=50, alpha=0.6):

    mapper = UMAP(n_neighbors=15, min_dist=0.1, n_components=2, random_state=42)
    projected_embeddings = mapper.fit_transform(embeddings)
    
    unique_target_values = target_values.sort_values(ascending=True).unique()
    if color_dict is not None:
        # labels = list(color_dict.keys())
        labels = unique_target_values
        sorted_color_dict = dict(sorted(color_dict.items()))
        my_colors = [c for k,c in sorted_color_dict.items() if k in labels]
    else:
        labels = unique_target_values
        n_colors = len(labels)
        my_cmap = plt.get_cmap('Set3', n_colors)
        my_colors = [mcolors.to_hex(c) for c in my_cmap.colors]
        color_dict = {lb:c for lb,c in zip(unique_target_values,my_colors)}

    target_names = target_values.tolist()

    fig, ax = plt.subplots(figsize=figsize)
    # n_colors = len(le.classes_)
    # my_colors = plt.get_cmap('Set3', n_colors)
    # my_colors = [mcolors.to_hex(my_colors(i)) for i in range(n_colors)]
    # print(len(my_colors), "colors")
    # my_colors = list(islice(cycle(['b', 'r', 'g', 'y', 'k']), None, len(target_values.unique())))

    for idx, label in enumerate(labels):
        # Get the indices for the current label
        if label in unique_target_values:
            indices = np.where([l == label for l in target_names])
            print(label, len(indices[0])) #, indices[0])
            ax.scatter(projected_embeddings[indices, 0], projected_embeddings[indices, 1], label=label, s=s, c=my_colors[idx], alpha=alpha)

    # Add the legend
    ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1)) # Position outside plot for clarity

    ax.set_title(title)
    # ax.set_xlabel('UMAP 1')
    # ax.set_ylabel('UMAP 2')
    plt.axis('off')
    plt.show()
    
    return color_dict
    
def show_classification_mosaic(cm, cm_labels: list[str], color_dict: dict[str, str]=None, x_labels_colored=True, title="", figsize=(11, 10)):

    results = cm.tolist()
    n_classes = len(cm_labels)
    cm_labels_sorted = cm_labels.copy()
    cm_labels_sorted.sort()

    if color_dict is not None:
        # labels = list(color_dict.keys())
        labels = cm_labels_sorted
        sorted_color_dict = dict(sorted(color_dict.items()))
        my_colors = [c for k,c in sorted_color_dict.items() if k in labels]
    else:
        labels = cm_labels_sorted
        n_colors = len(labels)
        my_cmap = plt.get_cmap('Set3', n_colors)
        my_colors = [mcolors.to_hex(c) for c in my_cmap.colors]
        color_dict = {lb:c for lb,c in zip(labels,my_colors)}

    """
    build a mosaic plot from the results of a classification
    
    parameters:
    n_classes: number of classes
    results: results of the prediction in form of an array of arrays
    
    In case of 3 classes the prdiction could look like
    [[10, 2, 4],
     [1, 12, 3],
     [2, 2, 9]
    ]
    where there is one array for each class and each array holds the
    predictions for each class [class 1, class 2, class 3].
    
    This is just a prototype including colors for 6 classes.
    """
    class_lists = [range(n_classes)]*2
    mosaic_tuples = tuple(itertools.product(*class_lists))
    
    res_list = results[0]
    for i, l in enumerate(results):
        if i == 0:
            pass
        else:
            tmp = deque(l)
            tmp.rotate(-i)
            res_list.extend(tmp)
    data = {t:res_list[i] for i,t in enumerate(mosaic_tuples)}

    fig, ax = plt.subplots(figsize=figsize)
    # plt.rcParams.update({'font.size': 16})
        
    # n_colors = len(labels)
    # my_colors = plt.get_cmap('Set3', n_colors)
    # my_colors = [mcolors.to_hex(my_colors(i)) for i in range(n_colors)]           
    # my_colors = list(islice(cycle(['b', 'r', 'g', 'y', 'k']), None, len(labels)))

    colors = deque(my_colors) # deque(pallet[:n_classes])
    # print("my colors", len(my_colors))
    all_colors = []
    for i in range(n_classes):
        if i > 0:
            colors.rotate(-1)
        all_colors.extend(colors)
    # print("All colors:", len(all_colors), "classes:", n_classes, "mosaic tuples:", len(mosaic_tuples))
    props = {(str(a), str(b)):{'color':all_colors[i]} for i,(a, b) in enumerate(mosaic_tuples)}

    labelizer = lambda k: ''

    p = mosaic(data, labelizer=labelizer, properties=props, ax=ax)

    # title_font_dict = {
    #     'fontsize': 20,
    #     'color' : font_color,
    # }
    # axis_label_font_dict = {
    #     'fontsize': 16,
    #     'color' : font_color,
    # }

    ax.tick_params(axis = "x", which = "both", bottom = False, top = False)
    ax.axes.yaxis.set_ticks([])
    ax.tick_params(axis='x', which='major') #, labelsize=14)
    ax.set_xticklabels(cm_labels_sorted, rotation=90, fontsize=10)

    # Iterate over the labels and set their individual colors
    if x_labels_colored:
        for tick in ax.get_xticklabels():
            tick.set_color(color_dict[tick.get_text()])

    # ax.set_title(title) #, fontdict=title_font_dict, pad=25)
    ax.set_xlabel('Actual (true) Label', fontsize=12) #, fontdict=axis_label_font_dict, labelpad=10)
    ax.set_ylabel('Predicted Label', fontsize=14) #, fontdict=axis_label_font_dict, labelpad=35)

    legend_elements = [Patch(facecolor=all_colors[labels.index(i)], label='{}'.format(i)) for i in labels]
    ax.legend(handles=legend_elements, bbox_to_anchor=(0.5, 1.02), loc='lower center', fontsize=10)

    plt.suptitle(title, fontsize=14)
    plt.tight_layout()
    plt.show()

    return color_dict
