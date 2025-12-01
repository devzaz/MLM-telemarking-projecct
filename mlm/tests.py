from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import MLMNode

User = get_user_model()

class MLMNodeTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username='u1', password='pass')
        self.u2 = User.objects.create_user(username='u2', password='pass')
        self.u3 = User.objects.create_user(username='u3', password='pass')

    def test_auto_place_root(self):
        n1 = MLMNode.objects.create(user=self.u1)
        parent, pos = MLMNode.auto_place(n1)
        self.assertIsNone(parent)
        self.assertIsNone(pos)

    def test_auto_place_children(self):
        root = MLMNode.objects.create(user=self.u1)
        n2 = MLMNode.objects.create(user=self.u2)
        parent, pos = MLMNode.auto_place(n2, start_node=root)
        self.assertEqual(parent.id, root.id)
        self.assertIn(pos, ('L','R'))



