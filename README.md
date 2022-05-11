# Capita Selecta Selenium Crawler

### Set up

0. Use python version 3.9.7 (or something else at your own risk)
1. Create venv: `python -m venv venv`
2. Activate venv: `source venv/bin/activate`
3. Install deps: `pip install -r requirements.txt`
4. Install chromedriver:
   1. For macOS: `brew install --cask chromedriver`


### Run a crawl
- `main.py -i crawler_src/tranco-top-500-safe.csv` to run a crawl on the tranco-top-500 dataset
- `main.py -u https://google.com/` for a single domain.

Use `main.py -h` to see all options.