"""
Utility functions for ADR mining and analysis notebooks.

This module provides helper functions for:
- Extracting and processing ADR documents
- Filtering and cleaning text corpora
- Visualizing classification results and embeddings
- Creating classification reports and confusion matrices

The module is designed for use in Jupyter notebooks and supports
various visualization libraries (matplotlib, seaborn, UMAP).
"""

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


def get_documents(org_projects: Tuple[str, str, str], adrs_dict: Dict, field='both', verbose=False) -> Dict[Tuple[str, str, str], str]:
    """
    Extract documents from ADRs based on the specified field.
    
    This function iterates through organizations and projects, extracting document
    content from each ADR according to the specified field type. It supports
    multiple extraction modes including full content, title only, or combinations.
    
    Args:
        org_projects: List of tuples containing (org, project) pairs.
            Note: Currently accepts tuples but treats them as (org, project) pairs.
        adrs_dict: Nested dictionary mapping org -> project -> ADR objects.
            The ADR objects must implement methods like get_title(), get_content_no_code_str(),
            get_decision(), and get_full_raw_content().
        field: Type of content to extract. Options:
            - 'content': Content without code blocks
            - 'title': ADR title only
            - 'both': Title + content without code blocks (default)
            - 'raw': Full raw content including all sections
            - 'decision': Title + decision section formatted as markdown list
        verbose: If True, log processing details including org, project, ADR name, and content.
    
    Returns:
        Dictionary mapping (org, project, adr_name) tuples to document content strings.
        Keys are 3-tuples that uniquely identify each ADR.
    
    Example:
        >>> org_projects = [("org1", "proj1"), ("org2", "proj2")]
        >>> docs = get_documents(org_projects, adrs_dict, field='both')
        >>> print(list(docs.keys())[0])
        ('org1', 'proj1', 'ADR001-example')
    """
    docs = {} # []
    for org, project in org_projects:
        if verbose:
            logger.info("===", org, project)
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
    """
    Extract documents from a single organization/project and return simplified dictionary.
    
    This is a convenience wrapper around get_documents() that returns a simpler
    dictionary mapping only ADR names to their content, rather than the full
    (org, project, adr) tuple keys.
    
    Args:
        org_project: Tuple containing (org, project) to extract documents from.
        adrs_dict: Nested dictionary mapping org -> project -> ADR objects.
        field: Type of content to extract. Options:
            - 'content': Content without code blocks (default)
            - 'title': ADR title only
            - 'both': Title + content without code blocks
            - 'raw': Full raw content
            - 'decision': Title + decision section
        verbose: If True, log processing details.
    
    Returns:
        Dictionary mapping ADR names (strings) to document content strings.
    
    Example:
        >>> docs = get_documents_by_key(("org1", "proj1"), adrs_dict, field='title')
        >>> print(docs['ADR001'])
        'Use microservice architecture'
    """
    docs = get_documents([org_project], adrs_dict, field=field, verbose=verbose)
    return {adr: docs[(org, project, adr)] for org, project, adr in docs}

def get_document(org: str, project: str, adr: str, adrs_dict: Dict, field='content', verbose=False) -> str:
    """
    Extract a single ADR document by name.
    
    This is a convenience function for retrieving the content of a specific
    ADR from a specific organization and project.
    
    Args:
        org: Organization name.
        project: Project name within the organization.
        adr: ADR name/identifier to retrieve.
        adrs_dict: Nested dictionary mapping org -> project -> ADR objects.
        field: Type of content to extract. Options:
            - 'content': Content without code blocks (default)
            - 'title': ADR title only
            - 'both': Title + content without code blocks
            - 'raw': Full raw content
            - 'decision': Title + decision section
        verbose: If True, log processing details.
    
    Returns:
        Document content string, or empty string if ADR not found.
    
    Example:
        >>> doc = get_document("org1", "proj1", "ADR001", adrs_dict)
        >>> print(doc[:50])
        'Use the microservice architecture style with...'
    """
    docs = get_documents([(org, project)], adrs_dict, field=field, verbose=verbose)
    return docs.get((org, project, adr), "")

