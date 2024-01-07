import csv
from sqlalchemy.exc import IntegrityError
from models import db, Movie, MovieGenre, MovieLinks, MovieTags, Ratings, User
from flask import Flask, url_for
from datetime import date, datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie_recommender.sqlite'  # Update with your database URI #FIXME
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def check_and_read_data(db):
    # check if we have movies in the database
    # read data if database is empty
    if Movie.query.count() == 0:
        # read movies from csv
        with open(url_for('data', filename='movies.csv', newline='', encoding='utf8')) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # Skip the header line
            next(reader)

            print("Reading movies")
            for row in reader: 

                    try:
                        id = row[0]
                        title = row[1]
                        movie = Movie(id=id, title=title)
                        db.session.add(movie)
                        genres = row[2].split('|')  # genres is a list of genres

                        for genre in genres:  # add each genre to the movie_genre table
                            movie_genre = MovieGenre(movie_id=id, genre=genre)
                            db.session.add(movie_genre)
                        db.session.commit()  # save data to database
                        
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass

    if MovieLinks.query.count() == 0:   
        with open(url_for('data', filename='links.csv', newline='', encoding='utf8')) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # Skip the header line
            next(reader)

            print("Reading links")
            for row in reader:
                    try:
                        
                        #existing_movie = Movie.query.get(row[0]) # get movie with id = row[0]
                        #print(existing_movie)

                        link = MovieLinks(movie_id= row[0], imdb_link=f"http://www.imdb.com/title/tt{row[1]}", tmdb_link=f"https://www.themoviedb.org/movie/{row[2]}")
                        db.session.add(link)
                        db.session.commit()  # save data to database

                    except IntegrityError:
                        print("Ignoring duplicate link: " + row[0])
                        db.session.rollback()

    if MovieTags.query.count() == 0:
        with open(url_for('data', filename='tags.csv', newline='', encoding='utf8')) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # Skip the header line
            next(reader)

            print("Reading tags")
            for row in reader:
                    try:
                        tag = MovieTags(user_id= row[0], movie_id=row[1], tag=row[2], timestamp= datetime.fromtimestamp(int(row[3])))
                        db.session.add(tag)

                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate tag: " + row[0])
                        db.session.rollback()

    if Ratings.query.count() == 0:
        with open(url_for('data', filename='ratings.csv', newline='', encoding='utf8')) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            # Skip the header line
            next(reader)

            print("Reading ratings")
            for row in reader:
                    try:
                        rating = Ratings(user_id= row[0], movie_id=row[1], rating=row[2], timestamp= datetime.fromtimestamp(int(row[3])))
                        db.session.add(rating)

                         #Check if user exists in the database
                        existing_user = db.session.query(User).filter_by(id=row[0]).first()

                        if not existing_user:
                            new_user = User(id = row[0], username = f"user{row[0]}")
                            db.session.add(new_user)

                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate rating: " + row[0])
                        db.session.rollback()

if __name__ == '__main__':

    with app.app_context():
        db.create_all()
        check_and_read_data(db)

