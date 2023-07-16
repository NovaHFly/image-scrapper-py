
import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import unquote

import httpx
from bs4 import BeautifulSoup as bs

from image_scrapper.api import (
    AuthorPackage, DownloadUnit, PageParser,
    construct_package_name
)
from image_scrapper.constants.paths import DOWNLOADS
from image_scrapper.helpers import extract_file_extension

DOWNLOAD_DIR = DOWNLOADS / 'kemono_party'

PAGE_ID_REGEX = re.compile('\/([0-9a-zA-Z]+)$')


@dataclass
class KemonoPackage(AuthorPackage):
    
    image_urls: list[str]
    attachments: list[tuple[str, str]]

    @property
    def contents(self) -> Iterable[DownloadUnit]:

        base_name = construct_package_name(
            self.id, self.title, author=self.author, add_counter=True,
        )

        for i, i_url in enumerate(self.image_urls, 1):
            file_extension = extract_file_extension(i_url)

            file_path = DOWNLOAD_DIR / self.author / (
                base_name.format(i) + f'.{file_extension}'
            )
            yield DownloadUnit(i_url, file_path)

        a_base_name = construct_package_name(
            self.id, self.title, author=self.author
        )

        for a_name, a_url in self.attachments:
            
            file_path = DOWNLOAD_DIR / self.author / (
                a_base_name + f' - {a_name}'
            )
            yield DownloadUnit(a_url, file_path)


class LocalPageParser(PageParser):
    
    def parse(self, response: httpx.Response) -> KemonoPackage:

        # TODO: if post body contains links leading to files add them to attachments\

        # dump_response_text(response, 'kemono')
        
        post_id = PAGE_ID_REGEX.search(response.url.path)[1]

        soup = bs(response.text, 'lxml')

        title = soup.select_one('h1 span').text.strip()
        author = soup.select_one('.post__user-name').text.strip()

        image_urls = [
            image_tag.attrs['href']
                for image_tag in soup.select('.fileThumb')
        ]
        
        attachment_tags = soup.select('.post__attachment-link')
        attachments = [
            (unquote(tag.attrs['download']), tag.attrs['href'])
                for tag in attachment_tags
        ]
        
        return KemonoPackage(
            post_id, title, author, image_urls, attachments)

__all__ = [
    'LocalPageParser'
]
