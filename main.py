import argparse

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

def crawl_url(URL):
    driver = webdriver.Chrome()
    driver.get(URL)
    elem = driver.find_element(by=By.NAME, value="q")
    elem.clear()
    driver.close()

def crawl_list(urls):
    pass

def main():
    args = parse_args()

    if args.u:
        crawl_url(args.u)
    elif args.i:
        # TODO: Open CSV and crawl all URLS
        pass

if __name__ == '__main__':
    main()
