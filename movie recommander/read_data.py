import csv
from sqlalchemy.exc import IntegrityError
from models import db, Movie, MovieGenre, MovieLinks, MovieTags
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie_recommender.sqlite'  # Update with your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def check_and_read_data(db):
    # check if we have movies in the database
    # read data if database is empty
    if Movie.query.count() == 0:
        # read movies from csv
        with open('data/movies.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
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
                count += 1
                if count % 100 == 0:
                    print(count, " movies read")
        
        with open('data/links.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                    try:
                        
                        existing_movie = Movie.query.get(row[0])
                        print(existing_movie)

                        link = MovieLinks(movie_id= row[0], imdb_link=f"http://www.imdb.com/title/tt{row[1]}", tmdb_link=f"https://www.themoviedb.org/movie/{row[2]}")
                        db.session.add(link)

                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + row[0])
                        db.session.rollback()
                        pass

        with open('data/tags.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                    try:
                        
                        existing_movie = Movie.query.get(row[0])
                        print(existing_movie)

                        tag = MovieLinks(user_id= row[0], movie_id=row[1], tag=row[2], timestamp=row[3])
                        db.session.add(tag)

                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + row[0])
                        db.session.rollback()
                        pass

if __name__ == '__main__':

    with app.app_context():
        db.create_all()
        check_and_read_data(db)

