# TODO: Large todo: make sta.sh links description scraping and downloading

import json
import re
from typing import Iterable

from dataclasses import dataclass
import httpx
from bs4 import BeautifulSoup as bs
from icecream import ic

from image_scrapper.api import (
    AuthorPackage, DownloadUnit, ScrapperApi,
    UnloggedError, construct_package_name,
)
from image_scrapper.constants.paths import COOKIES, DOWNLOADS
from image_scrapper.helpers import (
    extract_file_extension,
    write_cookies,
    retry_times,
)

LOCAL_HEADERS = {'referer': 'https://www.pixiv.net/'}

LOCAL_DOWNLOADS = DOWNLOADS / 'pixiv'
LOCAL_COOKIES = COOKIES / 'pixiv'

PAGE_ID_REGEX = re.compile('\/([0-9]+)$')

UGOIRA_API = 'https://ugoira.com/api/illusts/queue'

@dataclass
class UgoiraPackage(AuthorPackage):
    
    download_url: str

    @property
    def contents(self) -> Iterable[DownloadUnit]:

        file_name = construct_package_name(
            pack_id=self.id,
            title=self.title,
            author=self.author,
            file_extension='mp4'
        )
        file_path = LOCAL_DOWNLOADS / self.author / file_name

        yield DownloadUnit(self.download_url, file_path)
        
@dataclass
class IllustrationPackage(AuthorPackage):
    
    base_url: str
    page_count: int

    @property
    def contents(self) -> Iterable[DownloadUnit]:

        base_name = construct_package_name(
            pack_id=self.id,
            title=self.title,
            author=self.author,
            file_extension=extract_file_extension(self.base_url),
            multipage=True
        )
        
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


class LocalApi(ScrapperApi):

    @retry_times(5)
    def get_ugoira_mp4_url(self, px_id: str):
        
        api_response = self.post(UGOIRA_API, {'text': px_id})
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
                px_id, title, author, ugoira_url)
        
        page_count: int = img_data['pageCount']
        base_url = orig_url.replace('_p0', '_p{}')
        return IllustrationPackage(
            px_id, title, author, base_url, page_count
        )
            

__all__ = [
    'LocalApi'
]
