from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import os
import requests

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('TMDB_API_KEY')

# Determine the base directory
basedir = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'movies.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db = SQLAlchemy(app)
    Bootstrap5(app)

    # Ensure the instance folder exists
    instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)

    # Define the Movie model inside the create_app to ensure it's ready when db is initiated
    class Movie(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(250), unique=True, nullable=False)
        year = db.Column(db.Integer, nullable=False)
        description = db.Column(db.String(500), nullable=False)
        rating = db.Column(db.Float, nullable=True)
        ranking = db.Column(db.Integer, nullable=True)
        review = db.Column(db.String(500), nullable=True)
        img_url = db.Column(db.String(500), nullable=False)

    # Create the database and tables
    with app.app_context():
        db.create_all()

    class MovieSearchForm(FlaskForm):
        title = StringField('Movie Title', validators=[DataRequired()])
        submit = SubmitField('Search')

    @app.route("/", methods=["GET"])
    def home():
        movies = Movie.query.order_by(Movie.rating.desc()).all()
        for index, movie in enumerate(movies, start=1):
            movie.ranking = index
        db.session.commit()
        return render_template("index.html", movies=movies)

    @app.route("/add", methods=["GET", "POST"])
    def add_movie():
        form = MovieSearchForm()
        if form.validate_on_submit():
            return redirect(url_for('select_movie', title=form.title.data))
        return render_template("add.html", form=form)

    @app.route("/select", methods=["GET"])
    def select_movie():
        title = request.args.get('title')
        response = requests.get(
            f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={title}"
        )
        movies = response.json().get('results', [])
        return render_template("select.html", movies=movies)

    @app.route("/add_movie_details/<int:movie_id>", methods=["GET"])
    def add_movie_details(movie_id):
        response = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}"
        )
        movie_data = response.json()
        new_movie = Movie(
            title=movie_data['title'],
            year=movie_data['release_date'].split("-")[0] if movie_data['release_date'] else None,
            description=movie_data['overview'],
            img_url=f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit_movie', movie_id=new_movie.id))

    @app.route("/edit/<int:movie_id>", methods=["GET", "POST"])
    def edit_movie(movie_id):
        movie = Movie.query.get_or_404(movie_id)
        form = RateMovieForm(obj=movie)
        if form.validate_on_submit():
            movie.rating = form.rating.data
            movie.review = form.review.data
            db.session.commit()
            return redirect(url_for('home'))  # Redirect to home to recalculate rankings
        return render_template("edit.html", form=form, movie=movie)

    @app.route("/delete/<int:movie_id>")
    def delete_movie(movie_id):
        movie = Movie.query.get_or_404(movie_id)
        db.session.delete(movie)
        db.session.commit()
        return redirect(url_for('home'))

    class RateMovieForm(FlaskForm):
        rating = StringField('Rating', validators=[DataRequired()])
        review = StringField('Review', validators=[DataRequired()])
        submit = SubmitField('Submit')

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