def process_projects(dict_adrs: Dict, min_adrs_per_project: int = 5, min_adr_length: int = 500) -> Dict[str, list]:
    """
    Filter projects based on ADR count and minimum content length.
    
    This function validates projects by checking if they have enough ADRs meeting
    minimum length requirements. Projects that don't meet thresholds are filtered out.
    Useful for data quality control before topic modeling or classification.
    
    Args:
        dict_adrs: Nested dictionary mapping org -> project -> ADR objects.
            ADR objects must implement get_content_no_code_str() method.
        min_adrs_per_project: Minimum number of ADRs required per project
            to be considered valid (default: 5). Additionally requires at least
            this many ADRs to meet min_adr_length threshold.
        min_adr_length: Minimum character count required for an ADR to be
            considered valid (default: 500). Empty or whitespace-only ADRs
            are also excluded.
    
    Returns:
        Dictionary with three keys:
            - 'all_projects': List of all (org, project) tuples found
            - 'filtered_projects': List of (org, project) tuples that were
              filtered out (failed thresholds)
            - 'valid_projects': List of (org, project) tuples that passed
              all validation checks
    
    Example:
        >>> result = process_projects(adrs_dict, min_adrs_per_project=3)
        >>> print(f"Valid projects: {len(result['valid_projects'])}")
        'Valid projects: 42'
    """
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
    """
    Convert DataFrame of labeled ADRs to list of dictionaries and optionally save to JSON.
    
    This function is useful for converting labeled datasets into the format
    expected by few-shot learning prompts. It strips quotes from ADR text
    and can save the result to a JSON file for reuse.
    
    Args:
        df: DataFrame containing ADR text and category labels.
            Must have columns specified by adr_column and category_column.
        filename: Path to output JSON file. If None, file is not saved.
            File will contain list of dicts with 'ADR' and 'Category' keys.
        adr_column: Name of column containing ADR text (default: 'text').
        category_column: Name of column containing category/label (default: 'human').
    
    Returns:
        List of dictionaries, each with keys:
            - 'ADR': The ADR text content with surrounding quotes stripped
            - 'Category': The category/label value
    
    Example:
        >>> df = pd.DataFrame({'text': ["'ADR content'", "'Another'"], 'human': ['A', 'B']})
        >>> examples = convert_sample_to_examples(df, 'examples.json')
        >>> print(examples[0])
        {'ADR': 'ADR content', 'Category': 'A'}
    """
    df = df.dropna(subset=[category_column, adr_column])
    list_dicts = []
    for index, row in df.iterrows():
        list_dicts.append({'ADR': row[adr_column].strip("'"), 'Category': row[category_column]})
    # Save to JSON file
    if filename is not None:
        with open(filename, "w") as f:
            json.dump(list_dicts, f, indent=4) # Using 'indent=4' makes the file human-readable
    return list_dicts

