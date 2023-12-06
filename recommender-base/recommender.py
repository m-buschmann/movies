# Containts parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html
#
# This file contains an example Flask-User application.
# To keep the example simple, we are applying some unusual techniques:
# - Placing everything in one file
# - Using class-based configuration (instead of file-based configuration)

import csv
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_user import login_required, UserManager, UserMixin


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


# Create Flask app load app.config
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')
app.app_context().push()

# Initialize Flask-SQLAlchemy
db = SQLAlchemy(app)

# Define the User data-model.
# NB: Make sure to add flask_user UserMixin as this adds additional fields and properties required by Flask-User
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    username = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    email_confirmed_at = db.Column(db.DateTime())

    # User information
    first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')


class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
    genres = db.relationship('MovieGenre', backref='movie', lazy=True)
    tags = db.relationship('Tags', backref='movie', lazy=True)

class MovieGenre(db.Model):
    __tablename__ = 'movie_genres'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    genre = db.Column(db.String(255), nullable=False, server_default='')

class Tags(db.Model):
    __tablename__ = 'movie_tags'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    tag = db.Column(db.String(255), nullable=False, server_default='')


def check_and_read_data(db):
    # check if we have movies in the database
    # read data if database is empty
    if Movie.query.count() == 0:
        # read movies from csv
        with open('C:\\Users\\j k\\Documents\\uni\\semester5\\aiweb\\aiweb\\movies\\movies-1\\recommender-base\\data\\movies.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        id = row[0]
                        title = row[1]
                        n_movie = Movie(id=id, title=title)
                      
                        db.session.add(n_movie)
                        genres = row[2].split('|')  # genres is a list of genres
                        for genre in genres:  # add each genre to the movie_genre table
                            movie_genre = MovieGenre(movie_id=id, genre=genre)
                            db.session.add(movie_genre)
                        db.session.commit()  # save data to database
                        movie_id = row[0]
                        # Assuming tags are in a separate CSV file named tags.csv with columns: movie_id, tags
                        tags_file_path = 'C:\\Users\\j k\\Documents\\uni\\semester5\\aiweb\\aiweb\\movies\\movies-1\\recommender-base\\data\\tags.csv'

                        with open(tags_file_path, newline='', encoding='utf8') as tags_csvfile:
                            tags_reader = csv.reader(tags_csvfile, delimiter=',')
                            for tags_row in tags_reader:
                                if tags_row[1] == movie_id:
                                    tags = tags_row[2]
                                    tags_list = tags.split(',')

                                    for tag in tags_list:
                                        n_tag = Tags(movie_id=movie_id, tag=tag.strip())
                                        db.session.add(n_tag)
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movies read")

def check_tags(db):
    #TODO: evl sortieren welche tags wir ausgeben wollen, nicht nur den ersten
    if Tags.query.count() == 0:
        # read movies from csv
        with open("C:\\Users\\j k\\Documents\\uni\\semester5\\aiweb\\aiweb\\movies\\movies-1\\recommender-base\\data\\tags.csv", newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        id = row[1]
                        tag = row[2]
                        tags = Tags(id=id, tag=tag)
                        db.session.add(tags)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        #print("Ignoring duplicate movieID: " + id)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " tags read")
    count_tags = Tags.query.count()
    print(f"Number of entries in the Tags table: {count_tags}")


#count_tags = Movie.query.count()
#print(f"Number of entries in the Tags table: {count_tags}")
# Create all database tables
db.create_all()
check_and_read_data(db)
#check_tags(db)



"""# Fetch all tags from the database
all_tags = Tags.query.all()

# Print the tags
for tag in all_tags:
    print(f"Tag ID: {tag.id}, Movie ID: {tag.movie_id}, Tag: {tag.tag}")"""

# Setup Flask-User and specify the User data-model
user_manager = UserManager(app, db, User)

# The Home page is accessible to anyone
@app.route('/')
def home_page():
    # render home.html template
    return render_template("home.html")

# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/movies')
@login_required  # User must be authenticated
def movies_page():
    # String-based templates

    # first 10 movies
    movies = Movie.query.limit(10).all()
    tags = Tags.query.all()

    # only Romance movies
    # movies = Movie.query.filter(Movie.genres.any(MovieGenre.genre == 'Romance')).limit(10).all()

    # only Romance AND Horror movies
    # movies = Movie.query\
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Romance')) \
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Horror')) \
    #     .limit(10).all()

    return render_template("movies.html", movies=movies, tags = tags)


# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)


'''
include more of the data: 
tags, ratings, links table (create link from time table )
'''