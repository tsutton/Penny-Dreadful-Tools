import os
import subprocess
import sys

from modo_bugs import (scrape_announcements, scrape_bugblog, update,
                       verification)
from shared import configuration


def run() -> None:
    wd = configuration.get_str('modo_bugs_dir')
    if not os.path.exists(wd):
        subprocess.run(['git', 'clone', 'https://github.com/PennyDreadfulMTG/modo-bugs.git', wd])
    os.chdir(wd)
    args = sys.argv[2:]
    if not args:
        args.extend(['scrape', 'update', 'verify'])
    print('modo_bugs invoked with modes: ' + repr(args))

    if 'scrape' in args:
        args.extend(['scrape_bb', 'scrape_an'])
    if 'scrape_bb' in args:
        scrape_bugblog.main()
    if 'scrape_an' in args:
        scrape_announcements.main()

    if 'update' in args:
        update.main()
    if 'verify' in args:
        verification.main()
