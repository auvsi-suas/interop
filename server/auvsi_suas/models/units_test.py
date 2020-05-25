"""Tests for the units module."""

from auvsi_suas.models import units
from django.test import TestCase


class TestMetersToFeet(TestCase):
    """Tests the conversion from meters to feet."""
    def test_m_to_ft(self):
        """Performs a data-driven test of the conversion."""
        cases = [
            # (m, ft_actual)
            (  0,     0),
            (  1,     3.28084),
            (  1.5,   4.92126),
            (100,   328.084),
        ]  # yapf: disable
        for (km, ft_actual) in cases:
            self.assertAlmostEqual(ft_actual,
                                   units.meters_to_feet(km),
                                   delta=5)


class TestKilometersToFeet(TestCase):
    """Tests the conversion from kilometers to feet."""
    def test_km_to_ft(self):
        """Performs a data-driven test of the conversion."""
        cases = [
            # (km, ft_actual)
            (  0,        0),
            (  1,     3280.84),
            (  1.5,   4921.26),
            (100,   328084),
        ]  # yapf: disable
        for (km, ft_actual) in cases:
            self.assertAlmostEqual(ft_actual,
                                   units.kilometers_to_feet(km),
                                   delta=5)


class TestFeetToMeters(TestCase):
    """Tests the conversion from feet to meters."""
    def test_feet_to_meters(self):
        """Performs a data-driven test of the conversion."""
        cases = [
            # (feet, meters)
            (   0,   0),
            (   1,   0.3048),
            (  10,   3.048),
            (1000, 304.8),
        ]  # yapf: disable
        for (feet, meters_actual) in cases:
            self.assertAlmostEqual(meters_actual,
                                   units.feet_to_meters(feet),
                                   delta=0.1)


class TestKnotsToFeetPerSecond(TestCase):
    """Tests the conversion from knots to feet per second."""
    def test_knots_to_fps(self):
        """Performs a data-drive test of the conversion."""
        cases = [
            # (knots, fps)
            (  1,       1.68781),
            ( 10,      16.8781),
            (100,     168.781),
        ]  # yapf: disable
        for (knots, fps_actual) in cases:
            self.assertAlmostEqual(fps_actual,
                                   units.knots_to_feet_per_second(knots),
                                   delta=5)
