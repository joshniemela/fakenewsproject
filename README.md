# Fake News Project
Group 1 - shared repository related to the Fake News Project in Data Science 2023.  
The code has only been tested on Linux (Arch, NixOS, Fedora). The code will not work on Windows since the scripts use UNIX paths.

## Specs
The code was run on various machines, the large multithreaded tasks (tokenisation, TF-iDF, SVD, UMAP, etc.) and the XGBoost, small DNN, and logistic regression were all trained on the server with specs below. Other tasks (big DNN, SQL, data exploration, etc.) were done on two other machines.
### Server
- 40GiB RAM (2x8, 6x4), 20GiB of virtual compressed ram (ZRAM). DDR3 with 1333MHz clock.
- i7-3820 CPU
- p9x79 motherboard
### Arch machine
- 7.6GiB Ram, 2GiB swap
- Intel(R) Core(TM) i5-7200U CPU @ 2.50GHz

## Pipeline
In order to reproduce our pipeline on FakeNews dataset:
1. Run `download_data.sh` which downloads, extracts and removes carriage returns.
2. Enter the virtual python env by running `pipenv shell`
3. Go through the steps in `preprocess.ipynb`.
4. Choose which script to run, it being one of either:
   * `simple_model/simple_model.py`
   * `complex_models/bigdnn_complex.py`
   * `complex_models/dnn_complex.py`
   * `complex_models/xgboost_complex.py`

Some of these scripts require copious amounts of RAM, (+30 GiB)
However, `bigdnn_complex.py` (ironically) does everything in chunks, except when fitting the `tf-idf` vectoriser. This can however be done rather effectively on a single parquet file from test.parquet, making it possible to run train and predict this model on a low-resource computer, even using the entire dataset (which was done on the Arch machine). Other files such as `tokenise.py` exists as a headless alternative to some of the steps in the notebook so that it can be run in a terminal.

* Running `umap_fake.py`, or `umap_liar.py` produces beautiful unsupervised maps of the corpus.

## LIAR
To prepare dataset:
1. Run `liar/download_data.sh`
2. Run `liar/tokenise.py`

Now the liar dataset is ready and you can run `predict_on_liar.py` to check how to models perform on this out-of-domain data.

# Dependencies
`pipenv` is required to ensure that your python environment is the correct one.  
Nix flakes were used to install `pipenv` on our server. 
