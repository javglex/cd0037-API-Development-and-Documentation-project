import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        self.new_question = {"answer": "Stephen King", "question": "Which Author wrote The Shining?", "category": 3, "difficulty": 3}
        self.new_question_invalid = {"answer": None, "question": "??", "category": 5}
        self.quiz = {"previous_questions":[2,4], "quiz_category": {"id":5, "type":"Entertainment"}}

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass


    def test_retrieve_categories_success(self):
        res = self.client().get("/categories")
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["total_categories"])
        self.assertTrue(len(data["categories"]))

    """Retrieve Questions Tests"""

    def test_retrieve_questions_success(self):
        res = self.client().get("/questions?page=2")
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["questions"]))
        self.assertTrue(len(data["categories"]))
        self.assertTrue(data["total_questions"])
        self.assertEqual(data["current_category"], None)

    def test_retrieve_questions_out_of_bounds(self):
        res = self.client().get("/questions?page=2000")
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)

    """Create Questions Tests"""

    def test_create_question_success(self):
        res = self.client().post("/questions", json=self.new_question)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertIsNotNone(data["created"])

    def test_create_question_invalid(self):
        res = self.client().post("/questions", json=self.new_question_invalid)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)

    """Search Questions Tests"""

    def test_search_question_success(self):
        res = self.client().post("/questions/search", json={"searchTerm": "which"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["total_questions"])
        self.assertTrue(len(data["questions"]))
        self.assertEqual(data["current_category"], None)

    def test_search_question_no_resource(self):
        res = self.client().post("/questions/search", json={"searchTerm": "bndfgadsfasd"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)

    def test_search_question_invalid_args(self):
        res = self.client().post("/questions/search", json={"searchTerm": ""})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)

    """Retrieve Questions By Category Tests"""

    def test_retrieve_questions_by_category_success(self):
        res = self.client().get("/categories/1/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["count"])
        self.assertTrue(len(data["questions"]))

    def test_retrieve_questions_by_invalid_category(self):
        res = self.client().get("/categories/100/questions")
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)

    """Delete Questions Tests"""

    def test_delete_question_success(self):
        res = self.client().post("/questions", json=self.new_question)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertIsNotNone(data["created"])

        idCreated = data["created"]
        res = self.client().delete("/questions/"+str(idCreated))
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["deleted"], idCreated)

    def test_delete_invalid_question(self):
        res = self.client().post("/questions", json=self.new_question)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertIsNotNone(data["created"])

        res = self.client().delete("/questions/"+str(-1))
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)

    """Start Quiz Tests"""

    def test_start_quiz_success(self):
        res = self.client().post("/quizzes", json=self.quiz) # we start a new quiz with previous questions answered (id 2 & 4)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["question"]['id'], 6)

    def test_start_quiz_fail(self):
        res = self.client().post("/quizzes", json=None) # provide an invalid quiz
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()