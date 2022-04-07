from os.path import exists
import argparse
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def parse_args():
    '''
    Parses the command line arguments and validates the input

    Returns: arguments
    '''
    parser = argparse.ArgumentParser(
        description="The most awesome Selenium Capita Selecta crawler"
    )
    parser.add_argument("-m", help="mobile or desktop")
    parser.add_argument(
        "-u", help="single URL to crawl, this takes precedent over the -i option"
    )
    parser.add_argument("-i", help="path to CSV with domains to crawl")
    parser.add_argument("-H", help="headless or headful (default is headless)")

    args = parser.parse_args()

    if args.m:
        assert args.m == "mobile" or args.m == "desktop"

    if args.H:
        assert args.H == "headless" or args.H == "headful"

    return args


def crawl_url(url, headless=False):
    '''
    Crawls a single url

    Parameters:
    url (string): The url to crawl
    headless (bool): To run in headless mode
    '''

    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    elem = driver.find_element(by=By.NAME, value="q")
    elem.clear()
    driver.close()


def crawl_list(urls):
    '''
    Crawls a list of urls

    urls (list[string]): The urls
    '''
    print(urls)


def main():
    ''' Main function '''

    args = parse_args()
    headless = bool(not args.H or (args.H and args.H == "headless"))
    if args.u:
        crawl_url(args.u, headless=headless)
    elif args.i:
        assert exists(args.i)
        with open(args.i, "r", newline="") as urls_csv:
            reader = csv.reader(urls_csv)
            urls_with_ranks = list(reader)[1:]  # Skip header
            crawl_list(urls_with_ranks)


if __name__ == "__main__":
    main()
