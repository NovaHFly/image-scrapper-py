import re
from dataclasses import dataclass, field
from typing import Iterable

from bs4 import BeautifulSoup as bs
from httpx import Response
from icecream import ic

from image_scrapper.api import (
    AuthorPackage, DownloadUnit, ScrapperApi,
    UnloggedError, construct_package_name
)
from image_scrapper.constants.paths import COOKIES, DOWNLOADS
from image_scrapper.helpers import (
    extract_file_extension,
    replace_win_path_symbols,
    write_cookies, dump_response_text
)
from .stash import get_stash_urls

LOCAL_HEADERS = {'referer': 'https://www.deviantart.com'}

LOCAL_DOWNLOADS = DOWNLOADS / 'deviantart'
LOCAL_COOKIES = COOKIES / 'deviantart'

STASH_REGEX = re.compile('(sta\.sh\/[0-9a-z]+)\??')

SIZE_REGEX = re.compile('size([0-9]+x[0-9]+)px')


@dataclass
class DeviantartPackage(AuthorPackage):
    
    download_url: str | None
    description: str | None = field(repr=False)
    stash_urls: list[tuple[str,str]] = field(default_factory=list)

    @property
    def contents(self) -> Iterable[DownloadUnit]:
        
        # ? 1. Main url, uses id, title and author
        # 2. Description
        # 3. Stash urls, uses id, title + 'sta.sh', author and counter
        base_fname = construct_package_name(
            pack_id=self.id,
            title=self.title,
            author=self.author,
        )
        base_path = LOCAL_DOWNLOADS / self.author / base_fname
        
        if self.download_url:
            suffix = f'.{extract_file_extension(self.download_url)}'
            main_path = base_path.with_suffix(suffix)
            yield DownloadUnit(self.download_url, main_path)

        if self.description:
            text_path = base_path.with_suffix('.txt')
            yield DownloadUnit(self.description, text_path, kind='text')

            ic(self.stash_urls)

            if not self.stash_urls:
                ic('STOP!!!!!')
                raise StopIteration

            for img_url, img_title in self.stash_urls:

                img_title = replace_win_path_symbols(img_title)
                img_title = f'{img_title} by {self.author} - {self.id}'

                ic(img_url)

                stash_path = base_path.with_stem(
                    img_title
                ).with_suffix(f'.{extract_file_extension(img_url)}')

                yield DownloadUnit(img_url, stash_path)

def _get_original_link(fullview: str, image_size: tuple[int, int]) -> str:
    
    if '.png?' in fullview:
        return fullview

    width, height = image_size

    fullview = fullview.split('?')[0]
    beginning, divider, stem = fullview.rpartition('/fill/')
    stem = stem.split("/")[1]


    dimensions = f'w_{width},h_{height},q_100'
    beginning = beginning.replace('/f/', '/intermediary/f/')

    return f'{beginning}{divider}{dimensions}/{stem}'

def _get_download_url(main: bs) -> str | None:
    
    download_button = main.select_one('a[data-hook=download_button]')

    if download_button:
        ic('Found button!') # TODO: logging debug
        return download_button.attrs['href']

    if (video_link := main.select_one('link[as="video"]')):
        return video_link.attrs['href']

    # ! Prolly not working anymore
    if (fullview_link := main.select_one('link[fetchpriority="high"]')):
        
        image_size_string = main.select_one('._3rhGt').text.split('px')[0]
        image_size = (int(size) for size in image_size_string.split('x'))

        return _get_original_link(fullview_link.attrs['src'], image_size)
    
    if img_alt := main.select_one('img.TZM0T'):
        ic('Alt image!')
        # image_size_raw = SIZE_REGEX.search(main.text)[1].split('x')
        # image_size = (int(size) for size in image_size_raw)
        
        # return _get_original_link(img_alt.attrs['src'], image_size)
        return img_alt.attrs['src']

    return None

def _get_description(main: bs) -> str | None:
    
    # If description isn't present by either of selectors return None
    if (editor_journal := \
            main.select_one('.da-editor-journal') or main.select_one('.legacy-journal')):
        # return '\n'.join(editor_journal.strings)
        return "\n".join(editor_journal.strings)
    
    return None


class LocalApi(ScrapperApi):

    def parse(self, response: Response) -> DeviantartPackage:

        cookies = response.cookies

        dump_response_text(response, 'deviantart')

        main = bs(response.text, 'lxml')

        if 'Log In' in main.text:

            print('Cookies outdated! '
                    'Please enter new cookies and restart program:')
            
            cookies = {
                'auth': input('auth: '),
                'auth_secure': input('auth_secure: '),
                'userinfo': input('userinfo: ')
            }
            
            write_cookies(cookies, LOCAL_COOKIES)

            raise UnloggedError
        
        da_id = str(response.url).rsplit('-', maxsplit=1)[-1]
        title, author = main.select_one('title') \
            .text.strip() \
            .removesuffix(' on DeviantArt') \
            .rsplit(' by ', maxsplit=1)

        download_url = _get_download_url(main)
        description = _get_description(main)
        stash_urls = get_stash_urls(self, main)

        
        return DeviantartPackage(
            da_id, title, author, download_url, description, stash_urls
        )


__all__ = [
    'LocalApi',
    'LOCAL_COOKIES',
    'LOCAL_HEADERS',
]

