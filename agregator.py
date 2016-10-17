import itertools

import yaml

from page import get_page, compare_page
from text_handler.normalize import Normalize
from url_handler.urleee import check_url


def parse_config_file(file):
    with open(file, 'r') as config:
        configuration = yaml.load(config)
    return configuration


class Agregator:
    def __init__(self, config_file='config.yml'):
        config = parse_config_file(config_file)
        self.urls_need_check = {url for url in config['url'] if check_url(url)}
        self.requests = {Normalize.text(request) for request
                         in config['requests']}
        self.page_limit = config['page_limit']
        self.pages = []
        self.urls_check = set()
        self.walk()

    def walk(self):
        while True:
            delta = self.urls_need_check - self.urls_check
            if not delta or len(self.pages) == self.page_limit:
                break
            limit = self.page_limit - len(self.pages)
            part_of_urls = list(delta)[:limit]
            new_page = get_page(part_of_urls)
            self.urls_check.update(set(part_of_urls))
            for page in new_page:
                if page:
                    self.urls_need_check.update(page.urls_on_page)
                    self.pages.append(page)

    def compare_pages(self):
        result = compare_page(list(itertools.combinations(self.pages, 2)))
        print('Compare page:')
        for report in result:
            print(report)

    def find_requests_in_page(self):
        for request in self.requests:
            urls = [page.url for page in self.pages if request in page.text]
            if urls:
                print('Request - "{}" you can find in next url(s): \n\t{}'.
                      format(request, '\n\t'.join(urls)))
            else:
                print('Request - "{}" missing in our url list.'.format(request))


if __name__ == '__main__':
    a = Agregator()
    a.compare_pages()
    a.find_requests_in_page()
