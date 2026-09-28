import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.routers import activities


class FakeActivitiesCollection:
    def __init__(self, documents):
        self.documents = documents

    def find(self, query):
        return [
            copy.deepcopy(document)
            for document in self.documents
            if self._matches(document, query)
        ]

    def _matches(self, document, query):
        for field, condition in query.items():
            if field == "$or":
                if not any(self._matches(document, option) for option in condition):
                    return False
                continue

            if field == "schedule_details.days":
                days = document.get("schedule_details", {}).get("days", [])
                if not any(day in days for day in condition["$in"]):
                    return False
                continue

            if field == "schedule_details.start_time":
                start_time = document.get("schedule_details", {}).get("start_time")
                if start_time is None or start_time < condition["$gte"]:
                    return False
                continue

            if field == "schedule_details.end_time":
                end_time = document.get("schedule_details", {}).get("end_time")
                if end_time is None or end_time > condition["$lte"]:
                    return False
                continue

            if field == "difficulty":
                if isinstance(condition, dict) and "$exists" in condition:
                    has_difficulty = "difficulty" in document
                    if has_difficulty != condition["$exists"]:
                        return False
                    continue

                if document.get("difficulty") != condition:
                    if not (condition is None and "difficulty" not in document):
                        return False

        return True


class GetActivitiesDifficultyTests(unittest.TestCase):
    def setUp(self):
        self.collection = FakeActivitiesCollection(
            [
                {
                    "_id": "General Club",
                    "description": "Open to everyone",
                    "schedule_details": {
                        "days": ["Monday"],
                        "start_time": "15:00",
                        "end_time": "16:00",
                    },
                    "participants": [],
                    "max_participants": 10,
                },
                {
                    "_id": "Beginner Club",
                    "description": "Introductory",
                    "difficulty": "Beginner",
                    "schedule_details": {
                        "days": ["Monday"],
                        "start_time": "15:00",
                        "end_time": "16:00",
                    },
                    "participants": [],
                    "max_participants": 10,
                },
                {
                    "_id": "Advanced Club",
                    "description": "Experienced students",
                    "difficulty": "Advanced",
                    "schedule_details": {
                        "days": ["Tuesday"],
                        "start_time": "15:00",
                        "end_time": "16:00",
                    },
                    "participants": [],
                    "max_participants": 10,
                },
            ]
        )

    def test_all_difficulty_returns_only_general_activities(self):
        with patch.object(activities, "activities_collection", self.collection):
            response = activities.get_activities(difficulty="All")

        self.assertEqual(set(response.keys()), {"General Club"})

    def test_no_difficulty_filter_returns_all_activities(self):
        with patch.object(activities, "activities_collection", self.collection):
            response = activities.get_activities()

        self.assertEqual(
            set(response.keys()),
            {"General Club", "Beginner Club", "Advanced Club"},
        )

    def test_specific_difficulty_includes_matching_and_general_activities(self):
        with patch.object(activities, "activities_collection", self.collection):
            response = activities.get_activities(difficulty="Beginner")

        self.assertEqual(set(response.keys()), {"General Club", "Beginner Club"})

    def test_difficulty_filter_combines_with_day_filter(self):
        with patch.object(activities, "activities_collection", self.collection):
            response = activities.get_activities(day="Tuesday", difficulty="Advanced")

        self.assertEqual(set(response.keys()), {"Advanced Club"})


if __name__ == "__main__":
    unittest.main()
