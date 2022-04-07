from os.path import exists
import argparse
import csv
<<<<<<< HEAD
import json
=======
from tld import get_fld
<<<<<<< HEAD
>>>>>>> 03cec468b152cd821a943b8acc99c160a97d3c2a
=======
import logging
import time
>>>>>>> aad38fd544a926ec5f4dc1dfae1e833d4084269b

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


LOGNAME = 'crawl.log'
logging.basicConfig(filename=LOGNAME, level=logging.INFO)


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

<<<<<<< HEAD
def create_json(url):
    data = {'website_domain': url,
            'crawl_mode': "desktop"}
    print(data)
    test = "google.com"
    with open('%s_desktop.json' %test, 'w') as outfile:
        json.dump(data, outfile)

def crawl_url(url):
    driver = webdriver.Chrome()
=======

def crawl_url(url, headless=False):
    """
    Crawls a single url

    Parameters:
    url (string): The url to crawl
    headless (bool): To run in headless mode
    """

    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
<<<<<<< HEAD

>>>>>>> 03cec468b152cd821a943b8acc99c160a97d3c2a
=======
    logging.info(f'Crawl start: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')
>>>>>>> aad38fd544a926ec5f4dc1dfae1e833d4084269b
    driver.get(url)
    create_screenshot(driver)
    cookies = driver.get_cookies()
    driver.close()
<<<<<<< HEAD
    create_json(url)
=======
    logging.info(f'Crawl end: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')
>>>>>>> aad38fd544a926ec5f4dc1dfae1e833d4084269b

    output = {
        'website_domain': None,
        'crawl_mode': None,
        'post_pageload_url': None,
        'pageload_start_ts': None,
        'pageload_end_ts': None,
        'consent_status': None,
        'requests': [None],
        'load_time': None,
        'cookies': cookies,
    }
    # TODO: Save the output here


def crawl_list(urls):
    """
    Crawls a list of urls

    urls (list[string]): The urls
    """
    logging.info(f'Crawl start: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')
    print(urls)
    logging.info(f'Crawl end: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')


def create_screenshot(driver, mobile=False, post_consent=False):
    fld = get_fld(driver.current_url)
    filename = f"{fld}_{'mobile' if mobile else 'desktop'}_{'post' if post_consent else 'pre'}_consent.png"
    driver.save_screenshot(filename)


def main():
    """Main function"""

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
