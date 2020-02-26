import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

# Paginates any SQLAlchemy result object given.

QUESTIONS_PER_PAGE = 10

# Created pagination function to reduce what is returned
# I have to say I can't find documentation for the .format() method here.
# I took the .format() from the tutorial,
# however I could find docs explaining it


def paginate(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [q.format() for q in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app)  # Added CORS func to app instance

# Allows CORS to allow on all routes.
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST, DELETE, OPTIONS')
        return response

# Obtains all categories
    @app.route('/categories', methods=['GET'])
    def get_categories():
        selection = Category.query.order_by(Category.id).all()
        current_categories = paginate(request, selection)
        types = [c['type'] for c in current_categories]

        return jsonify({
          "categories": types
        })


# Returns questions paginated by 10 per page
    @app.route('/questions', methods=['GET'])
    def get_questions():
        page = request.args.get('page', 1, type=int)

        try:
            selection = Question.query.all()
            questions = paginate(request, selection)
            total_questions = len(Question.query.all())
            current_cat = Category.query.all()
            category = paginate(request, current_cat)
            types = [c['type'] for c in category]
            return jsonify({
              "questions": questions,
              "totalQuestions": total_questions,
              "categories": types
            }) except: abort(400)

# Deletes a question by ID
    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_question(id):
        try:
            question = Question.query.filter(Question.id == id).one_or_none()
            category = question.category

            question.delete()

            selection = Question.query.all()
            questions = paginate(request, selection)
            total_questions = len(Question.query.all())
            categories = len(Category.query.all())

            if question is None:
                abort(404)
                print('item not found in DB.')
            return jsonify({
              'questions': questions,
              'totalQuestions': total_questions,
              'categories': categories,
              'currentCategory': category
              })except: abort(400)

# Add questions to the database
    @app.route('/questions', methods=['POST'])
    def add_questions():
        try:
            submission = request.get_json()

            question = submission['question']
            answer = submission['answer']
            difficulty = submission['difficulty']
            category = submission['category']

            new_trivia = Question(question=question, answer=answer,
                                  difficulty=difficulty, category=category)

            new_trivia.insert()

            selection = Question.query.all()
            questions = paginate(request, selection)
            total_questions = len(Question.query.all())
            categories = len(Category.query.all())

            return jsonify({
              'success': True,
              'question': questions,
              'totalQuestions': total_questions,
              'categories': categories,
              'currentCategory': category
            })except: abort(400)

# Searches for related questions depending on whats search, no case sensitive
    @app.route('/search', methods=['POST'])
    def search_questions():
        try:
            search = request.get_json()
            term = search['searchTerm']
            selection = Question.query.filter(Question.question
                                              .ilike(f'%{term}%')).all()
            result = paginate(request, selection)
            total_questions = len(result)

            if result[0] is None:
                abort(400)
            return jsonify({
              'questions': result,
              'totalQuestions': total_questions,
              'currentCategory': result[0]['category']
            })except: abort(404)

# Fetches specific question.
    @app.route('/categories/<int:id>/questions', methods=['GET'])
    def fetch_category_questions(id):
        try:
            selection = Question.query.join(Category,
                                            Category.id == Question.category)
            .filter(Question.category == id)
            .all()
            questions = paginate(request, selection)
            total_questions = len(questions)
            current_category = id
            query = Category.query.all()
            return jsonify({
              "questions": questions,
              "totalQuestions": total_questions,
              "currentCategory": current_category
            })except: abort(400)

# Play game quizzes in the Play tab
    @app.route('/quizzes', methods=['POST'])
    def get_quizzes():
        data = request.get_json()
        previous_questions = data['previous_questions']
        category = data['quiz_category']['type']

        if category == 'click':
            questions = Question.query.all()
            result = paginate(request, questions)
            choice = random.choice(result)
            while choice['id'] in previous_questions:
                choice = random.choice(result)

        else:
            questions = Question.query.join(Category,
                                            Category.id == Question.category)
            .filter(Category.type == category)
            result = paginate(request, questions)

            choice = random.choice(result)
            while choice['id'] in previous_questions:
                choice = random.choice(result)
        return jsonify({
          "previousQuestions": data['previous_questions'],
          "question": choice
        })

# handling of earch error depending on their code status
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
          "success": False,
          "error": 400,
          "message": 'bad request'
        }), 400

    @app.errorhandler(404)
    def resource_not_found(error):
        return jsonify({
          "success": False,
          "error": 400,
          "message": 'resource not found'
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
          "success": False,
          "error": 405,
          "message": 'method not allowed'
        }), 405

    @app.errorhandler(422)
    def unprocessible(error):
        return jsonify({
          "success": False,
          "error": 422,
          "message": 'unprocessible'
        }), 422

    @app.errorhandler(500)
    def unprocessible(error):
        return jsonify({
          "success": False,
          "error": 500,
          "message": 'server error'
        }), 500

    return app
