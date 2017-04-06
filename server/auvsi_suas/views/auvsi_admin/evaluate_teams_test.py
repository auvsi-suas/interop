"""Tests for the evaluate_teams module."""

import cStringIO
import csv
import json
import logging
import zipfile
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client


class TestEvaluateTeams(TestCase):
    """Tests the evaluate_teams view."""

    fixtures = ['testdata/sample_mission.json']

    def setUp(self):
        """Sets up the tests."""
        # Create nonadmin user
        self.nonadmin_user = User.objects.create_user(
            'testuser', 'testemail@x.com', 'testpass')
        self.nonadmin_user.save()
        self.nonadmin_client = Client()
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            'testuser2', 'testemail@x.com', 'testpass')
        self.admin_user.save()
        self.admin_client = Client()
        # Create URLs for testing
        self.login_url = reverse('auvsi_suas:login')
        self.eval_url = reverse('auvsi_suas:evaluate_teams')

    def test_evaluate_teams_nonadmin(self):
        """Tests that you can only access data as admin."""
        self.client.post(self.login_url, {'username': 'testuser',
                                          'password': 'testpass'})
        response = self.client.get(self.eval_url)
        self.assertEqual(403, response.status_code)

    def test_invalid_mission(self):
        """Tests that an invalid mission ID results in error."""
        self.client.post(self.login_url, {'username': 'testuser',
                                          'password': 'testpass'})

        response = self.client.get(self.eval_url, {'mission': 100000})
        self.assertGreaterEqual(response.status_code, 400)

    def load_json(self, response):
        """Gets the json data out of the response's zip archive."""
        zip_io = cStringIO.StringIO(response.content)
        with zipfile.ZipFile(zip_io, 'r') as zip_file:
            return json.loads(zip_file.read('/evaluate_teams/all.json'))

    def load_csv(self, response):
        """Gets the CSV data out of the response's zip archive."""
        zip_io = cStringIO.StringIO(response.content)
        with zipfile.ZipFile(zip_io, 'r') as zip_file:
            return zip_file.read('/evaluate_teams/all.csv')

    def test_evaluate_teams(self):
        """Tests the eval Json method."""
        self.client.post(self.login_url, {'username': 'testuser2',
                                          'password': 'testpass'})
        response = self.client.get(self.eval_url)
        self.assertEqual(response.status_code, 200)
        data = self.load_json(response)
        self.assertIn('teams', data)
        teams = data['teams']
        self.assertEqual(len(teams), 3)
        self.assertEqual('user0', teams[0]['team'])
        self.assertEqual('user1', teams[1]['team'])
        self.assertIn('missionClockTimeSec', teams[0]['feedback'])

    def test_evaluate_teams_specific_team(self):
        """Tests the eval Json method on a specific team."""
        self.client.post(self.login_url, {'username': 'testuser2',
                                          'password': 'testpass'})
        response = self.client.get(self.eval_url, {'team': 53})
        self.assertEqual(response.status_code, 200)
        data = self.load_json(response)
        self.assertIn('teams', data)
        teams = data['teams']
        self.assertEqual(len(teams), 1)
        self.assertEqual('user0', teams[0]['team'])

    def test_evaluate_teams_csv(self):
        """Tests the CSV method."""
        self.client.post(self.login_url, {'username': 'testuser2',
                                          'password': 'testpass'})
        response = self.client.get(self.eval_url)
        self.assertEqual(response.status_code, 200)
        csv_data = self.load_csv(response)
        self.assertEqual(len(csv_data.split('\n')), 5)
        self.assertIn('team', csv_data)
        self.assertIn('missionClockTimeSec', csv_data)
        self.assertIn('user0', csv_data)
        self.assertIn('user1', csv_data)
