from os.path import exists
import argparse
import csv
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

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

def crawl_url(URL):
    driver = webdriver.Chrome()
    driver.get(URL)
    elem = driver.find_element_by_name("q")
    elem.clear()
    driver.close()

def crawl_list(URLS):
    print(URLS)

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