def prune_corpus(docs: dict) -> tuple[list[str], list[str]]:
    """
    Prune the corpus by removing empty or whitespace-only documents.
    
    This function cleans the document corpus by removing documents that are
    empty, contain only whitespace, or otherwise invalid. It also removes
    corresponding keys from the document dictionary to maintain consistency.
    
    Args:
        docs: Dictionary mapping (org, project, adr) tuples to document
            content strings. Keys must be 3-tuples.
    
    Returns:
        Tuple containing:
            - List of valid document content strings (pruned corpus)
            - List of valid (org, project, adr) tuples that correspond to
              documents in the pruned corpus
    
    Example:
        >>> docs = {('org1', 'proj1', 'ADR001'): 'Valid content',
        ...         ('org1', 'proj1', 'ADR002'): '   ',  # whitespace only
        ...         ('org1', 'proj1', 'ADR003'): ''}  # empty
        >>> corpus, keys = prune_corpus(docs)
        >>> print(f"Kept {len(corpus)} of {len(docs)} documents")
        'Kept 1 of 3 documents'
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
    """
    Display classification report as a heatmap.
    
    Visualizes sklearn classification report metrics (precision, recall, f1-score)
    as a color-coded heatmap, excluding the 'accuracy' row for clarity.
    
    Args:
        report_dict: Classification report dictionary from sklearn.metrics.classification_report()
            with output_dict=True. Should contain metrics like precision, recall, f1-score.
        title: Title for the plot (default: empty string).
        figsize: Figure size as (width, height) in inches (default: (8, 6)).
        cmap: Matplotlib colormap name for heatmap (default: "rocket_r").
            See matplotlib colormaps for options.
    
    Example:
        >>> from sklearn.metrics import classification_report
        >>> report = classification_report(y_true, y_pred, output_dict=True)
        >>> show_classification_report(report, title="Classification Results", cmap="YlGnBu")
    """
    plt.figure(figsize=figsize)
    sns.heatmap(pd.DataFrame(report_dict).iloc[:-1, :].T, annot=True, cmap=cmap)
    plt.title(title, fontsize=14)
    plt.show()


def show_confusion_matrix(confusion_df: pd.DataFrame, cmap='Greens', title="", figsize=(8,6), normalized=False):
    """
    Display confusion matrix as a heatmap.
    
    Visualizes classification performance with a confusion matrix, optionally
    normalized to show proportions instead of counts. Normalized view helps
    identify class imbalance effects.
    
    Args:
        confusion_df: Confusion matrix as pandas DataFrame. Should have true
            labels as index and predicted labels as columns.
        cmap: Matplotlib colormap name for heatmap (default: 'Greens').
        title: Title for the plot (default: empty string).
        figsize: Figure size as (width, height) in inches (default: (8, 6)).
        normalized: If True, normalize the confusion matrix to show proportions
            per true class (row-normalization). If False, show raw counts.
    
    Example:
        >>> from sklearn.metrics import confusion_matrix
        >>> cm = confusion_matrix(y_true, y_pred)
        >>> cm_df = pd.DataFrame(cm, index=classes, columns=classes)
        >>> show_confusion_matrix(cm_df, title="Confusion Matrix", normalized=True)
    """
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
    """
    Display horizontal bar chart of category frequencies.
    
    Visualizes the distribution of target categories with their relative
    frequencies as percentages. Supports custom color schemes or generates
    default colors using matplotlib's Set3 colormap.
    
    Args:
        target_values: Pandas Series containing categorical target values.
            Will be converted to value counts normalized to 0-1 range.
        color_dict: Dictionary mapping category names to color hex codes.
            If None, generates colors automatically using Set3 colormap.
            Returned for reuse in other visualizations.
        title: Title for the plot (default: "Frequencies of Categories (Target)").
        figsize: Figure size as (width, height) in inches (default: (7, 4)).
        width: Width of bars in bar chart (default: 0.6).
    
    Returns:
        Dictionary mapping category names to color hex codes. This can be
        passed to other visualization functions to maintain color consistency.
    
    Example:
        >>> colors = show_target_frequencies(y_train, title="Training Set Distribution")
        >>> show_umap_projection(y_test, embeddings_test, color_dict=colors)
    """
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
    """
    Display UMAP 2D projection of embeddings colored by target values.
    
    Visualizes high-dimensional embeddings in 2D space using UMAP dimensionality
    reduction. Points are colored by their target category, making it easy to
    see clustering and separation between classes. Prints count of points per class.
    
    Args:
        target_values: Pandas Series containing categorical labels for each embedding.
        embeddings: Array-like object of shape (n_samples, n_features) containing
            the high-dimensional embeddings to project.
        color_dict: Dictionary mapping category names to color hex codes.
            If None, generates colors automatically using Set3 colormap.
            Returned for reuse in other visualizations.
        figsize: Figure size as (width, height) in inches (default: (8, 8)).
        title: Title for the plot (default: empty string).
        s: Size of scatter points in matplotlib units (default: 50).
        alpha: Transparency of scatter points (0-1) (default: 0.6).
    
    Returns:
        Dictionary mapping category names to color hex codes. This can be
        passed to other visualization functions to maintain color consistency.
    
    Example:
        >>> from umap import UMAP
        >>> colors = show_umap_projection(y_train, train_embeddings,
        ...                                 title="UMAP Projection", alpha=0.7)
        >>> show_target_frequencies(y_test, color_dict=colors)
    """
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
    """
    Display classification results as a mosaic plot.
    
    Creates a mosaic plot visualization of a confusion matrix, showing the
    relationship between actual and predicted classes. The mosaic representation
    makes it easy to identify patterns in misclassifications and class
    relationships. Handles empty rows by adding placeholder blocks.
    
    Args:
        cm: Confusion matrix (numpy array or list of lists) where cm[i][j]
            represents the count of samples with true label i predicted as label j.
        cm_labels: List of class label names/identifiers. Will be sorted
            alphabetically for consistent display.
        color_dict: Dictionary mapping class names to color hex codes.
            If None, generates colors automatically using Set3 colormap.
            Returned for reuse in other visualizations.
        x_labels_colored: If True, color x-axis labels to match their
            corresponding class colors (default: True).
        title: Title for the plot (default: empty string).
        figsize: Figure size as (width, height) in inches (default: (11, 10)).
    
    Returns:
        Dictionary mapping class names to color hex codes. This can be
        passed to other visualization functions to maintain color consistency.
    
    Example:
        >>> from sklearn.metrics import confusion_matrix
        >>> cm = confusion_matrix(y_true, y_pred)
        >>> classes = ['Architecture', 'Database', 'Security']
        >>> colors = show_classification_mosaic(cm, classes,
        ...                                    title="Classification Mosaic")
        >>> show_target_frequencies(y_train, color_dict=colors)
    """
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

    # TODO: read by "rows", and if all values are 0, then add a black rectangle
    def chunker(iterable, k):
        """Yields chunks of k elements from an iterable."""
        for i in range(0, len(iterable), k):
            yield iterable[i:i + k]
    
    # Create chunk iterators for both lists
    chunks1 = chunker(list(props.keys()), n_classes)
    chunks2 = chunker(list(data.keys()), n_classes) 

    # Zip the chunks and iterate
    for chunk_l1, chunk_l2 in zip(chunks1, chunks2):
        # print(f"Chunk from list1: {chunk_l1}")
        # print(f"Chunk from list2: {chunk_l2}")
        # If the whole "row" has zero proportions, then artificially mark the first one a 1 and set a black color as the default
        if all(data[key] == 0 for key in chunk_l2): 
            props[chunk_l1[0]] = {'color': 'black'}
            data[chunk_l2[0]] = 1

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
