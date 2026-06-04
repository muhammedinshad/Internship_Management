from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from Apps.accounts.models import User
from .models import Internship


class InternshipAPITests(APITestCase):
    def setUp(self):
        self.list_create_url = reverse('internship-list-create')
        self.detail_url = lambda pk: reverse('internship-detail', kwargs={'pk': pk})

        self.company1_data = {
            'username': 'company1',
            'email': 'company1@test.com',
            'password': 'TestPass@123',
            'confirm_password': 'TestPass@123',
            'phone': '1111111111',
            'role': 'company'
        }
        self.company2_data = {
            'username': 'company2',
            'email': 'company2@test.com',
            'password': 'TestPass@123',
            'confirm_password': 'TestPass@123',
            'phone': '2222222222',
            'role': 'company'
        }
        self.student_data = {
            'username': 'teststudent',
            'email': 'student@test.com',
            'password': 'TestPass@123',
            'confirm_password': 'TestPass@123',
            'phone': '1234567890',
            'role': 'student'
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

    def _create_internship(self, company_data=None):
        if company_data is None:
            company_data = self.company1_data
        self._register_and_login(company_data)
        response = self.client.post(self.list_create_url, self.internship_data, format='json')
        return response

    def test_create_internship_as_company_returns_201(self):
        resp = self._create_internship()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resp.data['success'])
        self.assertEqual(resp.data['data']['title'], self.internship_data['title'])
        self.assertEqual(resp.data['data']['company_name'], self.company1_data['username'])
        self.assertTrue(Internship.objects.filter(title=self.internship_data['title']).exists())

    def test_create_internship_as_student_returns_403(self):
        self._register_and_login(self.student_data)
        response = self.client.post(self.list_create_url, self.internship_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])

    def test_create_internship_without_auth_returns_401(self):
        response = self.client.post(self.list_create_url, self.internship_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_internships_without_token_returns_200(self):
        self._create_internship()
        self.client.credentials()
        response = self.client.get(self.list_create_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 1)

    def test_get_single_internship_returns_correct_data(self):
        create_resp = self._create_internship()
        internship_id = create_resp.data['data']['id']
        self.client.credentials()
        response = self.client.get(self.detail_url(internship_id), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['title'], self.internship_data['title'])
        self.assertEqual(response.data['data']['company_name'], self.company1_data['username'])

    def test_get_nonexistent_internship_returns_404(self):
        response = self.client.get(self.detail_url(9999), format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])

    def test_update_internship_as_owner_returns_200(self):
        create_resp = self._create_internship()
        internship_id = create_resp.data['data']['id']
        update_data = {'title': 'Updated Internship Title', 'location': 'Mumbai'}
        response = self.client.put(self.detail_url(internship_id), update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['title'], 'Updated Internship Title')
        self.assertEqual(response.data['data']['location'], 'Mumbai')

    def test_update_internship_as_different_company_returns_403(self):
        create_resp = self._create_internship()
        internship_id = create_resp.data['data']['id']
        self._register_and_login(self.company2_data)
        response = self.client.put(self.detail_url(internship_id),
                                    {'title': 'Hacked Title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])

    def test_delete_internship_as_owner_returns_200(self):
        create_resp = self._create_internship()
        internship_id = create_resp.data['data']['id']
        response = self.client.delete(self.detail_url(internship_id), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertFalse(Internship.objects.filter(id=internship_id).exists())

    def test_delete_internship_as_different_company_returns_403(self):
        create_resp = self._create_internship()
        internship_id = create_resp.data['data']['id']
        self._register_and_login(self.company2_data)
        response = self.client.delete(self.detail_url(internship_id), format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
        self.assertTrue(Internship.objects.filter(id=internship_id).exists())
