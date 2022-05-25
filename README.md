# Capita Selecta Selenium Crawler

### Set up

0. Use python version 3.9.7 (or something else at your own risk)
1. Create venv: `python -m venv venv`
2. Activate venv: `source venv/bin/activate`
3. Install deps: `pip install -r requirements.txt`
4. Install chromedriver:
   1. For macOS: `brew install --cask chromedriver`
   2. For linux: https://skolo.online/documents/webscrapping/#step-2-install-chromedriver and use `weg https://chromedriver.storage.googleapis.com/101.0.4951.41/chromedriver_linux64.zip`, `unzip chromedriver_linux64.zip` and `ln -s ./chromedriver /usr/bin/chromedriver`


### Run a crawl
- `main.py -i crawler_src/tranco-top-500-safe.csv` to run a crawl on the tranco-top-500 dataset
- `main.py -u https://google.com/` for a single domain.

Use `main.py -h` to see all options.

### Run the analysis
- run `jupyter notebook` from the root of the project
    * Note: if you do not run this from the project root, the canvas images will load incorrectly
- open and run `analysis/analysis.ipynb`
