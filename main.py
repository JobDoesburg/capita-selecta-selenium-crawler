from os.path import exists
import argparse
import csv
import json

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

def parse_args():
    parser = argparse.ArgumentParser(description='The most awesome Selenium Capita Selecta crawler')
    parser.add_argument('-m', help='mobile or desktop')
    parser.add_argument('-u', help='single URL to crawl, this takes precedent over the -i option')
    parser.add_argument('-i', help='path to CSV with domains to crawl')

    args = parser.parse_args()

    if args.m:
        assert args.m == 'mobile' or args.m == 'desktop'

    print(args)
    return args

def create_json(url):
    data = {'website_domain': url,
            'crawl_mode': "desktop"}
    print(data)
    test = "google.com"
    with open('%s_desktop.json' %test, 'w') as outfile:
        json.dump(data, outfile)

def crawl_url(url):
    driver = webdriver.Chrome()
    driver.get(url)
    elem = driver.find_element(by=By.NAME, value="q")
    elem.clear()
    driver.close()
    create_json(url)

def crawl_list(urls):
    print(urls)

def main():
    args = parse_args()

    if args.u:
        crawl_url(args.u)
    elif args.i:
        assert exists(args.i)
        with open(args.i, 'r', newline='') as urls_csv:
            reader = csv.reader(urls_csv)
            urls_with_ranks = list(reader)[1:] # Skip header
            crawl_list(urls_with_ranks)

if __name__ == '__main__':
    main()
