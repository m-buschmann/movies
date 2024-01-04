#https://www.imdb.com/title/tt
# Contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html

from flask import Flask, jsonify, render_template, request
from flask_login import current_user
from flask_user import login_required, UserManager
from sqlalchemy import func, desc
from models import db, User, Movie, MovieGenre, Tags, Links, Ratings
from read_data import check_and_read_data
import chromadb

# Initialize ChromaDB client
chroma_client = chromadb.Client()

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///movie_recommender.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-User settings
    USER_APP_NAME = "Movie Recommender"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = False  # Disable email authentication
    USER_ENABLE_USERNAME = True  # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = True  # Simplify register form

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary
user_manager = UserManager(app, db, User)  # initialize Flask-User management


@app.cli.command('initdb')
def initdb_command():
    global db
    """Creates the database tables."""
    check_and_read_data(db)
    print('Initialized the database.')

# The Home page is accessible to anyone
@app.route('/')
def home_page():
    # render home.html template
    return render_template("home.html")

@app.route('/update-rating', methods=['POST'])
@login_required  # User must be authenticated
def update_rating():
    try:
        rating = int(request.form.get('rating'))
        movieID = request.form.get('movie_id')
        print(movieID)
        # Save the new rating to the database
        new_rating = Ratings(id=current_user.id, movie_id=movieID, rating=rating)
        db.session.add(new_rating)
        db.session.commit()

        # Calculate the new average rating
        average_rating = (
            db.session.query(func.avg(Ratings.rating))
            .filter_by(movie_id=request.form.get('movie_id'))
            .scalar()
        )
        new_average = round(average_rating, 2) if average_rating is not None else None

        return jsonify({'newAverage': new_average})

    except Exception as e:
        print('Error updating rating:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500
    
# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/movies')
@login_required  # User must be authenticated
def movies_page():
    # String-based templates

    # first 10 movies
    movies =  Movie.query.join(Ratings).group_by(Movie.id).order_by(desc(func.avg(Ratings.rating))).limit(10).all()
       # Calculate average rating for each movie
    average = []
    for m in movies:
        
        average_rating = (
            db.session.query(func.avg(Ratings.rating))
            .filter_by(movie_id=m.id)
            .scalar()
        )
        # Assign the calculated average_rating to the movie
        average.append(round(average_rating, 2) if average_rating is not None else None)
    print(average)
    return render_template("movies.html", movies=movies, average = average)


# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)
