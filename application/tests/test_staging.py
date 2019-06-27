import pytest
from prio_processor import staging
import apache_beam as beam
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to

import json


def test_prio_ping_transform():
    with TestPipeline() as p:
        test_data = list(map(json.dumps, [{"id": "1"}, {"id": "2"}]))
        data = p | "create test data" >> beam.Create(test_data)
        result = data | staging.PrioPingTransform()
        assert_that(result, equal_to(test_data))
