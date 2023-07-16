
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from string import Template

import httpx
from bs4 import BeautifulSoup as bs
from icecream import ic

from image_scrapper.helpers import extract_file_extension

from .api_base import (
    BasicPackage, DownloadUnit, PageParser,
    construct_package_name
)


ID_REGEX = re.compile('\/([0-9]+)\/')
PAGE_COUNT_REGEX = re.compile('[0-9]+')

@dataclass(kw_only=True)
class GalleryParseParams:
    
    title_header_selector: str
    page_count_selector: str

    big_img_selector: str
    big_img_attr: str

    download_dir: str
    template_url: Template|None = None

    @property
    def headers_selectors(self):
        return self.title_header_selector, self.page_count_selector

    @property
    def big_img_selectors(self):
        return self.big_img_selector, self.big_img_attr


@dataclass
class GalleryPackage(BasicPackage):
    
    image_urls: list
    download_dir: Path

    @property
    def contents(self) -> Iterable[DownloadUnit]:
        
        base_path = self.download_dir / construct_package_name(
            self.id, self.title
        )

        for i, url in enumerate(self.image_urls, 1):

            file_extension = extract_file_extension(url)
            file_path = base_path / f'{i}.{file_extension}'

            yield DownloadUnit(url, file_path)
    

class GalleryParser(PageParser):

    parse_params: GalleryParseParams
    current_url: str = ''

    # & It just works for now
    def __call__(self):
        return self

    def set_parse_params(self, params: GalleryParseParams) -> 'GalleryParser':
        self.parse_params = params
        return self


    def get_gallery_meta(self, soup: bs) -> tuple[str, str, int]:
        
        title_selector, count_selector = self.parse_params.headers_selectors
        
        gallery_id = ID_REGEX.search(self.current_url)[1]

        gallery_title = soup.select_one(title_selector).text
        page_count = int(PAGE_COUNT_REGEX.search(
            soup.select_one(count_selector).text)[0])

        return gallery_id, gallery_title, page_count
    
    # May be redefined
    def generate_page_urls(
            self, page_count: int) -> list[str]:
        
        url_template = self.parse_params.template_url
        
        for i in range(1, page_count+1):
            yield url_template.safe_substitute({'page_n': i})

    def parse_page_urls(
            self, page_urls: list[str]) -> list[str]:
        
        for i, url in enumerate(page_urls, 1):

            page_res = self.parent_api.get_response(url)
            soup = bs(page_res.text, 'lxml')

            selector, tag_attr = self.parse_params.big_img_selectors
            image_url = soup.select_one(selector).attrs[tag_attr]
            ic(f'Got image {i}')

            yield image_url


    def parse(self, response: httpx.Response) -> GalleryPackage:
        
        soup = bs(response.text, 'lxml')
        self.current_url = str(response.url)

        gallery_id, title, page_count = self.get_gallery_meta(soup)
        
        if template := self.parse_params.template_url:
            self.parse_params.template_url = \
                Template(template.safe_substitute(
                    {'gal_id': gallery_id}
                ))

        image_page_urls = list(self.generate_page_urls(page_count))
        image_urls = list(self.parse_page_urls(image_page_urls))

        download_dir = self.parse_params.download_dir

        return GalleryPackage(
            gallery_id, title, image_urls, download_dir)


__all__ = [
    'GalleryParser',
    'GalleryPackage',
    'GalleryParseParams',
]