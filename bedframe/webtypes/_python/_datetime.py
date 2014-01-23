"""Web-transmittable :mod:`datetime` types"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import datetime as _datetime
import re as _re

import pytz as _tz

from .. import _core


class datetime(_core.webobject):

    """A web-transmittable date and time

    This wraps a timezone-aware :class:`datetime.datetime`.

    """

    @classmethod
    def fromprim(cls, prim):
        # FIXME: generalize this and move it to :mod:`spruce.datetime`
        match = cls._FORMAT_RE.match(prim)
        if match:
            try:
                year = int(match.group('year'))
                month = int(match.group('month'))
                day = int(match.group('day'))
                hour = int(match.group('hour') or 0)
                minute = int(match.group('minute') or 0)
                second = int(match.group('second') or 0)
                microsecond = int(match.group('microsecond') or 0)
            except (TypeError, ValueError):
                # FIXME
                raise ValueError()

            tz_sign = match.group('tz_sign')
            if tz_sign:
                try:
                    tz_hours = int(tz_sign + match.group('tz_hours'))
                    tz_minutes = int(tz_sign
                                     + (match.group('tz_minutes') or '0'))
                except (TypeError, ValueError):
                    # FIXME
                    raise ValueError()
                tz_minutes += tz_hours * 60

                tzinfo = _tz.FixedOffset(tz_minutes)

            else:
                tzinfo = _tz.UTC

            return cls(_datetime.datetime(year, month, day, hour, minute,
                                          second, microsecond, tzinfo))
        # FIXME
        raise ValueError()

    def prim(self):
        return unicode(self.native().strftime(self._FORMAT))

    _FORMAT = '%Y-%m-%d %H:%M:%S.%f %z'

    _FORMAT_RE = \
        _re.compile(r'(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)'
                    r'(?= (?P<hour>\d+):(?P<minute>\d+):(?P<second>\d+)'
                    r'.(?P<microsecond>\d+)'
                    r'(?= (?P<tz_sign>[-+])(?P<tz_hours>\d\d)'
                    r'(?P<tz_minutes>\d\d)?)?)?')


class timedelta(_core.webobject):

    """A web-transmittable time difference

    This wraps a :class:`datetime.timedelta`.

    """

    @classmethod
    def fromprim(cls, prim):
        match = cls._FORMAT_RE.match(prim)
        if match:
            try:
                days = int(match.group('days'))
                seconds = int(match.group('seconds'))
                microseconds = int(match.group('microseconds'))
            except (TypeError, ValueError):
                # FIXME
                raise ValueError()
            return cls(_datetime.timedelta(days=days, seconds=seconds,
                                           microseconds=microseconds))
        # FIXME
        raise ValueError()

    def prim(self):
        return self._FORMAT.format(td=self.native())

    _FORMAT = u'{td.days:+} days {td.seconds:+}.{td.microseconds:06} s'

    _FORMAT_RE = _re.compile(r'(?P<days>[+-]\d+) days'
                             r' (?P<seconds>[+-]\d+).(?P<microseconds>\d+) s')
