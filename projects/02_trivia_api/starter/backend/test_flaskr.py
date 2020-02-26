import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy
import random

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""

        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}:{}@{}/{}".format('victor',
                                                             'cyberfalcon',
                                                             'localhost:5432',
                                                             self
                                                             .database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_get_categories(self):
        result = self.client().get('/categories')
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.data)

    def test_question_via_category(self):
        category = random.randint(1, 6)
        result = self.client().get(f'/categories/{category}/questions')
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.data)

    def test_questions_page(self):
        result = self.client().get('/questions?page=1')
        self.assertEqual(result.status_code, 200)

    def test_post_categories(self):
        result = self.client().post('/questions',
                                    json={"question":
                                          "This is a Test Question?",
                                          "answer": "TEST",
                                          "difficulty": "2",
                                          "category": "1"})
        self.assertEqual(result.status_code, 200)

    def test_delete_questions(self):
        result = self.client().delete('/categories')
        self.assertEqual(result.status_code, 200)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
