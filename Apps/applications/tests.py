from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from Apps.accounts.models import User
from Apps.internships.models import Internship
from .models import Application


class ApplicationAPITests(APITestCase):
    def setUp(self):
        self.apply_url = reverse('apply-internship')
        self.list_url = reverse('list-applications')
        self.status_url = lambda pk: reverse('update-status', kwargs={'pk': pk})

        self.student1_data = {
            'username': 'student1',
            'email': 'student1@test.com',
            'password': 'TestPass@123',
            'confirm_password': 'TestPass@123',
            'phone': '1111111111',
            'role': 'student'
        }
        self.student2_data = {
            'username': 'student2',
            'email': 'student2@test.com',
            'password': 'TestPass@123',
            'confirm_password': 'TestPass@123',
            'phone': '2222222222',
            'role': 'student'
        }
        self.company_data = {
            'username': 'testcompany',
            'email': 'company@test.com',
            'password': 'TestPass@123',
            'confirm_password': 'TestPass@123',
            'phone': '9999999999',
            'role': 'company'
        }

        self.internship_data = {
            'title': 'Software Developer Intern',
            'description': 'Build and maintain web applications.',
            'location': 'Bangalore',
        }

    def _register_and_login(self, data):
        self.client.post(reverse('register'), data, format='json')
        login_resp = self.client.post(reverse('login'), {
            'email': data['email'],
            'password': data['password']
        }, format='json')
        token = login_resp.cookies.get('access_token').value
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return login_resp

    def _create_internship(self):
        self._register_and_login(self.company_data)
        resp = self.client.post(reverse('internship-list-create'), self.internship_data, format='json')
        return resp.data['data']['id']

    def test_apply_as_student_returns_201(self):
        internship_id = self._create_internship()
        self._register_and_login(self.student1_data)
        response = self.client.post(self.apply_url, {'internship': internship_id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'pending')
        self.assertTrue(Application.objects.filter(student__email=self.student1_data['email']).exists())

    def test_duplicate_application_returns_400(self):
        internship_id = self._create_internship()
        self._register_and_login(self.student1_data)
        self.client.post(self.apply_url, {'internship': internship_id}, format='json')
        response = self.client.post(self.apply_url, {'internship': internship_id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_apply_as_company_returns_403(self):
        internship_id = self._create_internship()
        # Already logged in as company from _create_internship
        response = self.client.post(self.apply_url, {'internship': internship_id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])

    def test_apply_without_token_returns_401(self):
        self.client.credentials()
        response = self.client.post(self.apply_url, {'internship': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_apply_invalid_internship_returns_error(self):
        self._register_and_login(self.student1_data)
        response = self.client.post(self.apply_url, {'internship': 9999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_list_applications_as_student_returns_own_only(self):
        internship_id = self._create_internship()
        # Student 1 applies
        self._register_and_login(self.student1_data)
        self.client.post(self.apply_url, {'internship': internship_id}, format='json')
        # Student 2 applies
        self._register_and_login(self.student2_data)
        self.client.post(self.apply_url, {'internship': internship_id}, format='json')
        # Student 1 lists their applications
        self._register_and_login(self.student1_data)
        response = self.client.get(self.list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 1)

    def test_list_applications_as_company_returns_company_only(self):
        internship_id = self._create_internship()
        self._register_and_login(self.student1_data)
        self.client.post(self.apply_url, {'internship': internship_id}, format='json')
        self._register_and_login(self.company_data)
        response = self.client.get(self.list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['student_name'], self.student1_data['username'])

    def test_update_status_as_company_returns_200(self):
        internship_id = self._create_internship()
        self._register_and_login(self.student1_data)
        apply_resp = self.client.post(self.apply_url, {'internship': internship_id}, format='json')
        application_id = apply_resp.data['data']['id']
        self._register_and_login(self.company_data)
        response = self.client.put(self.status_url(application_id),
                                   {'status': 'accepted'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'accepted')

    def test_update_status_invalid_value_returns_400(self):
        internship_id = self._create_internship()
        self._register_and_login(self.student1_data)
        apply_resp = self.client.post(self.apply_url, {'internship': internship_id}, format='json')
        application_id = apply_resp.data['data']['id']
        self._register_and_login(self.company_data)
        response = self.client.put(self.status_url(application_id),
                                   {'status': 'approved'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_update_status_as_student_returns_403(self):
        internship_id = self._create_internship()
        self._register_and_login(self.student1_data)
        apply_resp = self.client.post(self.apply_url, {'internship': internship_id}, format='json')
        application_id = apply_resp.data['data']['id']
        # Still logged in as student1
        response = self.client.put(self.status_url(application_id),
                                   {'status': 'accepted'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
