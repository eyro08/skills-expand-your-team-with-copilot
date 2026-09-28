import unittest
from unittest.mock import patch

from fastapi import HTTPException
from argon2 import PasswordHasher

from src.backend.routers import auth


class FakeTeachersCollection:
    def __init__(self, teachers):
        self._teachers = teachers

    def find_one(self, query):
        return self._teachers.get(query["_id"])


class LoginTests(unittest.TestCase):
    def setUp(self):
        self.collection = FakeTeachersCollection(
            {
                "mchen": {
                    "_id": "mchen",
                    "username": "mchen",
                    "display_name": "Mr. Chen",
                    "password": PasswordHasher().hash("chess456"),
                    "role": "teacher",
                }
            }
        )

    def test_login_accepts_seeded_argon2_password(self):
        with patch.object(auth, "teachers_collection", self.collection):
            response = auth.login("mchen", "chess456")

        self.assertEqual(
            response,
            {
                "username": "mchen",
                "display_name": "Mr. Chen",
                "role": "teacher",
            },
        )

    def test_login_rejects_invalid_password(self):
        with patch.object(auth, "teachers_collection", self.collection):
            with self.assertRaises(HTTPException) as context:
                auth.login("mchen", "wrong-password")

        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "Invalid username or password")


if __name__ == "__main__":
    unittest.main()
