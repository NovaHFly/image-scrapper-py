'''Image scrapper console app v0.1

Usage:
    image_scrapper.py URLS...
    image_scrapper.py -f URL_FILE

Options:
    -h           show this message
    -f URL_FILE  specify text file with urls

'''

from docopt import docopt, ParsedOptions
from .modules import module_apis


def main(args: ParsedOptions):

    module = module_apis['deviantart']
    
    url = args.URLS[0]
    module.download_from(url)


def main_cli():
    args = docopt(__doc__)
    main(args)