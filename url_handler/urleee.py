import re
from urllib.parse import urlparse


VALID_URL_TEMPLATE = re.compile(
    'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F]'
    '[0-9a-fA-F]))+'
)


def check_url(url):
    """
    Check url by regex VALID_URL_TEMPLATE.
    >>> check_url('http://itea.ua/courses-itea/python/python-advanced/')
    True
    >>> check_url('https://www.fullstackpython.com/best-python-resources.html')
    True
    >>> check_url('Python')
    False
    >>> check_url(None)
    False
    """
    return bool(url and VALID_URL_TEMPLATE.fullmatch(url))


def url_to_dict(url):
    url = urlparse(url)
    d = {'r_path': ''}
    if url[0]:
        d['scheme'] = url[0]
    if url[1]:
        d['netloc'] = url[1]
    if url[2]:
        path = url[2] + '/' if not url[2].endswith('/') else url[2]
        if path.startswith('/'):
            d['path'] = path
        else:
            d['r_path'] = path
    return d


def dict_url_to_string(url):
    return '{scheme}://{netloc}{path}{r_path}'.format(**url)
