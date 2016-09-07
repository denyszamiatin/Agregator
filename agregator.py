import chardet
import requests
import re
import os.path
from bs4 import BeautifulSoup
from urllib.parse import urlparse


VALID_URL_TEMPLATE = re.compile(
    'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F]'
    '[0-9a-fA-F]))+'
)

REMOVE_MULTIPLE_WATER_SPACE = re.compile('\s+')


class AgregatorError(Exception):
    pass

def get_url_list_from_file(file_path='urls.txt'):
    """
    Open file and return urls.txt of valid urls.txt.
    >>> get_url_list_from_file(file_path='./test/only_urls.txt')
    ['http://itea.ua/courses-itea/python/python-advanced/', \
'https://www.fullstackpython.com/best-python-resources.html', \
'https://pymotw.com/3/', \
'https://www.python.org/dev/peps/pep-0020/']
    >>> get_url_list_from_file(file_path='./test/mix_text_urls.txt')
    ['http://itea.ua/courses-itea/python/python-advanced/', \
'https://www.fullstackpython.com/best-python-resources.html', \
'https://pymotw.com/3/', \
'https://www.python.org/dev/peps/pep-0020/']
    >>> get_url_list_from_file(file_path='./test/text_without_url.txt')
    Traceback (most recent call last):
    ...
    agregator.AgregatorError: No url in set file
    >>> get_url_list_from_file(file_path='abrakadabra.txt')
    Traceback (most recent call last):
    ...
    agregator.AgregatorError: File not found

    """
    try:
        with open(os.path.normpath(file_path), 'r') as f:
            url_file = f.read()
    except FileNotFoundError:
        raise AgregatorError('File not found')
    url_list = [url for url in url_file.split() if check_url(url)]
    if not url_list:
        raise AgregatorError('No url in set file')
    return url_list


def check_url(url):
    """
    Check url by regex VALID_URL_TEMPLATE.
    >>> check_url('http://itea.ua/courses-itea/python/python-advanced/')
    True
    >>> check_url('https://www.fullstackpython.com/best-python-resources.html')
    True
    >>> check_url('Python')
    False
    """
    return bool(VALID_URL_TEMPLATE.fullmatch(url))


def get_content(url):
    """
    Get web page in bytes format by url. If something wrong return None
    >>> type(get_content(url='http://itea.ua/courses-itea/python/python-advanced/'))
    <class 'bytes'>
    >>> type(get_content('hts://pysad2asdmotw.com/3/'))
    <class 'NoneType'>
    """
    try:
        if requests.head(url).status_code == 200:
            return requests.get(url).content
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def decode(data):
    """Decode raw data to unicode string."""
    charset = chardet.detect(data)['encoding']
    try:
        return data.decode(charset)
    except ValueError:
        return ''


def remove_special_tags(soup, tags):
    """Completely remove script or style or any other special tags."""
    for script in soup(tags):
        script.extract()
    return soup


def remove_multiple_water_spaces(text):
    """Remove multiple water spaces"""
    return REMOVE_MULTIPLE_WATER_SPACE.sub(' ', text)


def remove_html_tags(page):
    """Remove HTML tags and remove."""
    soup = BeautifulSoup(page, 'html.parser')
    remove_special_tags(soup, ["script", "style"])
    return remove_multiple_water_spaces(soup.get_text())


def validate_domain_in_url(scheme, domain, url):
    url_domain = urlparse(url)[1]
    if url:
        if url_domain is domain:
            return url
        elif url_domain == '':
            return "{0}://{1}{3}{2}".format(scheme, domain, url, ('/' if url[0] != '/' else ''))
        else:
            return None


def get_urls_from_page(page, url):
    """Return list of URLs on HTML page"""
    soup = BeautifulSoup(page, 'html.parser')
    remove_special_tags(soup, ["script", "style"])
    url_list = [a['href'] for a in soup.find_all('a', href=True)]
    domain = urlparse(url)[1]
    scheme = urlparse(url)[0]
    clean_url = []
    for link in url_list:
        tmp = validate_domain_in_url(scheme, domain, link)
        if tmp is not None:
            clean_url.append(tmp)
    return [a for a in clean_url if check_url(a)]


if __name__ == '__main__':
    for url in get_url_list_from_file('urls.txt'):
        page = get_content(url)
        decode_page = decode(page)
        page_without_tags = remove_html_tags(decode_page)
        url_list = get_urls_from_page(decode_page, url)
        debug = True
        print(page_without_tags)
        print(url_list)
