# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import datetime
import pytest

from eventdata.parameter_sources.timeutils import TimestampStructGenerator, TimeParsingError


class ReproducibleClock:
    def __init__(self, start, delta=datetime.timedelta(0)):
        self.now = start
        self.delta = delta

    def __call__(self, *args, **kwargs):
        now = self.now
        self.now += self.delta
        return now


def test_generate_interval_from_now():
    clock = ReproducibleClock(start=datetime.datetime(year=2019, month=1, day=5, hour=15),
                              delta=datetime.timedelta(seconds=5))

    g = TimestampStructGenerator(starting_point="now", utcnow=clock)

    # first generated timestamp will be one (clock) invocation after the original start
    assert g.next_timestamp() == {
        "iso": "2019-01-05T15:00:05.000Z",
        "iso_prefix": "2019-01-05T15:00:05",
        "yyyy": "2019",
        "yy": "19",
        "mm": "01",
        "dd": "05",
        "hh": "15"
    }

    assert g.next_timestamp() == {
        "iso": "2019-01-05T15:00:10.000Z",
        "iso_prefix": "2019-01-05T15:00:10",
        "yyyy": "2019",
        "yy": "19",
        "mm": "01",
        "dd": "05",
        "hh": "15"
    }

    assert g.next_timestamp() == {
        "iso": "2019-01-05T15:00:15.000Z",
        "iso_prefix": "2019-01-05T15:00:15",
        "yyyy": "2019",
        "yy": "19",
        "mm": "01",
        "dd": "05",
        "hh": "15"
    }


def test_generate_interval_from_fixed_starting_point():
    clock = ReproducibleClock(start=datetime.datetime(year=2019, month=1, day=5, hour=15),
                              delta=datetime.timedelta(seconds=1))

    g = TimestampStructGenerator(starting_point="2018-05-01:00:59:56",
                                 acceleration_factor=3.0,
                                 utcnow=clock)

    assert g.next_timestamp() == {
        "iso": "2018-05-01T00:59:59.000Z",
        "iso_prefix": "2018-05-01T00:59:59",
        "yyyy": "2018",
        "yy": "18",
        "mm": "05",
        "dd": "01",
        "hh": "00"
    }

    assert g.next_timestamp() == {
        "iso": "2018-05-01T01:00:02.000Z",
        "iso_prefix": "2018-05-01T01:00:02",
        "yyyy": "2018",
        "yy": "18",
        "mm": "05",
        "dd": "01",
        "hh": "01"
    }
    assert g.next_timestamp() == {
        "iso": "2018-05-01T01:00:05.000Z",
        "iso_prefix": "2018-05-01T01:00:05",
        "yyyy": "2018",
        "yy": "18",
        "mm": "05",
        "dd": "01",
        "hh": "01"
    }


def test_generate_interval_from_fixed_starting_point_with_offset():
    clock = ReproducibleClock(start=datetime.datetime(year=2019, month=1, day=5, hour=15),
                              delta=datetime.timedelta(seconds=1))

    g = TimestampStructGenerator(starting_point="2018-05-01:00:59:56",
                                 offset="+10d",
                                 acceleration_factor=3.0,
                                 utcnow=clock)

    assert g.next_timestamp() == {
        "iso": "2018-05-11T00:59:59.000Z",
        "iso_prefix": "2018-05-11T00:59:59",
        "yyyy": "2018",
        "yy": "18",
        "mm": "05",
        "dd": "11",
        "hh": "00"
    }

    assert g.next_timestamp() == {
        "iso": "2018-05-11T01:00:02.000Z",
        "iso_prefix": "2018-05-11T01:00:02",
        "yyyy": "2018",
        "yy": "18",
        "mm": "05",
        "dd": "11",
        "hh": "01"
    }
    assert g.next_timestamp() == {
        "iso": "2018-05-11T01:00:05.000Z",
        "iso_prefix": "2018-05-11T01:00:05",
        "yyyy": "2018",
        "yy": "18",
        "mm": "05",
        "dd": "11",
        "hh": "01"
    }


def test_generate_interval_and_skip():
    clock = ReproducibleClock(start=datetime.datetime(year=2019, month=1, day=5, hour=15),
                              delta=datetime.timedelta(seconds=1))

    g = TimestampStructGenerator(starting_point="2018-05-01:00:59:56",
                                 acceleration_factor=3.0,
                                 utcnow=clock)

    assert g.next_timestamp() == {
        "iso": "2018-05-01T00:59:59.000Z",
        "iso_prefix": "2018-05-01T00:59:59",
        "yyyy": "2018",
        "yy": "18",
        "mm": "05",
        "dd": "01",
        "hh": "00"
    }

    assert g.next_timestamp() == {
        "iso": "2018-05-01T01:00:02.000Z",
        "iso_prefix": "2018-05-01T01:00:02",
        "yyyy": "2018",
        "yy": "18",
        "mm": "05",
        "dd": "01",
        "hh": "01"
    }

    g.skip(datetime.timedelta(days=1))

    assert g.next_timestamp() == {
        "iso": "2018-05-02T00:59:59.000Z",
        "iso_prefix": "2018-05-02T00:59:59",
        "yyyy": "2018",
        "yy": "18",
        "mm": "05",
        "dd": "02",
        "hh": "00"
    }

    assert g.next_timestamp() == {
        "iso": "2018-05-02T01:00:02.000Z",
        "iso_prefix": "2018-05-02T01:00:02",
        "yyyy": "2018",
        "yy": "18",
        "mm": "05",
        "dd": "02",
        "hh": "01"
    }


def test_simulate_ticks():
    clock = ReproducibleClock(start=datetime.datetime(year=2019, month=1, day=5, hour=15),
                              delta=datetime.timedelta(seconds=1))

    g = TimestampStructGenerator(starting_point="2018-05-01:00:59:56",
                                 acceleration_factor=3.0,
                                 utcnow=clock)

    assert g.next_timestamp() == {
        "iso": "2018-05-01T00:59:59.000Z",
        "iso_prefix": "2018-05-01T00:59:59",
        "yyyy": "2018",
        "yy": "18",
        "mm": "05",
        "dd": "01",
        "hh": "00"
    }

    assert g.simulate_tick(micros=1.0) == {
        "iso": "2018-05-01T00:59:59.001Z",
        "iso_prefix": "2018-05-01T00:59:59",
        "yyyy": "2018",
        "yy": "18",
        "mm": "05",
        "dd": "01",
        "hh": "00"
    }

    assert g.simulate_tick(micros=0.1) == {
        "iso": "2018-05-01T00:59:59.001Z",
        "iso_prefix": "2018-05-01T00:59:59",
        "yyyy": "2018",
        "yy": "18",
        "mm": "05",
        "dd": "01",
        "hh": "00"
    }

    assert g.simulate_tick(micros=10.0) == {
        "iso": "2018-05-01T00:59:59.011Z",
        "iso_prefix": "2018-05-01T00:59:59",
        "yyyy": "2018",
        "yy": "18",
        "mm": "05",
        "dd": "01",
        "hh": "00"
    }


def test_generate_invalid_time_interval():
    # "w" is unsupported
    with pytest.raises(TimeParsingError) as ex:
        TimestampStructGenerator(starting_point="now+1w")

    assert "Invalid time format: now+1w" == str(ex.value)

