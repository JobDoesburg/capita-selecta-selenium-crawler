import signal
from os import path

import tqdm
from tld import get_fld
import logging
import time
import json
import base64

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchFrameException
from selenium.common.exceptions import WebDriverException

from exceptions import *
from utils import *


class Crawler:
    def __init__(
        self,
        headless=True,
        mobile=False,
        output_dir="crawl_data",
        pageload_timeout=30,
        js_load_wait=5,
    ):
        """
        Initializes the crawler.
        :param headless: run the browser headless or not
        :param mobile: run the browser as mobile device
        :param output_dir: folder to put the output files
        """
        self.timeout = pageload_timeout
        self.js_load_wait = js_load_wait

        self.headless = headless
        self.mobile = mobile
        self.output_dir = output_dir

        self.__init_consent_accept_words_list()
        self.__init_fingerprint_canvas()

        self.current_url = None

        self.errored_urls = []

        self.start_driver()

    def __init_consent_accept_words_list(self):
        """Initialize a list with words to consider as consent window accept words."""
        self.consent_accept_words = set()
        file_path = path.join(path.dirname(path.abspath(__file__)), "accept_words.txt")
        with open(file_path, "r", encoding="utf-8") as accept_words_file:
            lines = accept_words_file.read().splitlines()
        for w in lines:
            if not w.startswith("#") and not w == "":
                self.consent_accept_words.add(w)

    def __init_fingerprint_canvas(self):
        """Initialize a javascript file to detect fingerprinting."""
        file_path = path.join(
            path.dirname(path.abspath(__file__)), "./js/HTMLCanvasElement.js"
        )
        with open(file_path, "r") as file:
            self.fingerprint_html_canvas_element_js = file.read().replace("\n", "")

    @property
    def crawl_mode(self):
        return "mobile" if self.mobile else "desktop"

    @property
    def current_domain(self):
        return get_fld(self.current_url)

    @property
    def output_file_prefix(self):
        return f"{self.current_domain}_{self.crawl_mode}"

    def start_driver(self):
        """Start a Chrome browser instance."""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Don't reveal you're a crawler
        if self.mobile:
            mobile_emulation = {"deviceName": "Nexus 6P"}
            chrome_options.add_argument(
                '--user-agent="Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.78 Mobile Safari/537.36"'
            )
            chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        else:
            chrome_options.add_argument(
                '--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36"'
            )

        desired_capabilities = {
            "acceptInsecureCerts": True,
            "pageLoadStrategy": "eager",
        }
        seleniumwire_options = {
            "request_storage": "memory",
        }  # Use in-memory storage because it is more optimal

        self.driver = webdriver.Chrome(
            options=chrome_options,
            seleniumwire_options=seleniumwire_options,
            desired_capabilities=desired_capabilities,
        )
        self.driver.set_page_load_timeout(self.timeout)

        if not self.mobile:
            self.driver.set_window_size(1440, 900)

    def stop_driver(self):
        """Close the driver"""
        self.driver.stop_client()
        self.driver.get("about:blank")
        self.driver.delete_all_cookies()
        del self.driver.requests
        self.driver.start_client()

    def _get_requests(self):
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
                "response_status_code": request.response.status_code
                if request.response
                else None,
                "response_headers": dict(shorten_http_headers(request.response.headers))
                if request.response
                else None,
            }
            requests.append(request_data)
        return requests

    def _create_screenshot(self, post_consent=False):
        """
        Create a screenshot and save it.
        :param post_consent: Pre or post accepting cookies
        """
        filename = (
            f"{self.output_file_prefix}_{'post' if post_consent else 'pre'}_consent.png"
        )
        filename = path.join(self.output_dir, filename)

        self.driver.save_screenshot(filename)

    def _create_json(self, output):
        """
        Create a json file containing crawler output.
        :param output: output data
        """
        filename = path.join(self.output_dir, f"{self.output_file_prefix}.json")
        with open(filename, "w") as outfile:
            json.dump(output, outfile, indent=4)

    def _prepare_fingerprint_canvas_capture(self):
        """Execute CDP command for detecting canvas fingerprinting."""
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": self.fingerprint_html_canvas_element_js},
        )

    def _capture_fingerprint_canvas_images(self):
        """Detect canvas fingerprinting."""
        images = self.driver.find_elements_by_class_name("canvas_img_crawler")

        output = []
        for i, image in enumerate(images):
            img_src = image.get_attribute("src")
            if not img_src:
                continue

            header, img_base64 = img_src.split(",")
            resource_url = image.get_attribute("resource_url")

            extension = "png"
            if "jpeg" in header or "jpg" in header:
                extension = "jpg"

            img_decoded = base64.b64decode(img_base64)

            file_path = path.join(
                self.output_dir,
                f"{self.output_file_prefix}_canvas_capture_{i}.{extension}",
            )
            with open(file_path, "wb") as file:
                file.write(img_decoded)

            output.append(
                {
                    "canvas_fingerprint_image": f"{self.output_file_prefix}_canvas_capture_{i}.{extension}",
                    "fingerprint_script_resource_url": resource_url,
                }
            )

        return output

    def __click_consent_banner(self):
        """
        Click on a consent accept banner element.
        :return: whether an element was clicked
        """
        contents = self.driver.find_elements_by_css_selector(
            "a, button, div, span, form, p, input[type=button]"
        )

        candidate = None

        for c in contents:
            if c.text.lower().strip(" ✓›!\n") in self.consent_accept_words:
                candidate = c
                break

        if candidate is not None:
            candidate.click()
            return True

        logging.info("No consent accept element was found")
        return None

    def _accept_consent(self):
        """
        Try to accept a privacy consent popup.
        :return: whether an element was clicked
        """
        element_clicked = self.__click_consent_banner()

        if element_clicked:
            # Also try windows in iframes
            iframe_contents = self.driver.find_elements_by_css_selector("iframe")
            for content in iframe_contents:
                try:
                    self.driver.switch_to.frame(content)
                    element_clicked = self.__click_consent_banner()
                    self.driver.switch_to.default_content()
                    if element_clicked:
                        break
                except NoSuchFrameException:
                    self.driver.switch_to.default_content()
                    logging.info(
                        "Error occurred in switching to iframe for accepting consent"
                    )

        if not element_clicked:
            logging.info(f"No consent banner found.")
            return element_clicked

        time.sleep(2)
        logging.info(f"URL after accepting consent: {self.driver.current_url}")

        return element_clicked

    def _load_page_first_time(self, url):
        """
        Loads a single url.
        :param url: The url
        """
        self.current_url = url
        self._prepare_fingerprint_canvas_capture()

        try:
            self.driver.get(url)
        except WebDriverException:
            raise TimeoutError()

        if len(self.driver.requests) == 0:
            raise TimeoutError()

        first_request = self.driver.requests[0]
        # Note, this does not always result in the correct request.
        # In headful mode, Chrome can add additional requests here.
        # Also think about 301/302 responses

        if first_request.response is None:
            logging.warning("Domain doesn't exist")
            raise DomainDoesNotExist()

        certificate = first_request.cert
        if certificate["expired"] is True:
            raise CertificateExpired()

        def get_certificate_issuer_cn(cert):
            for key, val in cert["issuer"]:
                if key == b"CN":
                    return val

        if certificate["cn"] == get_certificate_issuer_cn(certificate):
            raise SelfSignedCertificate()

        if not check_certificate_host(self.current_url, certificate):
            raise WrongHostCertificate()

    def _handle_page(self):
        """
        Interact with a page that is loaded by the crawler: try to accept consent and detect fingerprinting.
        """
        time.sleep(self.js_load_wait)
        self._create_screenshot()
        try:
            consent_clicked = self._accept_consent()
            consent_failure = False
        except Exception as e:
            logging.warning(f"Accepting tracking caused crash. Exception: {e}")
            consent_clicked = False
            consent_failure = True

        if consent_clicked:
            time.sleep(self.js_load_wait)
            self._create_screenshot(post_consent=True)

        post_pageload_url = self.driver.current_url
        canvas_image_data = self._capture_fingerprint_canvas_images()
        requests = self._get_requests()
        cookies = self.driver.get_cookies()

        return (
            post_pageload_url,
            requests,
            cookies,
            canvas_image_data,
            consent_clicked,
            consent_failure,
        )

    def crawl_url(self, url, rank=None):
        """
        Crawls a single url.
        :param url: The url to crawl
        :param rank: the rank of the url to include in the output
        """
        logging.info(f'Start crawling {self.current_url}: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')
        tls_failure = None

        start_time = time.mktime(time.localtime())

        try:
            self._load_page_first_time(url)
        except DomainDoesNotExist:
            logging.error(f"Domain {self.current_url} does not exist. Skipping this domain.")
            self.errored_urls.append(self.current_url)
            self.stop_driver()
            return
        except TimeoutError:
            logging.error(f"Timeout occurred during crawling of {self.current_url}")
            self.errored_urls.append(self.current_url)
            output = {
                "website_domain": self.current_domain,
                "rank": rank,
                "crawl_mode": self.crawl_mode,
                "post_pageload_url": None,
                "pageload_start_ts": None,
                "pageload_end_ts": None,
                "consent_status": None,
                "requests": [],
                "load_time": None,
                "cookies": None,
                "canvas_image_data": None,
                "failure_status": {
                    "timeout": True,
                    "TLS": None,
                    "consent": False,
                },
            }
            self._create_json(output)
            self.stop_driver()
            return
        except TLSError as e:
            tls_failure = str(e)
            logging.warning(f"TLS error occurred: {tls_failure}")

        end_time = time.mktime(time.localtime())

        (
            post_pageload_url,
            requests,
            cookies,
            canvas_image_data,
            consent_clicked,
            consent_failure,
        ) = self._handle_page()

        logging.info(f'Crawl end: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')

        if consent_failure:
            consent_status = "errored"
        elif consent_clicked:
            consent_status = "clicked"
        else:
            consent_status = "not_found"

        output = {
            "website_domain": self.current_domain,
            "rank": rank,
            "crawl_mode": self.crawl_mode,
            "post_pageload_url": post_pageload_url,
            "pageload_start_ts": start_time,
            "pageload_end_ts": end_time,
            "consent_status": consent_status,
            "requests": requests,
            "load_time": end_time - start_time,
            "cookies": cookies,
            "canvas_image_data": canvas_image_data,
            "consent_clicked": consent_clicked,
            "failure_status": {
                "timeout": False,
                "TLS": str(tls_failure) if tls_failure else None,
                "consent": consent_failure,
            },
        }
        self._create_json(output)
        self.stop_driver()

    def crawl_urls(self, urls):
        """
        Crawls a list of urls.
        :param urls: The urls to crawl.
        """
        with tqdm.tqdm(urls) as urls_progress:
            for i, url in urls_progress:
                url = f"https://{url}"
                urls_progress.set_description(f"Crawling {url}")
                try:
                    self.crawl_url(url, rank=i)
                except Exception as e:
                    logging.error(f"Something went wrong during crawling of {url}: {e}")
                    self.errored_urls.append(self.current_url)
                    continue

        print(f"Errored urls: {self.errored_urls}")
