from os import path

import tqdm
from tld import get_fld
import logging
import time
import json
import base64
from urllib.parse import urlparse

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchFrameException
from selenium.common.exceptions import WebDriverException

GLOBAL_SELECTOR = "a, button, div, span, form, p"
ACCEPTWORDS = path.join(path.dirname(path.abspath(__file__)), "accept_words.txt")
TRY_SCROLL = True


def get_signature(element):
    def props_to_dict(e):
        props = {"tag": e.tag_name}
        for attr in e.get_property("attributes"):
            props[attr["name"]] = attr["value"]
        return props

    signature = []
    current = element
    while True:
        signature.insert(0, props_to_dict(current))

        if current.tag_name == "html":
            break
        current = current.find_element(by="XPATH", value="..")
        if current is None:
            break

    return signature


class DomainDoesNotExist(Exception):
    pass


class TLSError(Exception):
    pass


class SelfSignedCertificate(TLSError):
    def __str__(self):
        return "Self-signed certificate"


class WrongHostCertificate(TLSError):
    def __str__(self):
        return "Wrong host certificate"


class CertificateExpired(TLSError):
    def __str__(self):
        return "Certificate expired"


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
            if full_domain_part == "www" and len(full_domain) == 0:
                return True
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
    def __init__(
        self,
        headless=True,
        mobile=False,
        output_dir="crawl_data",
        pageload_timeout=10,
        js_load_wait=10,
    ):
        """
        Initializes the crawler
        :param headless: run the browser headless or not
        :param mobile: run the browser as mobile device
        :param output_dir: folder to put the output files
        """
        self.timeout = pageload_timeout
        self.js_load_wait = js_load_wait

        self.headless = headless
        self.mobile = mobile
        self.output_dir = output_dir

        self.current_url = None
        self.driver = None

    def start_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        if self.mobile:
            mobile_emulation = {"deviceName": "Nexus 5"}
            chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

        desired_capabilities = {
            "acceptInsecureCerts": True,
            "pageLoadStrategy": "eager",
        }
        self.driver = webdriver.Chrome(
            options=chrome_options, desired_capabilities=desired_capabilities
        )
        self.driver.set_page_load_timeout(self.timeout)

        if not self.mobile:
            self.driver.set_window_size(1366,768)

    @property
    def crawl_mode(self):
        return "mobile" if self.mobile else "desktop"

    @property
    def current_domain(self):
        return get_fld(self.current_url)

    @property
    def output_file_prefix(self):
        return f"{self.current_domain}_{self.crawl_mode}"

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
                "response_status_code": request.response.status_code,
                "response_headers": dict(
                    shorten_http_headers(request.response.headers)
                ),
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
        Create a json file containing crawler output
        :param output: output data
        """
        filename = path.join(self.output_dir, f"{self.output_file_prefix}.json")
        with open(filename, "w") as outfile:
            json.dump(output, outfile, indent=4)

    def _prepare_canvas_capture(self):
        file_path = path.join(
            path.dirname(path.abspath(__file__)), "./js/HTMLCanvasElement.js"
        )
        with open(file_path, "r") as file:
            js = file.read().replace("\n", "")

        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument", {"source": js}
        )

    def _capture_canvas_images(self):
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

    def __click_banner(self):
        accept_words_list = set()
        with open(ACCEPTWORDS, "r", encoding="utf-8") as accept_words_file:
            lines = accept_words_file.read().splitlines()
        for w in lines:
            if not w.startswith("#") and not w == "":
                accept_words_list.add(w)

        banner_data_return = {"matched_containers": [], "candidate_elements": []}
        contents = self.driver.find_elements_by_css_selector(GLOBAL_SELECTOR)

        candidate = None

        for c in contents:
            try:
                if c.text.lower().strip(" ✓›!\n") in accept_words_list:
                    candidate = c
                    banner_data_return["candidate_elements"].append(
                        {
                            "id": c.id,
                            "tag_name": c.tag_name,
                            "text": c.text,
                            "size": c.size,
                            "signature": get_signature(c),
                        }
                    )
                    break
            except:
                logging.info("Consent:Exception in processing element: {}".format(c.id))

        # Click the candidate
        if candidate is not None:
            try:  # in some pages element is not clickable
                logging.info(
                    "Consent:Clicking text: {}".format(
                        candidate.text.lower().strip(" ✓›!\n")
                    )
                )
                candidate.click()
                banner_data_return["clicked_element"] = candidate.id
                logging.info("Consent:Clicked: {}".format(candidate.id))

            except:
                logging.info("Consent:Exception in candidate click")
        else:
            logging.info("Consent:Warning, no matching candidate")

        return banner_data_return

    def _accept_consent(self):
        # Click Banner
        logging.info("Consent:Searching Banner")
        banner_data = self.__click_banner()

        if "clicked_element" not in banner_data:
            iframe_contents = self.driver.find_elements_by_css_selector("iframe")
            for content in iframe_contents:
                logging.info("Consent:Switching to frame: {}".format(content.id))
                try:
                    self.driver.switch_to.frame(content)
                    banner_data = self.__click_banner()
                    self.driver.switch_to.default_content()
                    if "clicked_element" in banner_data:
                        break
                except NoSuchFrameException:
                    self.driver.switch_to.default_content()
                    logging.info("Consent:Error in switching to frame")

        if not "clicked_element" in banner_data and TRY_SCROLL:
            logging.info("Consent:Trying with scroll")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        logging.info("Consent:URL after click: {}".format(self.driver.current_url))

        # Clean last page
        # self.driver.get("about:blank")

        return "clicked_element" in banner_data

    def _load_page_first_time(self, url):
        """
        Loads a single url
        :param url: The url
        """
        self.current_url = url
        self.start_driver()
        self._prepare_canvas_capture()

        try:
            self.driver.get(url)
        except WebDriverException:
            raise TimeoutError()

        if len(self.driver.requests) == 0:
            logging.error("Timeout")
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

        if certificate["cn"] == get_certificate_issuer_cn(certificate):
            raise SelfSignedCertificate()

        if not check_certificate_host(self.current_url, certificate):
            raise WrongHostCertificate()

    def _handle_page(self):
        time.sleep(self.js_load_wait)
        self._create_screenshot()
        try:
            accepted_tracking = self._accept_consent()
        except Exception as e:
            logging.warning(f"Accepting tracking caused crash. Exception: {e}")
            accepted_tracking = False
        time.sleep(self.js_load_wait)

        self._create_screenshot(post_consent=True)
        post_pageload_url = self.driver.current_url
        canvas_image_data = self._capture_canvas_images()
        requests = self._get_requests()
        cookies = self.driver.get_cookies()

        return (
            post_pageload_url,
            requests,
            cookies,
            canvas_image_data,
            accepted_tracking,
        )

    def crawl_url(self, url, rank=None):
        """
        Crawls a single url
        :param url: The url to crawl
        :param rank: the rank of the url to include in the output
        """
        self.start_driver()
        logging.info(f'Crawl start: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')
        tls_failure = None

        start_time = time.mktime(time.localtime())

        try:
            self._load_page_first_time(url)
        except DomainDoesNotExist:
            logging.error("Domain does not exist. Skipping this domain.")
            self.driver.close()
            return
        except TimeoutError:
            logging.error(f"Timeout occurred")
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
            self.driver.close()
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
            consent_failure,
        ) = self._handle_page()

        logging.info(f'Crawl end: {time.strftime("%d-%b-%Y_%H%M", time.localtime())}')

        output = {
            "website_domain": self.current_domain,
            "rank": rank,
            "crawl_mode": self.crawl_mode,
            "post_pageload_url": post_pageload_url,
            "pageload_start_ts": start_time,
            "pageload_end_ts": end_time,
            "consent_status": None,
            "requests": requests,
            "load_time": end_time - start_time,
            "cookies": cookies,
            "canvas_image_data": canvas_image_data,
            "failure_status": {
                "timeout": False,
                "TLS": str(tls_failure) if tls_failure else None,
                "consent": consent_failure,
            },
        }
        self._create_json(output)
        self.driver.close()

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
                    continue
