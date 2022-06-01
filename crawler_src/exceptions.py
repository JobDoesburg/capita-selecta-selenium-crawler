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
