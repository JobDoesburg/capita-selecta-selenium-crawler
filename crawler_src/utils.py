from urllib.parse import urlparse


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
    cert_domains = [
        record.decode("utf-8").split(".")
        for record in [certificate["cn"]] + certificate["altnames"]
    ]

    def check_single_domain(url, cert_domain):
        full_domain = urlparse(url).netloc.split(".")
        while len(full_domain) > 0:
            full_domain_part = full_domain.pop()
            try:
                cert_domain_part = cert_domain.pop()
            except IndexError:
                if full_domain_part == "www" and len(full_domain) == 0:
                    return True
                return False
            if cert_domain_part is None or (
                cert_domain_part != "*"
                and cert_domain_part.lower() != full_domain_part.lower()
            ):
                return False

        if len(cert_domain) == 0 or cert_domain[0] == "*":
            return True

        return False

    for domain in cert_domains:
        if check_single_domain(url, domain):
            return True
        continue
    return False


def check_certificate_self_signed(certificate):
    for key, val in certificate["issuer"]:
        if key == b"CN":
            return certificate["cn"] == val
