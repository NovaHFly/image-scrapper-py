
import re
from typing import Iterable

from bs4 import BeautifulSoup as bs
from icecream import ic

from image_scrapper.api import ScrapperApi


def _get_stash_page(client: ScrapperApi, main: bs):
    
    # If url leads to single image
    if not (folder_title_tag := main.select_one('h2')):

        yield _get_stash_file(main)
        return

    folder_title = folder_title_tag.text
    yield from _get_stash_folder(client, main, folder_title)

def _get_stash_file(main: bs) -> tuple[str, str]:
    """Gets data of a single stash image"""

    img_tags = main.select('img[collect_rid]')
    img_url = img_tags[1].attrs['src']
    img_title = main.select_one('a.title').text

    return img_url, img_title

def _get_stash_folder(client: ScrapperApi, main: bs, folder_title: str) -> Iterable[tuple[str, str]]:
    
    # Iterate over all item anchor tags in folder page
    for i, a in enumerate(main.select('.stash-thumb-container.already-uploaded a.t'), 1):

        stash_url = a.attrs['href']
        ic(stash_url)
        page_res = client.get(stash_url)

        img_url, img_title = _get_stash_file(bs(page_res.text, 'lxml'))
        yield img_url, f'[{folder_title}] [{i}] {img_title}'

def get_stash_urls(client: ScrapperApi, da_main: bs) -> Iterable[tuple[str, str]]:
    """Goes over all sta.sh urls found in deviation's description.
    Separately processes sta.sh singles and folders."""

    desc_tag = da_main.select_one('.da-editor-journal') or da_main.select_one('.legacy-journal')

    if not desc_tag:
        return None
    
    # Collect all sta.sh urls
    all_urls = (a.attrs['href'] for a in desc_tag.select('a'))
    stash_urls = {url.partition('?')[0] for url in all_urls if 'sta.sh' in url}

    # IF none are found stop generator
    if not stash_urls:
        return None

    for url in stash_urls:

        page_res = client.get(url)
        main = bs(page_res.text, 'lxml')

        yield from _get_stash_page(client, main)

__all__ = [
    'get_stash_urls'
]

        
            

        

    