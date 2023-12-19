import csv
from sqlalchemy.exc import IntegrityError
from models import db, Movie, MovieGenre, Tags, Links, Rating_users
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
                                        existing_tag = Tags.query.filter_by(movie_id=movie_id, tag=tag.strip()).first() #check that we have not doublicates
                                        if not existing_tag:
                                            n_tag = Tags(movie_id=movie_id, tag=tag.strip())
                                            db.session.add(n_tag)

                        links_file_path = 'data/links.csv'

                        with open(links_file_path, newline='', encoding='utf8') as links_csvfile:
                            link_reader = csv.reader(links_csvfile, delimiter=',')
                            for link_row in link_reader:
                                if link_row[0] == movie_id:
                                    imdb_id = Links(movie_id=movie_id, link = link_row[1])
                                    #print(link_row[1])
                                    db.session.add(imdb_id)
                        
                        ratings_file_path = 'data/ratings_small.csv'

                        with open(ratings_file_path, newline='', encoding='utf8') as ratings_csvfile:
                            ratings_reader = csv.reader(ratings_csvfile, delimiter=',')
                            for ratings_row in ratings_reader:
                                user_id = ratings_row[0]

                                # Check if the user already exists in the database
                                existing_user = db.session.query(Rating_users).filter_by(user_id=user_id).first()

                                if not existing_user:
                                    # Insert the user into the database
                                    new_user = Rating_users(user_id=user_id)
                                    db.session.add(new_user)

                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movies read")


if __name__ == '__main__':
    with app.app_context():
        # Create the tables
        db.create_all()

        # Run your data check functions
        check_and_read_data(db)

        # Now you can perform other operations outside the app context, if needed
        count_tags = Tags.query.count()
        count_movies = Movie.query.count()
        count_links = Links.query.count()
        count_users = Rating_users.query.count()
        print(f"Number of entries in the Tags table: {count_tags}")
        print(f"Number of entries in the Movies table: {count_movies}")
        print(f"Number of entries in the Links table: {count_links}")
        print(f"Number of entries in the Users table: {count_users}")

