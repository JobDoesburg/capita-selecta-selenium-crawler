from os.path import exists
import argparse
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By


def parse_args():
    parser = argparse.ArgumentParser(
        description="The most awesome Selenium Capita Selecta crawler"
    )
    parser.add_argument("-m", help="mobile or desktop")
    parser.add_argument(
        "-u", help="single URL to crawl, this takes precedent over the -i option"
    )
    parser.add_argument("-i", help="path to CSV with domains to crawl")

    args = parser.parse_args()

    if args.m:
        assert args.m == "mobile" or args.m == "desktop"

    return args


def crawl_url(url):
    driver = webdriver.Chrome()
    driver.get(url)
    elem = driver.find_element(by=By.NAME, value="q")
    elem.clear()
    driver.close()


def crawl_list(urls):
    print(urls)


def main():
    args = parse_args()

    if args.u:
        crawl_url(args.u)
    elif args.i:
        assert exists(args.i)
        with open(args.i, "r", newline="") as urls_csv:
            reader = csv.reader(urls_csv)
            urls_with_ranks = list(reader)[1:]  # Skip header
            crawl_list(urls_with_ranks)


if __name__ == "__main__":
    main()
