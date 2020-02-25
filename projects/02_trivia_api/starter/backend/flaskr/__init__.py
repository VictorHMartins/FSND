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
# I took the .format() from the tutorial, however I could find docs explaining it
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
  
  # '''
  # @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  # '''
  CORS(app) # Added CORS func to app instance


  # '''
  # @TODO: Use the after_request decorator to set Access-Control-Allow
  # '''

  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

  # '''
  # @TODO: COMPLETE
  # Create an endpoint to handle GET requests 
  # for all available categories.
  # '''

  @app.route('/categories', methods=['GET'])
  def get_categories():
    selection = Category.query.order_by(Category.id).all()
    current_categories = paginate(request,selection)
    types = [c['type'] for c in current_categories]


    return jsonify({
      "categories": types
    })


  # '''
  # @TODO: COMPLETE
  # Create an endpoint to handle GET requests for questions, 
  # including pagination (every 10 questions). 
  # This endpoint should return a list of questions, 
  # number of total questions, current category, categories. 

  # TEST: At this point, when you start the application
  # you should see questions and categories generated,
  # ten questions per page and pagination at the bottom of the screen for three pages.
  # Clicking on the page numbers should update the questions. 
  # '''

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
      
      return jsonify( {
        "questions": questions,
        "totalQuestions": total_questions,
        "categories": types
      })
    except:
      abort(400)


  # '''
  # @TODO: COMPLETE
  # Create an endpoint to DELETE question using a question ID. 

  # TEST: When you click the trash icon next to a question, the question will be removed.
  # This removal will persist in the database and when you refresh the page. 
  # '''
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
        })
    except:
      abort(400)
  
  # '''
  # @TODO: COMPLETE
  # Create an endpoint to POST a new question, 
  # which will require the question and answer text, 
  # category, and difficulty score.

  # TEST: When you submit a question on the "Add" tab, 
  # the form will clear and the question will appear at the end of the last page
  # of the questions list in the "List" tab.  
  # '''

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
      })
    except:
      abort(400)

  # '''
  # @TODO: COMPLETE
  # Create a POST endpoint to get questions based on a search term. 
  # It should return any questions for whom the search term 
  # is a substring of the question. 

  # TEST: Search by any phrase. The questions list will update to include 
  # only question that include that string within their question. 
  # Try using the word "title" to start. 
  # '''

  @app.route('/search', methods=['POST'])
  def search_questions():
    
    try:
      search = request.get_json()
      term = search['searchTerm']
      selection = Question.query.filter(Question.question.ilike(f'%{term}%')).all()
      result = paginate(request, selection)
      total_questions = len(result)

      if result[0] is None:
        abort(400)
      
      return jsonify({
      'questions': result,
      'totalQuestions': total_questions,
      'currentCategory': result[0]['category']
    })
    except:
      abort(404)




  # '''
  # @TODO: COMPLETE
  # Create a GET endpoint to get questions based on category. 

  # TEST: In the "List" tab / main screen, clicking on one of the 
  # categories in the left column will cause only questions of that 
  # category to be shown. 
  # '''
  try:
    @app.route('/categories/<int:id>/questions', methods=['GET'])
    def fetch_category_questions(id):

      selection = Question.query.join(Category, 
      Category.id == Question.category).filter(Question.category == id).all()
      questions = paginate(request, selection)
      total_questions = len(questions)
      current_category = id
      query = Category.query.all()
          
      return jsonify({
        "questions": questions,
        "totalQuestions": total_questions,
        "currentCategory": current_category
      })
  except:
    abort(400)

  # '''
  # @TODO: COMPLETE
  # Create a POST endpoint to get questions to play the quiz. 
  # This endpoint should take category and previous question parameters 
  # and return a random questions within the given category, 
  # if provided, and that is not one of the previous questions. 

  # TEST: In the "Play" tab, after a user selects "All" or a category,
  # one question at a time is displayed, the user is allowed to answer
  # and shown whether they were correct or not. 
  # '''

  @app.route('/quizzes', methods= ['POST'])
  def get_quizzes():
    data = request.get_json()
    previous_questions = data['previous_questions']
    category = data['quiz_category']['type']

    if category == 'click':
      questions = Question.query.all()
      result = paginate(request, questions)
      
      choice =  random.choice(result)
      while choice['id'] in previous_questions:
        choice =  random.choice(result)

    else:
      questions = Question.query.join(Category,
      Category.id == Question.category).filter(Category.type == category)
      result = paginate(request, questions)

      choice =  random.choice(result)
      while choice['id'] in previous_questions:
        choice =  random.choice(result)

        
    return jsonify({
      # "showAnswer": 
      "previousQuestions": data['previous_questions'],
      "question": choice

    })

  # '''
  # @TODO: COMPLETE
  # Create error handlers for all expected errors 
  # including 404 and 422. 
  # '''


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

    