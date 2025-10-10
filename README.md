# ADRminer

This is the reproducibility kit for the paper “_What do Architecture Decisions talk about? A Data Mining Study based on Open-source Repositories_”.
It provides the code, data, and notebooks necessary to replicate the experiments and analyses from the paper.

The main topics covered by the analyzed ADRs are displayed in the chart below.

![image](https://github.com/tommantonela/ADRminer/blob/main/adr-topics.png)

Alternatively, you can get an interactive view of the chart using [top20_adr_topics.html](https://htmlpreview.github.io/?https://github.com/tommantonela/ADRminer/blob/main/top20_adr_topics.html).

---

## Motivation

Software architecture decisions (ADRs) capture design rationale and decisions made during software evolution. Understanding what topics ADRs commonly discuss helps researchers and practitioners gain insight into architectural concerns, trade-offs, and patterns in open-source projects.
This repository enables reproducibility and further exploration of that study.

## Features & scope

* Mining and preprocessing of ADR documents from open-source repositories.
* Topic modeling and classification of ADR texts.
* Statistical analysis and visualization of extracted topics.
* Jupyter notebooks to replicate experiments and generate results.
* Visualization of top ADR topics (e.g., via topic charts).

## Repository organization

Here’s a quick description of key files:

* ``adr.py`` – Core Python module for ADR definision and processing.
* ``adr_llm_classification.ipynb`` – Notebook using language models to classify ADRs.
* ``adrs_bertopic.ipynb`` – Topic modeling and clustering via BERTopic.
* ``classification_analysis.ipynb`` – Analysis of classification results and evaluation.
* ``data/`` – Folder containing datasets used in experiments.
* ``top20_adr_topics.html`` – Interactive HTML version of the top-20 topic visualization.
* ``adr-topics.png`` – Static chart of the most frequent ADR topics.

Setup & Installation

1. _Clone the repository_

```bash
git clone https://github.com/tommantonela/ADRminer.git
cd ADRminer
```

2. _Create a virtual environment (recommended)_

```bash
python -m venv venv
source venv/bin/activate   # on Linux/macOS  
.\venv\Scripts\activate     # on Windows
```

3. _Install dependencies_

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. _(Optional) Download or prepare datasets_
   
Place any external datasets needed under the data/ folder, following the format used in the notebooks.


## Usage

You can replicate the experiments by running the Jupyter notebooks (in the order given). The notebooks include narrative explanations, code cells, and visual outputs.

Here’s a suggested workflow:

1. Start ``adrs_bertopic.ipynb`` to perform topic modeling on your ADR dataset.
2. Use ``adr_llm_classification.ipynb`` to classify ADRs using language models or other methods.
3. Explore ``classification_analysis.ipynb`` to analyze classification metrics, topic distributions, and comparative plots.

## Contributing

Contributions, improvements, issues, or suggestions are very welcome! Here are some ways you can help:

* Add support for new ADR datasets.
* Improve preprocessing (e.g. better text cleaning, embedding strategies).
* Experiment with alternate classification or topic modeling methods.
* Fix bugs, improve documentation, or enhance visualizations.

Feel free to open issues or submit pull requests.

## License
This project is licensed under the Apache License 2.0.
