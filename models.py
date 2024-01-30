import os
from datetime import datetime

from dotenv import load_dotenv, find_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

DB_NAME = os.environ.get("DB_NAME")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = "sqlite:///{}".format(os.path.join(PROJECT_DIR, DB_NAME))

db = SQLAlchemy()


def setup_db(app):
    """
    setup_db(app)
        binds a flask application and a SQLAlchemy service
    """
    with app.app_context():
        app.config['SQLALCHEMY_DATABASE_URI'] = DB_PATH
        app.config['SQLALCHEMY_NOTIFICATIONS'] = False
        db.app = app
        db.init_app(app)


def db_drop_and_create_all(app):
    """
    db_drop_and_create_all()
        drops the database tables and starts fresh
        can be used to initialize a clean database
        !!NOTE you can change the database_filename variable to have multiple versions of a database
    """
    with app.app_context():
        db.drop_all()
        db.create_all()


post_tags = db.Table(
    "post_tags",
    db.Column("tag_id", db.ForeignKey("tags.id")),
    db.Column("post_id", db.ForeignKey("posts.id"))
)


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(), nullable=False)
    short_description = db.Column(db.Text(), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    is_active = db.Column(db.Boolean(), default=True)
    pic = db.Column(db.String(), nullable=False)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow())
    date_modified = db.Column(db.DateTime(), default=datetime.utcnow())
    views = db.Column(db.Integer(), default=0)
    shares = db.Column(db.Integer(), default=0)
    likes = db.Column(db.Integer(), default=0)

    tags = db.relationship('Tag', secondary=post_tags, lazy='subquery',
                           backref=db.backref('posts', lazy=True), single_parent=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', lazy=True, backref='post')

    def short(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.short_description,
            "pic": self.pic,
            "date": self.date_added.strftime('%Y-%m-%d %H:%M:%S'),
            "views": self.views,
            "likes": self.likes,
            "tags": [tag.name for tag in self.tags],
        }


class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=False)

    def __str__(self):
        return f"<Tag {self.id} | {self.name}>"

    def format(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer(), primary_key=True)
    author = db.Column(db.String(), default="<Anonymous User>")
    content = db.Column(db.Text(), nullable=False)
    date_added = db.Column(db.DateTime(), default=datetime.utcnow())

    post_id = db.Column(db.Integer(), db.ForeignKey('posts.id'))


class Machine(db.Model):
    __tablename__ = 'machines'

    id = db.Column(db.Integer(), primary_key=True)
    machine_type = db.Column(db.String())

    name = db.Column(db.Integer(), nullable=False)
    desc = db.Column(db.Text(), nullable=False)
    price = db.Column(db.Float(), nullable=False)

    # Inspection Report
    model = db.Column(db.String(), nullable=False)
    mfg_year = db.Column(db.Integer(), nullable=False)
    manufacturer = db.Column(db.String(), nullable=False)
    hours = db.Column(db.Integer(), nullable=False)
    weight = db.Column(db.Integer(), nullable=False)
    engine_type = db.Column(db.String(), nullable=False)
    oil_type = db.Column(db.String(), nullable=False)
    condition = db.Column(db.String(), nullable=False)

    date_added = db.Column(db.DateTime, default=datetime.now())
    date_updated = db.Column(db.DateTime, default=datetime.now())
    images = db.relationship('ImagePath', backref='machine', lazy=True)


class ImagePath(db.Model):
    __tablename__ = 'image_paths'

    id = db.Column(db.Integer(), primary_key=True)
    path = db.Column(db.String(), nullable=False)
    machine_id = db.Column(db.Integer(), db.ForeignKey('machines.id'), nullable=False)
