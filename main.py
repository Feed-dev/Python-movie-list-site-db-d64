from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from dotenv import load_dotenv
import os

load_dotenv()  # This loads the environment variables from the .env file.

api_key = os.getenv('TMDB_API_KEY')
access_token = os.getenv('TMDB_API_READ_ACCESS_TOKEN')

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

    # Home route
    @app.route("/")
    def home():
        movies = Movie.query.order_by(Movie.ranking).all()
        return render_template("index.html", movies=movies)

    # Add movie route
    @app.route("/add", methods=["GET", "POST"])
    def add_movie():
        if request.method == "POST":
            new_movie = Movie(
                title=request.form["title"],
                year=request.form["year"],
                description=request.form["description"],
                img_url=request.form["img_url"]
            )
            db.session.add(new_movie)
            db.session.commit()
            return redirect(url_for('home'))
        return render_template("add.html")

    # Edit movie route using WTForms
    @app.route("/edit/<int:movie_id>", methods=["GET", "POST"])
    def edit_movie(movie_id):
        movie = Movie.query.get_or_404(movie_id)
        form = RateMovieForm(obj=movie)
        if form.validate_on_submit():
            movie.rating = form.rating.data
            movie.review = form.review.data
            db.session.commit()
            return redirect(url_for('home'))
        return render_template("edit.html", form=form, movie=movie)

    # Delete movie route
    @app.route("/delete/<int:movie_id>")
    def delete_movie(movie_id):
        movie = Movie.query.get_or_404(movie_id)
        db.session.delete(movie)
        db.session.commit()
        return redirect(url_for('home'))

    # Define the RateMovieForm using WTForms
    class RateMovieForm(FlaskForm):
        rating = StringField('Rating', validators=[DataRequired()])
        review = StringField('Review', validators=[DataRequired()])
        submit = SubmitField('Submit')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
