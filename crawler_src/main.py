from os import path
import argparse
import csv
from tld import get_fld
import logging
import time
import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

DATA_PATH = path.join(path.join(path.dirname(path.abspath(__file__)),
                                '..'),
                      'crawl_data')
LOGNAME = "crawl.log"
logging.basicConfig(filename=path.join(DATA_PATH, LOGNAME), level=logging.INFO)


def parse_args():
    """
    Parses the command line arguments and validates the input

    Returns: arguments
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


def create_json(crawler_output, filename):
    """
    Create a json file containing crawler output

    Parameters:
    crawler_output

    """
    with open('%s.json' %filename, 'w') as outfile:
        json.dump(crawler_output, outfile)


def crawl_url(url, output_dir='', mobile=False, headless=False):
    """
    Crawls a single url

    Parameters:
    url (string): The url to crawl
    output_dir (string): The output directory for the files
    mobile (bool): Run with a mobile client
    headless (bool): To run in headless mode
    """

    fld = get_fld(url)
    output_filename = f"{output_dir}{fld}_{'mobile' if mobile else 'desktop'}_"
    output_filename = path.join(DATA_PATH, output_filename)

    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    if mobile:
        mobile_emulation = {"deviceName": "Nexus 5"}
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    driver = webdriver.Chrome(options=chrome_options)
    logging.info(f'Crawl start: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')

    driver.get(url)
    create_screenshot(driver, output_filename, mobile=mobile)
    cookies = driver.get_cookies()
    create_screenshot(driver, output_filename, mobile=mobile, post_consent=True)

    driver.close()
    logging.info(f'Crawl end: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')
    output = {
        "website_domain": None,
        "crawl_mode": None,
        "post_pageload_url": None,
        "pageload_start_ts": None,
        "pageload_end_ts": None,
        "consent_status": None,
        "requests": [None],
        "load_time": None,
        "cookies": cookies,
    }
    
    create_json(output, output_filename)


def crawl_list(urls):
    """
    Crawls a list of urls

    urls (list[string]): The urls
    """
    logging.info(f'Crawl start: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')
    print(urls)
    logging.info(f'Crawl end: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')


def create_screenshot(driver, output_filename, mobile=False, post_consent=False):
    """
    Create a screenshot and save it

    Parameters:
    driver (object): Webdriver
    output_filename (string): The base location to save the ss
    post_consent (bool): Pre or post accepting cookies
    """

    filename = output_filename + f"{'mobile' if mobile else 'desktop'}_{'post' if post_consent else 'pre'}_consent.png"
    driver.save_screenshot(filename)


def main():
    """Main function"""

    args = parse_args()
    headless = bool(not args.H or (args.H and args.H == "headless"))
    mobile = bool(args.m and args.m == "mobile")

    if args.u:
        crawl_url(args.u, headless=headless, mobile=mobile)
    elif args.i:
        assert path.exists(args.i)
        with open(args.i, "r", newline="") as urls_csv:
            reader = csv.reader(urls_csv)
            urls_with_ranks = list(reader)[1:]  # Skip header
            crawl_list(urls_with_ranks)


if __name__ == "__main__":
    main()
