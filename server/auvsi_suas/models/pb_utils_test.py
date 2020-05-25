"""Tests for the pb_utils module."""

from auvsi_suas.models import pb_utils
from auvsi_suas.proto import interop_api_pb2
from django.test import TestCase


def TestFieldChociesFromEnum(TestCase):
    """Tests the FieldChoicesFromEnum utility."""
    def test_generates_choices(self):
        """Tests generates choices for a sample enum."""
        self.assertEqual([(1, 'N'), (2, 'NE'), (3, 'E'), (4, 'SE'), (5, 'S'),
                          (6, 'SW'), (7, 'W'), (8, 'NW')],
                         sorted(
                             pb_utils.FieldChoicesFromEnum(
                                 interop_api_pb2.Odlc.Orientation)))
