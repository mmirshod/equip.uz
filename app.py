import os
import uuid
from os import environ as env
from os.path import join
from urllib.parse import urlencode, quote_plus

from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, render_template, session, url_for, request
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename

from models import setup_db, db_drop_and_create_all, db, Post, Tag, Machine
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

setup_db(app)
db_drop_and_create_all(app)

ckeditor = CKEditor(app)

oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email"
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)


@app.route('/base')
def base():
    return render_template('base.html')


@app.route('/')
def index():
    posts = [_[0].short() for _ in
             db.session.execute(db.select(Post).order_by(Post.date_added.desc()).limit(6)).fetchall()]
    print(posts)
    return render_template("index.html", news=posts)


@app.route('/callback', methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session['user'] = token

    return redirect('/')


@app.route("/login")
def login():
    redirect_uri = url_for('callback', _external=True)
    return oauth.auth0.authorize_redirect(redirect_uri)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("index", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


@app.route("/add_news", methods=['GET', 'POST'])
def news_add():
    if request.method == 'POST' or request.method == 'post':
        pic = request.files.get('post_pic')
        pic_name = 'news/' + str(uuid.uuid4()) + "_" + secure_filename(pic.filename)
        pic.save(join(app.config['UPLOAD_FOLDER'], pic_name))

        tag_names = request.form.get('post_tags').split(',')
        tags = []
        for tag_name in tag_names:
            tag = db.session.execute(db.select(Tag).where(Tag.name == tag_name)).fetchone()[0]
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
                db.session.commit()

            tags.append(tag)

        post = Post(
            title=request.form.get('post_title'),
            short_description=request.form.get('post_short_desc'),
            content=request.form.get('post_content'),
            pic=pic_name,
        )

        post.tags.extend(tags)

        db.session.add(post)
        db.session.commit()
        return redirect(url_for('news_list'))

    return render_template('forms/add_news.html')


@app.route("/news/<int:news_id>/edit", methods=['GET', 'PUT'])
def news_edit(news_id: int):
    if request.method == 'PUT':
        post = db.get_or_404(Post, news_id)
        post.content = request.form.get('post_content')
        post.short_description = request.form.get('post_short_desc')
        post.title = request.form.get('post_title')

        os.remove(post.pic)
        new_pic = request.files.get('post_pic')
        pic_name = 'news/' + str(uuid.uuid4()) + "_" + secure_filename(new_pic.filename)
        new_pic.save(join(app.config['UPLOAD_FOLDER'], pic_name))
        post.pic = pic_name

        db.session.commit()
        return redirect(url_for('news_list'))

    return render_template('forms/edit_news.html')


@app.route("/news/<int:news_id>/delete", methods=['GET', 'DELETE'])
def news_delete(news_id: int):
    post = db.get_or_404(Post, news_id)
    os.remove(join(app.config['UPLOAD_FOLDER'], post.pic))

    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('news_list'))


@app.route('/news/<int:news_id>')
def news_detail(news_id: int) -> str:
    post = db.session.get(Post, news_id)

    return render_template('news-single.html',
                           post=post,
                           recent_news=[_[0].short() for _ in db.session.execute(
                                   db.select(Post).order_by(Post.date_added.desc()).limit(6)).fetchall()],
                           all_tags=[_[0].format for _ in db.session.execute(
                                   db.select(Tag).order_by(Tag.name.desc())).fetchall()]
                           )


@app.route("/news")
def news_list() -> str:
    return render_template("news-right-sidebar.html", posts=Post.query.all())


@app.route('/news/tag=<int:tag_id>')
def news_by_tag(tag_id: int):
    posts = db.session.execute(db.select(Post).filter(Post.tags.any(id=tag_id))).fetchall()
    print(posts)
    return render_template('news-right-sidebar.html', posts=[_[0] for _ in posts])


@app.route('/machines')
def machine_list():
    return render_template('projects.html', machines=db.session.execute(db.select(Machine)).scalars())


@app.route("/machines/<int:machine_id>")
def machine_detail(machine_id: int):
    return render_template('projects-single.html', machine=db.get_or_404(Machine, machine_id))


@app.route("/machines/add")
def machine_add():
    ...


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/team')
def team():
    return render_template('team.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.errorhandler(404)
def not_found(e):
    render_template('404.html')


if __name__ == '__main__':
    app.run(debug=True, ssl_context='adhoc')
