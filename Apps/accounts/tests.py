from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import User


class AuthAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.profile_url = reverse('profile')

        self.student_data = {
            'username': 'teststudent',
            'email': 'student@test.com',
            'password': 'TestPass@123',
            'confirm_password': 'TestPass@123',
            'phone': '1234567890',
            'role': 'student'
        }

        self.company_data = {
            'username': 'testcompany',
            'email': 'company@test.com',
            'password': 'TestPass@123',
            'confirm_password': 'TestPass@123',
            'phone': '0987654321',
            'role': 'company'
        }

    def _register_and_login(self, data=None):
        if data is None:
            data = self.student_data
        self.client.post(self.register_url, data, format='json')
        login_resp = self.client.post(self.login_url, {
            'email': data['email'],
            'password': data['password']
        }, format='json')
        token = login_resp.cookies.get('access_token').value
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return login_resp

    def test_register_student(self):
        response = self.client.post(self.register_url, self.student_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['user']['email'], self.student_data['email'])
        self.assertEqual(response.data['data']['user']['role'], 'student')
        self.assertTrue(User.objects.filter(email=self.student_data['email']).exists())

    def test_register_company(self):
        response = self.client.post(self.register_url, self.company_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['user']['role'], 'company')
        self.assertTrue(User.objects.filter(email=self.company_data['email']).exists())

    def test_duplicate_email_returns_400(self):
        self.client.post(self.register_url, self.student_data, format='json')
        response = self.client.post(self.register_url, self.student_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_mismatched_passwords_returns_400(self):
        data = self.student_data.copy()
        data['confirm_password'] = 'DifferentPass@456'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_login_success_sets_cookies(self):
        self.client.post(self.register_url, self.student_data, format='json')
        response = self.client.post(self.login_url, {
            'email': self.student_data['email'],
            'password': self.student_data['password']
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies['access_token'].value)
        self.assertTrue(response.cookies['refresh_token'].value)

    def test_login_wrong_password_returns_401(self):
        self.client.post(self.register_url, self.student_data, format='json')
        response = self.client.post(self.login_url, {
            'email': self.student_data['email'],
            'password': 'WrongPass!@#'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])

    def test_login_nonexistent_email_returns_404(self):
        response = self.client.post(self.login_url, {
            'email': 'doesnotexist@test.com',
            'password': 'SomePass@123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])

    def test_profile_with_token(self):
        self._register_and_login()
        response = self.client.get(self.profile_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], self.student_data['email'])

    def test_update_profile(self):
        self._register_and_login()
        update_data = {'username': 'updatedstudent', 'phone': '9999999999'}
        response = self.client.put(self.profile_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['username'], 'updatedstudent')
        self.assertEqual(response.data['data']['phone'], '9999999999')

    def test_profile_without_token_returns_401(self):
        response = self.client.get(self.profile_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_clears_cookies(self):
        self._register_and_login()
        response = self.client.post(self.logout_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')
