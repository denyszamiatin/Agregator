from bs4 import BeautifulSoup


def get_text(html):
    """ Return text without tags, and dict with content of tags"""
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()
