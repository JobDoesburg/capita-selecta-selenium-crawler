import os
from os import path, makedirs
import argparse
import csv
import logging

from crawler_src.crawler import Crawler

DATA_PATH = path.join(path.dirname(path.abspath(__file__)), "..", "crawl_data")
if not path.exists(DATA_PATH):
    makedirs(DATA_PATH)

LOGNAME = "crawl.log"
logging.basicConfig(filename=path.join(DATA_PATH, LOGNAME), level=logging.INFO)


def parse_args():
    """
    Parses the command line arguments and validates the input.
    :return: arguments
    """

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


def main():
    args = parse_args()
    headless = bool(not args.H or (args.H and args.H == "headless"))
    mobile = bool(args.m and args.m == "mobile")

    crawler = Crawler(
        headless=headless, mobile=mobile, output_dir=os.path.abspath(DATA_PATH)
    )

    if args.u:
        url = args.u
        crawler.crawl_url(url)
    elif args.i:
        assert path.exists(args.i)
        with open(args.i, "r", newline="") as urls_csv:
            reader = csv.reader(urls_csv)
            urls_with_ranks = list(reader)[1:]  # Skip header
            crawler.crawl_urls(urls_with_ranks)


if __name__ == "__main__":
    main()
