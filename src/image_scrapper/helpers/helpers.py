
import re
from pathlib import Path
from itertools import zip_longest

from httpx import Response
from tenacity import retry, stop_after_attempt

SYMBOL_REPLACEMENTS = {
    '::': '', ':': '-',
    '?': '', '|': '', '/': '-', '\\': '',
    '*': '', '<': '', '>': '', '"': "'",
    '{': '[', '}': ']',
    '\n': ' ', '  ': ' ',
}

EXTENSION_PATTERN = re.compile('\.(png|jpe?g?|webp|mp4|(?:t|g)if|psd)')


def extract_file_extension(url: str, pattern: re.Pattern = EXTENSION_PATTERN) -> str:
    return list(pattern.finditer(url))[-1][1]

# TODO: logging retries
def retry_times(attempts: int):
    return retry(stop = stop_after_attempt(attempts))

def replace_win_path_symbols(string: str) -> str:
    for symbol, replacement in SYMBOL_REPLACEMENTS.items():
        string = string.replace(symbol, replacement)
    return string

def read_cookies(cookie_path: Path) -> dict[str, str]:
    
    if not cookie_path.exists():
        return {}

    with cookie_path.open() as file:
        return {cookie_name.strip(): cookie_value.strip()
            for cookie_name, cookie_value in zip_longest(*[file,]*2)}

def write_cookies(cookies: dict[str, str], cookie_file: Path):

    with cookie_file.open('w') as f:
        for key, value in cookies.items():
            cookie_pair = f'{key}\n{value}\n'
            f.write(cookie_pair)

def dump_response_text(response: Response, file_name: str, extension: str = 'html'):
    """Shortcut function to save http response text to an file. Used to debug web scraping scripts
    
    :Args:
    response: Response - response object supporting attribute [text]
    file_name: str - file name to save text to
    extension: str - file extension (Default = 'html')
    """
    with open(f'{file_name}.{extension}', 'w', encoding='UTF-8') as f:
        f.write(response.text)


__all__ = [
    'retry_times',
    'replace_win_path_symbols',
    'extract_file_extension',
    'read_cookies',
    'write_cookies',
    'dump_response_text',
]