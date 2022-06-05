class CrawlingException(Exception):
    pass


class CrawlerInterceptionException(CrawlingException):
    def __init__(self, visiting_url, intercepted_url):
        self.visiting_url = visiting_url
        self.intercepted_url = intercepted_url

    def __str__(self):
        return f"First intercepted request wasn't for visiting url {self.visiting_url} but for {self.intercepted_url}"


class DomainDoesNotExist(CrawlingException):
    def __init__(self, domain):
        self.domain = domain


class TLSError(CrawlingException):
    def __init__(self, certificate, domain):
        self.certificate = certificate
        self.domain = domain


class SelfSignedCertificate(TLSError):
    def __str__(self):
        return "Self-signed certificate"


class WrongHostCertificate(TLSError):
    def __str__(self):
        return f"Wrong host certificate: valid for {[self.certificate['cn']] + self.certificate['altnames']} but used for {self.domain}"


class CertificateExpired(TLSError):
    def __str__(self):
        return "Certificate expired"
