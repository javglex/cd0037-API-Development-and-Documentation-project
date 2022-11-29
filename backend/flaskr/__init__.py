import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def null_or_blank(stringCheck):
    if stringCheck is None or stringCheck == "":
        return True
    return False

def null_or_zero(intCheck):
    if intCheck is None or intCheck == 0:
        return True
    return False

def null_or_empty(arrayCheck):
    if arrayCheck is None or len(arrayCheck) == 0:
        return True
    return False

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    @app.route("/categories", methods=["GET"])
    def retrieve_categories():
        categories = Category.query.all()
        categoryMap = {}
        for category in categories:         # add categories to a map
            categoryMap[category.id] = category.type

        return jsonify(
            {
                "success": True,
                "categories": categoryMap,
                "total_categories": len(categoryMap)
            }
        )

    @app.route("/questions", methods=["GET"])
    def retrieve_questions():
        page = request.args.get("page", 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        questions = Question.query.all()            # get list of questions
        questionsFormatted  = [question.format() for question in questions]          # format questions so that we can jsonfy it
        paginatedQuestions = questionsFormatted[start:end]          # only return paginated result
        
        if null_or_empty(paginatedQuestions):
            abort(404)

        categories = Category.query.all()           # get list of categories
        categoryMap = {}
        for category in categories:         # add categories to a map
            categoryMap[category.id] = category.type

        return jsonify({
            "success": True,
            "questions": paginatedQuestions,
            "total_questions": len(questionsFormatted),
            "categories": categoryMap,
            "current_category": None # current category empty, since there is no category for this endpoint
        })

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            questionsCount = Question.query.count()

            return jsonify({
                "success": True,
                "deleted": question_id,
                "total_questions": questionsCount

            })
        except:
            abort(422)


    @app.route("/questions", methods=["POST"])
    def create_question():
        body = request.get_json()

        answer_text = body.get("answer", None)
        question_text = body.get("question", None)
        category = body.get("category", None)
        difficulty = body.get("difficulty", None)

        # if any of our parameters are missing, abort
        if null_or_blank(question_text) or null_or_blank(answer_text) or null_or_blank(category) or null_or_blank(difficulty):
            print("missing request argument")
            abort(400)

        try:
            question = Question(question = question_text, answer=answer_text, category=category, difficulty=difficulty)
            question.insert()

            return jsonify(
                {
                    "success": True,
                    "created": question.id
                }
            )

        except:
            abort(422)

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        body = request.get_json()
        search_term = body.get('searchTerm', None)
        if null_or_blank(search_term):
            abort(400)
        print("search: "+search_term)
        query = Question.query.filter(Question.question.ilike('%' + search_term + '%'))

        questionsFormatted = [question.format() for question in query] # format questions so that we can jsonfy it

        if null_or_empty(questionsFormatted):
            abort(404) #questions not found

        response = {
            "success": True,
            "questions": questionsFormatted,
            "total_questions": len(questionsFormatted),
            "current_category": None,
        }
        return jsonify(response)

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def retrieve_questions_by_category(category_id):
        if category_id is None:
            abort(400)

        questionsQuery = Question.query.filter(Question.category==str(category_id))
        questionsFormatted = [question.format() for question in questionsQuery]

        if null_or_empty(questionsFormatted):
            abort(404)
            
        response = {
            "success": True,
            "count": questionsQuery.count(),
            "questions": questionsFormatted
        }
        return jsonify(response)

    @app.route('/quizzes', methods=['POST'])
    def get_next_question():
        body = request.get_json()
        category = body.get('quiz_category', None)
        previousQuestions = body.get('previous_questions', None)
        
        if null_or_zero(category['id']): # zero represents 'all' category
            questions = Question.query.all()
        else:
            questions = Question.query.filter(Question.category == category['id']).all()
        
        if len(questions) == 0: # if we have no questions, we somehow provided an invalid category
            abort(404)
        
        # fetch list of all questions in our category, except for questions where id matches a previous question
        availableQuestions = [question.format() for question in questions if question.id not in previousQuestions]

        if null_or_empty(availableQuestions): # if no questions remain, it means we're done
            return jsonify({
                'success': True,
                'question': None
            })

        question = random.choice(availableQuestions) #pick a random question to return

        return jsonify({
            'success': True,
            'question': question
        })



    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400
        
    return app

