from os import path

from tld import get_fld
import logging
import time
import json

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options


def shorten_http_headers(headers):
    """
    Shorten header values to 512 characters
    :return: HTTPheaders object with shortened header values
    """
    for key in headers:
        value = headers[key]
        if len(value) > 512:
            del headers[key]
            headers[key] = value[0:512]
    return headers


class Crawler:
    def __init__(self, headless=True, mobile=False, output_dir="crawl_data"):
        """
        Initializes the crawler
        :param headless: run the browser headless or not
        :param mobile: run the browser as mobile device
        :param output_dir: folder to put the output files
        """
        self.headless = headless
        self.mobile = mobile
        self.output_dir = output_dir

        self.current_url = None

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        if self.mobile:
            mobile_emulation = {"deviceName": "Nexus 5"}
            chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        self.driver = webdriver.Chrome(options=chrome_options)

    @property
    def crawl_mode(self):
        return "mobile" if self.mobile else "desktop"

    @property
    def current_domain(self):
        return get_fld(self.current_url)

    @property
    def output_file_prefix(self):
        return f"{self.current_domain}_{self.crawl_mode}"

    def get_requests(self):
        """
        Get the HTTP requests and responses including URL, time and headers.
        :return: All HTTP requests that were created.
        """
        requests = []

        for request in self.driver.requests:
            request_data = {
                "request_url": request.url,
                "time": request.date.timestamp(),
                "request_headers": dict(shorten_http_headers(request.headers)),
                "response_headers": dict(shorten_http_headers(request.response.headers)),
            }
            requests.append(request_data)
        return requests

    def create_screenshot(self, post_consent=False):
        """
        Create a screenshot and save it.
        :param post_consent: Pre or post accepting cookies
        """
        filename = (
            f"{self.output_file_prefix}_{'post' if post_consent else 'pre'}_consent.png"
        )
        filename = path.join(self.output_dir, filename)

        self.driver.save_screenshot(filename)

    def create_json(self, output):
        """
        Create a json file containing crawler output
        :param output: output data
        """
        filename = path.join(self.output_dir, f"{self.output_file_prefix}.json")
        with open(filename, "w") as outfile:
            json.dump(output, outfile, indent=4)

    def crawl_url(self, url):
        """
        Crawls a single url
        :param url: The url to crawl
        """
        self.current_url = url

        logging.info(f'Crawl start: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')
        self.driver.get(url)

        self.create_screenshot()

        requests = self.get_requests()
        cookies = self.driver.get_cookies()

        # TODO: accept cookies

        self.create_screenshot(post_consent=True)

        self.driver.close()
        logging.info(f'Crawl end: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')

        output = {
            "website_domain": self.current_domain,
            "crawl_mode": self.crawl_mode,
            "post_pageload_url": None,
            "pageload_start_ts": None,
            "pageload_end_ts": None,
            "consent_status": None,
            "requests": requests,
            "load_time": None,
            "cookies": cookies,
        }
        self.create_json(output)

    def crawl_urls(self, urls):
        """
        Crawls a list of urls.
        :param urls: The urls to crawl.
        """
        for url in urls:
            self.crawl_url(url)
