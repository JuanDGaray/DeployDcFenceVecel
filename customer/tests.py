from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from .models import Project, Customer, Notification
from .utils import create_manager_assignment_notification

# Create your tests here.

class ManagerAssignmentNotificationTest(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User1'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User2'
        )
        
        # Create test customer
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='1234567890',
            address='123 Test St',
            city='Test City',
            state='Test State',
            country='Test Country'
        )
        
        # Create test project
        self.project = Project.objects.create(
            customer=self.customer,
            project_name='Test Project',
            sales_advisor=self.user1
        )
        
        self.client = Client()
    
    def test_create_manager_assignment_notification(self):
        """Test that manager assignment notifications are created correctly"""
        # Create notification for accounting manager
        create_manager_assignment_notification(
            self.project, 
            self.user2, 
            'accounting', 
            self.user1
        )
        
        # Check that notification was created
        notification = Notification.objects.filter(
            recipient=self.user2,
            notification_type='manager_assignment',
            project=self.project
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.sender, self.user1)
        self.assertIn('Accounting Manager', notification.message)
        self.assertIn(self.project.project_name, notification.message)
        self.assertIn(self.user1.get_full_name(), notification.message)
    
    def test_create_project_manager_notification(self):
        """Test that project manager assignment notifications are created correctly"""
        # Create notification for project manager
        create_manager_assignment_notification(
            self.project, 
            self.user2, 
            'production', 
            self.user1
        )
        
        # Check that notification was created
        notification = Notification.objects.filter(
            recipient=self.user2,
            notification_type='manager_assignment',
            project=self.project
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.sender, self.user1)
        self.assertIn('Project Manager', notification.message)
        self.assertIn(self.project.project_name, notification.message)
        self.assertIn(self.user1.get_full_name(), notification.message)
