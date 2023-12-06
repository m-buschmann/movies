import csv
from sqlalchemy.exc import IntegrityError
from models import Movie, MovieGenre, Tags

"""def check_and_read_data(db):
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

#def check_tags(db):
    #TODO: evl sortieren welche tags wir ausgeben wollen, nicht nur den ersten
    if Tags.query.count() == 0:
        # read tags from csv
        with open('data/tags.csv', newline='', encoding='utf8') as csvfile:
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
    print(f"Number of entries in the Tags table: {count_tags}")"""



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
                        n_movie = Movie(id=id, title=title)
                      
                        db.session.add(n_movie)
                        genres = row[2].split('|')  # genres is a list of genres
                        for genre in genres:  # add each genre to the movie_genre table
                            movie_genre = MovieGenre(movie_id=id, genre=genre)
                            db.session.add(movie_genre)
                        
                        movie_id = row[0]
                        # Assuming tags are in a separate CSV file named tags.csv with columns: movie_id, tags
                        tags_file_path = 'data/tags.csv'

                        with open(tags_file_path, newline='', encoding='utf8') as tags_csvfile:
                            tags_reader = csv.reader(tags_csvfile, delimiter=',')
                            for tags_row in tags_reader:
                                if tags_row[1] == movie_id:
                                    tags = tags_row[2]
                                    tags_list = tags.split(',')

                                    for tag in tags_list:
                                        n_tag = Tags(movie_id=movie_id, tag=tag.strip())
                                        db.session.add(n_tag)
                                        
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movies read")

import csv
from flask import Flask
from sqlalchemy.exc import IntegrityError
from models import db, Movie, MovieGenre, Tags

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie_recommender.sqlite'  # Update with your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


if __name__ == '__main__':
    with app.app_context():
        # Create the tables
        db.create_all()

        # Run your data check functions
        check_and_read_data(db)

        # Now you can perform other operations outside the app context, if needed
        count_tags = Tags.query.count()
        count_movies = Movie.query.count()
        print(f"Number of entries in the Tags table: {count_tags}")
        print(f"Number of entries in the Movies table: {count_movies}")
