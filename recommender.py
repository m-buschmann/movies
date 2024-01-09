# Contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html

from flask import Flask, render_template, request, url_for,jsonify
from flask_user import login_required, UserManager, current_user
from flask_paginate import Pagination, get_page_parameter

from models import db, User, Movie, MovieGenre, MovieLinks, MovieTags, Ratings
from read_data import check_and_read_data

from datetime import datetime
import pandas as pd
import traceback

from lenskit_tf import BPR
import pickle
import os

# import sleep from python
from time import sleep

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///movie_recommender.sqlite'  # File-based SQL database 
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-User settings
    USER_APP_NAME = "Movie Ratommender"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = False  # Disable email authentication
    USER_ENABLE_USERNAME = True  # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = True  # Simplify register form

    # make sure we redirect to home view, not /
    # (otherwise paths for registering, login and logout will not work on the server)
    USER_AFTER_LOGIN_ENDPOINT = 'home_page'
    USER_AFTER_LOGOUT_ENDPOINT = 'home_page'
    USER_AFTER_REGISTER_ENDPOINT = 'home_page'
    USER_AFTER_CONFIRM_ENDPOINT = 'home_page'

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary
user_manager = UserManager(app, db, User)  # initialize Flask-User management

# Get the directory of the current script
current_directory = os.path.dirname(os.path.realpath(__file__))

# Define the relative path to the model file
MODEL_PATH = os.path.join(current_directory, 'instance', 'BPR_model.pkl')

@app.errorhandler(500)
def internal_error(exception):
   return "<pre>"+traceback.format_exc()+"</pre>"

@app.cli.command('initdb')
def initdb_command():
    global db
    """Creates the database tables."""
    check_and_read_data(db)
    print('Initialized the database.')

@app.cli.command('fitBPR')
def fitBPR_command():
    global db
    """Fits the BPR model. Takes a few minutes."""

    df = pd.read_sql(db.session.query(Ratings.user_id, Ratings.movie_id, Ratings.rating).statement, con= db.session.connection())
    df = df.rename(columns={'user_id': 'user', 'movie_id': 'item'})

    model = BPR(epochs = 200, batch_size = 20000).fit(df)

    # Save the model to a file using pickle
    with open(MODEL_PATH, 'wb') as model_file:
        pickle.dump(model, model_file)

# The Home page is accessible to anyone
@app.route('/')
def home_page():
    # render home.html template
    return render_template("home.html")


# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/movies')
@login_required  # User must be authenticated
def movies_page():

    try:
        page = request.args.get(get_page_parameter(), type=int, default=1) #getting page number from url
    
        total = db.session.query(Movie.id).count() #counting total number of movies
        per_page = 20 #number of movies shown per page

        pagination = Pagination(page=page, total=total, per_page=per_page, css_framework='bootstrap4') #creating pagination object

        movies = db.session.query(Movie, MovieLinks).join(MovieLinks).order_by(Movie.title)#querying movies from database
        movies = movies.paginate(page=page, per_page=per_page) #paginating them

        return render_template( "movies.html", movies = movies, pagination=pagination, db = db, user = current_user.id, Ratings = Ratings, MovieTags = MovieTags) #rendering movies.html template with movies and pagination object

    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")

@app.route('/reset', methods=['POST'])
@login_required  # User must be authenticated
def reset():
    # get data from form
    movieid = request.form.get('movieId')
    userid = current_user.id

    #check if rating already exists
    rating = Ratings.query.filter(Ratings.user_id == userid, Ratings.movie_id == movieid).first()

    if rating: 
        # save rating to database
        print(rating)
        db.session.delete(rating)
        db.session.commit()

    #TODO add loading screen

    return jsonify({"status": "success", "message": "Rating submitted successfully"})

@app.route('/rate', methods=['POST'])
@login_required  # User must be authenticated
def rate():
    # get data from form
    movieid = request.form.get('movieId')
    rating_value = request.form.get('rating')
    userid = current_user.id

    print("Rate {} for {} by {}".format(rating_value, movieid, userid))

    #check if rating already exists
    rating = Ratings.query.filter(Ratings.user_id == userid, Ratings.movie_id == movieid).first()

    if not rating: 
        # save rating to database
        new_rate = Ratings(user_id=userid, movie_id=movieid, rating=rating_value, timestamp=datetime.now())
        print(rating)
        db.session.add(new_rate)
        db.session.commit()

    #TODO add loading screen

    return jsonify({"status": "success", "message": "Rating submitted successfully"})

@app.route('/recommendations')
@login_required  # User must be authenticated
def recommendations():

    RECOMMENDATIONS = 10

    # get user id
    user = current_user.id

    with open(MODEL_PATH,'rb') as model_file:
        loaded_model = pickle.load(model_file)
    
    # get all movies that the current user has not rated using outer join
    movies = db.session.query(Movie.id).outerjoin(Ratings, (Ratings.movie_id == Movie.id) & (Ratings.user_id == user)).filter(Ratings.id == None).join(MovieLinks, (Movie.id == MovieLinks.movie_id))
    movies = [movie.id for movie in movies]

    # get all ratings for the current user
    ratings = pd.read_sql( db.session.query(Ratings.rating).filter(Ratings.user_id == user).order_by(Ratings.movie_id).statement, con= db.session.connection())
    ratings = ratings.squeeze() # put them in a pd.Series

    recom_idx = loaded_model.predict_for_user(user, movies) # get recommendations for the current user
    recom_idx = recom_idx.sort_values(ascending=False)[:RECOMMENDATIONS]#sort the series by value#
    
    percentage = list(recom_idx)

    # Multiply each element in the percentage list by 100 to convert to percentage
    percentage = [x * 100 for x in percentage]

    # Round each element in the percentage list to 2 decimal places
    percentage = [round(x, 2) for x in percentage]

    # Convert the rounded list to a string with 2 decimal places
    percentage = ", ".join(["{:.2f}%".format(x) for x in percentage])
    print(percentage)

    mov_links = db.session.query(Movie, MovieLinks).join(MovieLinks, (Movie.id == MovieLinks.movie_id)) #get the movies from the database
    recom = [mov_links.filter(Movie.id == idx).first() for idx in recom_idx.index]

    return render_template("recommendations.html", movies = recom, db = db, user = current_user.id, Ratings = Ratings, MovieTags = MovieTags, percentage = percentage)

@app.route('/my_ratings')
@login_required  # User must be authenticated
def my_ratings():

    page = request.args.get(get_page_parameter(), type=int, default=1) #getting page number from url
 
    per_page = 20 #number of movies shown per page

    user = current_user.id

    #find all movies that the user has rated

    movies = db.session.query(Movie, MovieLinks).outerjoin(Ratings, (Ratings.movie_id == Movie.id) & (Ratings.user_id == user)).filter(Ratings.id != None).join(MovieLinks, (Movie.id == MovieLinks.movie_id))

    pagination = Pagination(page=page, total=len(movies.all()), per_page=per_page, css_framework='bootstrap4') #creating pagination object

    movies = movies.paginate(page=page, per_page=per_page) #paginating them

    return render_template("movies.html", movies = movies, pagination=pagination, db = db, user = user, Ratings = Ratings, MovieTags = MovieTags) #rendering movies.html template with movies and pagination object

# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)
