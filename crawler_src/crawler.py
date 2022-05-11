from os import path

from tld import get_fld
import logging
import time
import json
import base64
from urllib.parse import urlparse

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


def check_certificate_host(url, certificate):
    """
    Check if the certificate is valid for this url. See RFC 2818.
    :param url: the url to verify against
    :param certificate: the certificate that is presented
    :return: True if the certificate is valid for this url, or false if it is the wrong host
    """
    full_domain = urlparse(url).netloc.split(".")
    cert_domain = certificate["cn"].decode("utf-8").split(".")

    while len(full_domain) > 0:
        full_domain_part = full_domain.pop()
        try:
            cert_domain_part = cert_domain.pop()
        except IndexError:
            return False
        if cert_domain_part is None or (
            cert_domain_part != "*" and cert_domain_part != full_domain_part
        ):
            return False

    if len(cert_domain) == 0 or cert_domain[0] == "*":
        return True

    return False


def get_certificate_issuer_cn(cert):
    """
    Get the issuer CN of a certificate
    :param cert: the certificate
    :return: the issuer CN
    """
    for key, val in cert["issuer"]:
        if key == b"CN":
            return val


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

        desired_capabilities = {"acceptInsecureCerts": True, "pageLoadStrategy": "eager"}
        self.driver = webdriver.Chrome(
            options=chrome_options, desired_capabilities=desired_capabilities
        )

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
                # TODO: Fix (the object does not appear to have repsonse headers)
                # "response_headers": dict(
                #     shorten_http_headers(request.response.headers)
                # ),
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

    def prepare_canvas_capture(self):
        file_path = path.join(path.dirname(path.abspath(__file__)), './js/HTMLCanvasElement.js')
        with open(file_path, 'r') as file:
            js = file.read().replace('\n', '')

        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': js})

    def capture_canvas_images(self):
        images = self.driver.find_elements_by_class_name("canvas_img_crawler")

        output = []
        for i, image in enumerate(images):
            header, img_base64 = image.get_attribute('src').split(',')
            resource_url = image.get_attribute('resource_url')

            extension = 'png'
            if 'jpeg' in header or 'jpg' in header:
                extension = 'jpg'

            img_decoded = base64.b64decode(img_base64)

            file_path = path.join(self.output_dir, f"{self.output_file_prefix}_canvas_capture_{i}.{extension}")
            with open(file_path, 'wb') as file:
                file.write(img_decoded)

            output.append({
                'canvas_fingerprint_image': f"{self.output_file_prefix}_canvas_capture_{i}.{extension}",
                'fingerprint_script_resource_url': resource_url
            })

        return output

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
        logging.info(f'Crawl start: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')
        self.current_url = url
        self.prepare_canvas_capture()

        # Compute the time it takes to load the page
        start_time = time.mktime(time.localtime())
        self.driver.get(url)
        end_time = time.mktime(time.localtime())

        post_pageload_url = self.driver.current_url

        if len(self.driver.requests) == 0:
            logging.error("Timeout")
            return

        first_request = self.driver.requests[0]
        # Note, this does not always result in the correct request.
        # In headful mode, Chrome can add additional requests here.
        # Also think about 301/302 responses

        certificate = first_request.cert

        if first_request.response is None:
            logging.warning("Domain doesn't exist")
            return

        if certificate["expired"] is True:
            logging.warning("SSL certificate is expired")

        if certificate["cn"] == get_certificate_issuer_cn(certificate):
            logging.warning("Self signed certificate")

        if not check_certificate_host(self.current_url, certificate):
            logging.warning("Wrong host")

        canvas_image_data = self.capture_canvas_images()
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
            "post_pageload_url": post_pageload_url,
            "pageload_start_ts": start_time,
            "pageload_end_ts": end_time,
            "consent_status": None,
            "requests": requests,
            "load_time": end_time - start_time,
            "cookies": cookies,
            "canvas_image_data": canvas_image_data
        }
        self.create_json(output)

    def crawl_urls(self, urls):
        """
        Crawls a list of urls.
        :param urls: The urls to crawl.
        """
        for url in urls:
            self.crawl_url(url)
