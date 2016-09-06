import chardet
import requests
import re
import os.path


VALID_URL_TEMPLATE = re.compile(
    'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F]'
    '[0-9a-fA-F]))+'
)


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


def remove_html_tags(page):
    """Remove HTML tags and remove more one whitespace characters."""
    without_tags = re.sub('<[^<]+?>', '', page)
    return re.sub('\s+', ' ', without_tags)


if __name__ == '__main__':
    for url in get_url_list_from_file('urls.txt'):
        page = get_content(url)
        decode_page = decode(page)
        page_without_tags = remove_html_tags(decode_page)
        debug = True
