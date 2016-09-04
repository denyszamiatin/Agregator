from bs4 import BeautifulSoup
import utest

sentinel = object()


def get_text(html, tags=sentinel):
    """ Return text without tags, and dict with content of tags"""
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    if tags is not sentinel:
        if not isinstance(tags, list) :
            raise TypeError('Tags must be a list')
        content = {}
        for tag in tags:
            content[tag] = list([BeautifulSoup(x.__str__(), 'html.parser').get_text()
                                 for x in soup.find_all(tag, recursive=True)])
        return text, content
    else:
        return text