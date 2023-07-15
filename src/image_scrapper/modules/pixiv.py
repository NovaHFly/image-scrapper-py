# TODO: Large todo: make sta.sh links description scraping and downloading

import json
import re
from typing import Iterable

from dataclasses import dataclass, field
import httpx
from bs4 import BeautifulSoup as bs
from icecream import ic

from image_scrapper.api_base import (
    AuthorPackage, DownloadUnit, PageParser,
    UnloggedError, construct_package_name,
)
from image_scrapper.constants.paths import COOKIES, DOWNLOADS
from image_scrapper.helpers import (
    extract_file_extension,
    replace_win_path_symbols,
    write_cookies,
    retry_times,
)

HEADERS = {'referer': 'https://www.pixiv.net/'}

LOCAL_DOWNLOADS = DOWNLOADS / 'pixiv'
LOCAL_COOKIES = COOKIES / 'pixiv'

PAGE_ID_REGEX = re.compile('\/([0-9]+)$')

UGOIRA_API = 'https://ugoira.com/api/illusts/queue'

@dataclass
class UgoiraPackage(AuthorPackage):
    
    download_url: str

    @property
    def download_data(self) -> Iterable[DownloadUnit]:
        
        file_path = LOCAL_DOWNLOADS / self.author / (construct_package_name(
            self.id, self.title, author=self.author
        ) + '.mp4')

        yield DownloadUnit(self.download_url, file_path)
        
@dataclass
class IllustrationPackage(AuthorPackage):
    
    base_url: str
    page_count: int

    @property
    def download_data(self) -> Iterable[DownloadUnit]:

        base_name = construct_package_name(
            self.id, self.title, author=self.author, add_counter=True
            ) + '.' + extract_file_extension(self.base_url)
        
        for i in range(self.page_count):
            
            download_url = self.base_url.format(i)
            file_path = LOCAL_DOWNLOADS / self.author / base_name.format(i+1)

            yield DownloadUnit(download_url, file_path)
            
PixivPackage = IllustrationPackage | UgoiraPackage

def _get_preload_json(
        soup: bs) -> dict[str, int | str]:
        
    meta_preload = soup.select_one('#meta-preload-data')

    # End program with assertion error if unable to get preload data
    assert meta_preload

    return json.loads(meta_preload.attrs['content'])


class LocalPageParser(PageParser):

    @retry_times(5)
    def get_ugoira_mp4_url(self, px_id: str):
        
        api_response = self.parent_api.client.post(UGOIRA_API, data={'text': px_id})
        ic(api_response)

        response_json = json.loads(api_response.text)

        mp4_url: str = response_json['data'][0]['preview'].get('mp4')
        return mp4_url
    
    def parse(self, response: httpx.Response) -> PixivPackage:

        soup = bs(response.text, 'lxml')

        px_id = PAGE_ID_REGEX.search(response.url.path)[1]
        img_data = _get_preload_json(soup)['illust'][px_id]

        title: str = img_data['illustTitle']
        author: str = img_data['userName']

        orig_url: str = img_data['urls']['original']

        if 'ugoira' in orig_url:
            while not (ugoira_url := self.get_ugoira_mp4_url(px_id)):
                pass
            return UgoiraPackage(
                px_id, title, ugoira_url, author=author)
        
        page_count: int = img_data['pageCount']
        base_url = orig_url.replace('_p0', '_p{}')
        return IllustrationPackage(
            px_id, title, base_url, page_count, author=author
        )
            

__all__ = [
    'LocalPageParser'
]
