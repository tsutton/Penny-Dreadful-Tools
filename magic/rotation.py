import datetime
import glob
import os
from typing import List, Optional, cast

from mypy_extensions import TypedDict

from magic import fetcher
from shared import configuration, dtutil
from shared.pd_exception import DoesNotExistException, InvalidDataException

SetInfo = TypedDict('SetInfo', { #pylint: disable=invalid-name
    'name': str,
    'block': Optional[str],
    'code': str,
    'mtgo_code': Optional[str],
    'enter_date': str,
    'exit_date': str,
    'rough_exit_date': str,
    'enter_date_dt': datetime.datetime,
    })

SEASONS = [
    'EMN', 'KLD', 'AER', 'AKH', 'HOU',
    'XLN', 'RIX', 'DOM', 'M19',
    ]

def init() -> List[SetInfo]:
    info = fetcher.whatsinstandard()
    if info['deprecated']:
        print('Current whatsinstandard API version is DEPRECATED.')
    set_info = cast(List[SetInfo], info['sets'])
    return [postprocess(release) for release in set_info]

def current_season_code():
    return last_rotation_ex()['code']

def current_season_num():
    look_for = current_season_code()
    look_in = SEASONS
    n = 0
    for code in look_in:
        n += 1
        if code == look_for:
            return n
    raise InvalidDataException('I did not find the current season code (`{code}`) in the list of seasons ({seasons}) and I am confused.'.format(code=look_for, seasons=','.join(look_in)))

def last_rotation() -> datetime.datetime:
    return last_rotation_ex()['enter_date_dt']

def next_rotation() -> datetime.datetime:
    return next_rotation_ex()['enter_date_dt']

def last_rotation_ex() -> SetInfo:
    return max([s for s in sets() if s['enter_date_dt'] < dtutil.now()], key=lambda s: s['enter_date_dt'])

def next_rotation_ex() -> SetInfo:
    return min([s for s in sets() if s['enter_date_dt'] > dtutil.now()], key=lambda s: s['enter_date_dt'])

def next_supplemental() -> datetime.datetime:
    last = last_rotation() + datetime.timedelta(weeks=3)
    if last > dtutil.now():
        return last
    return next_rotation() + datetime.timedelta(weeks=3)

def postprocess(setinfo: SetInfo) -> SetInfo:
    setinfo['enter_date_dt'] = dtutil.parse(cast(str, setinfo['enter_date']), '%Y-%m-%dT%H:%M:%S.%fZ', dtutil.WOTC_TZ)
    if setinfo['code'] == 'DOM': # !quality
        setinfo['mtgo_code'] = 'DAR'
    else:
        setinfo['mtgo_code'] = setinfo['code']
    return setinfo

def interesting(playability, c, speculation=True, new=True):
    if new and len({k: v for (k, v) in c['legalities'].items() if 'Penny Dreadful' in k}) == (0 if speculation else 1):
        return 'new'
    p = playability.get(c.name, 0)
    if p > 0.1:
        return 'heavily-played'
    elif p > 0.01:
        return 'moderately-played'
    return None

def text() -> str:
    full = next_rotation()
    supplemental = next_supplemental()
    now = dtutil.now()
    sdiff = supplemental - now
    diff = full - now
    if sdiff < diff:
        return 'The supplemental rotation is in {sdiff} (The next full rotation is in {diff})'.format(diff=dtutil.display_time(diff.total_seconds()), sdiff=dtutil.display_time(sdiff.total_seconds()))
    return 'The next rotation is in {diff}'.format(diff=dtutil.display_time(diff.total_seconds()))

__SETS: List[SetInfo] = []
def sets() -> List[SetInfo]:
    if not __SETS:
        __SETS.extend(init())
    return __SETS

def season_id(v):
    """From any value return the season id which is the integer representing the season, or 'all' for all time."""
    if v is None:
        return current_season_num()
    try:
        n = int(v)
        if SEASONS[n - 1]:
            return n
    except (ValueError, IndexError):
        pass
    try:
        if v.lower() == 'all':
            return 'all'
        return SEASONS.index(v.upper()) + 1
    except (ValueError, AttributeError):
        raise DoesNotExistException("I don't know a season called {v}".format(v=v))

def season_code(v):
    """From any value return the season code which is a three letter string representing the season, or 'ALL' for all time."""
    sid = season_id(v)
    if sid == 'all':
        return 'ALL'
    return SEASONS[sid - 1]

def season_name(v):
    """From any value return the person-friendly name of the season, or 'All Time' for all time."""
    sid = season_id(v)
    if sid == 'all':
        return 'All Time'
    return 'Season {num}'.format(num=sid)

def files():
    return glob.glob(os.path.join(configuration.get_str('legality_dir'), 'Run_*.txt'))
