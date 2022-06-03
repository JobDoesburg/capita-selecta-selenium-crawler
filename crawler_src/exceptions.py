class DomainDoesNotExist(Exception):
    pass


class TLSError(Exception):
    pass


class SelfSignedCertificate(TLSError):
    def __str__(self):
        return "Self-signed certificate"


class WrongHostCertificate(TLSError):
    def __init__(self, certificate, domain):
        self.certificate = certificate
        self.domain = domain

    def __str__(self):
        return f"Wrong host certificate: valid for {[self.certificate['cn']] + self.certificate['altnames']} but used for {self.domain}"


class CertificateExpired(TLSError):
    def __str__(self):
        return "Certificate expired"
