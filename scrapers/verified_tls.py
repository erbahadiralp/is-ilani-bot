"""Complete a public server chain while retaining root and hostname validation."""
import ssl
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter


def isbank_context():
    context = ssl.create_default_context(cafile=requests.certs.where())
    # The bundled intermediate must chain to a normal trusted root, not become one.
    context.verify_flags &= ~ssl.VERIFY_X509_PARTIAL_CHAIN
    context.load_verify_locations(cafile=str(Path(__file__).resolve().parents[1] / "certificates" / "globalsign-rsa-ov-ssl-ca-2018.pem"))
    return context


class IsbankTLSAdapter(HTTPAdapter):
    def __init__(self):
        self.context = isbank_context()
        super().__init__()

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self.context
        return super().init_poolmanager(*args, **kwargs)

    def build_connection_pool_key_attributes(self, request, verify, cert=None):
        host, pool = super().build_connection_pool_key_attributes(request, verify, cert)
        pool["ssl_context"] = self.context
        return host, pool


def get_isbank(url, **kwargs):
    with requests.Session() as session:
        session.mount("https://ik.isbank.com.tr/", IsbankTLSAdapter())
        return session.get(url, **kwargs)
