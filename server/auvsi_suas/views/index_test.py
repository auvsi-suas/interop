"""Tests for the index module."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

index_url = reverse('auvsi_suas:index')


class TestIndex(TestCase):
    """Tests the ACLs on index."""
    def setUp(self):
        # Create nonadmin user
        self.user = User.objects.create_user('testuser', 'testemail@x.com',
                                             'testpass')
        self.user.save()
        # Create admin user
        self.superuser = User.objects.create_superuser('superuser',
                                                       'testemail@x.com',
                                                       'superpass')
        self.superuser.save()

    def test_index_logged_out(self):
        """Index requires login."""
        response = self.client.get(index_url)
        # Redirect to login
        self.assertEqual(302, response.status_code)

    def test_index_normal_user(self):
        """Index requires superuser."""
        self.client.force_login(self.user)
        response = self.client.get(index_url)
        # Redirect to login
        self.assertEqual(302, response.status_code)

    def test_index_superuser(self):
        """Index works for superuser."""
        self.client.force_login(self.superuser)
        response = self.client.get(index_url)
        self.assertEqual(200, response.status_code)
