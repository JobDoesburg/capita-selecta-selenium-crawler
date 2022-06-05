# Capita Selecta Selenium Crawler

The crawler is written in Python and uses Selenium with Chrome. Selenium-wire is used for intercepting traffic.

### Set up

0. Use python version 3.9.7 (or something else at your own risk)
1. Create venv: `python -m venv venv`
2. Activate venv: `source venv/bin/activate`
3. Install deps: `pip install -r requirements.txt`
4. Install chromedriver:
   1. For macOS: `brew install --cask chromedriver`
   2. For linux: https://skolo.online/documents/webscrapping/#step-2-install-chromedriver and use `wget https://chromedriver.storage.googleapis.com/101.0.4951.41/chromedriver_linux64.zip`, `unzip chromedriver_linux64.zip` and `ln -s ./chromedriver /usr/bin/chromedriver`


### Run a crawl
- `main.py -i crawler_src/tranco-top-500-safe.csv` to run a crawl on the tranco-top-500 dataset
- `main.py -u https://google.com/` for a single domain.

Use `main.py -h` to see all options.

For running a crawl on a server, `screen` can be useful, and the command `python main.py -i crawler_src/tranco-top-500-safe.csv && python main.py -i crawler_src/tranco-top-500-safe.csv -m mobile` 

### Run the analysis
- run `jupyter notebook` from the root of the project
    * Note: if you do not run this from the project root, the canvas images will load incorrectly
- open and run `analysis/analysis.ipynb`
