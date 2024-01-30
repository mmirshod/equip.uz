import os
import uuid
from os import environ as env
from os.path import join
from urllib.parse import urlencode, quote_plus

from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, render_template, session, url_for, request
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename

from models import setup_db, db_drop_and_create_all, db, Post, Tag, Machine, ImagePath
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


@app.route("/news_add", methods=['GET', 'POST'])
def news_add():
    if request.method == 'POST' or request.method == 'post':
        pic = request.files.get('post_pic')
        pic_name = 'news/' + str(uuid.uuid4()) + "_" + secure_filename(pic.filename)
        pic.save(join(app.config['UPLOAD_FOLDER'], pic_name))

        tag_names = request.form.get('post_tags').split(',')
        tags = []
        for tag_name in tag_names:
            tag = db.session.execute(db.select(Tag).where(Tag.name == tag_name)).fetchone()
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
                           all_tags=[_[0].format() for _ in db.session.execute(
                                   db.select(Tag).order_by(Tag.name.desc())).fetchall()]
                           )


@app.route("/news")
def news_list() -> str:
    posts = [_[0].short() for _ in
             db.session.execute(db.select(Post).order_by(Post.date_added.desc()).limit(6)).fetchall()]
    return render_template("news-right-sidebar.html", news=posts)


@app.route("/prob")
def prob():
    return render_template("machienes/rollers/1.html")
@app.route("/prob1")
def prob1():
    return render_template("machienes/pavers/1.html")
@app.route("/prob2")
def prob2():
    return render_template("machienes/pavers/2.html")


@app.route('/news/tag=<int:tag_id>')
def news_by_tag(tag_id: int):
    posts = db.session.execute(db.select(Post).filter(Post.tags.any(id=tag_id))).fetchall()
    print(posts)
    return render_template('news-right-sidebar.html', posts=[_[0] for _ in posts])


@app.route('/machines', methods=['GET'])
def machine_list():
    machine_type = request.args.get('type', None)
    if machine_type:
        stmt = db.select(Machine).where(Machine.type.name == machine_type)
        machines = db.session.execute(stmt).scalars().all()

        return render_template('projects.html', machines=machines)

    return render_template('projects.html', machines=db.session.execute(db.select(Machine)).scalars())


@app.route("/machines/<int:machine_id>")
def machine_detail(machine_id: int):
    return render_template('projects-single.html', machine=db.get_or_404(Machine, machine_id))


@app.route('/machines/add', methods=['GET', 'POST'])
def machine_add():
    if request.method == 'POST':
        if 'images' not in request.files:
            raise Exception('No file part')

        images = request.files.getlist('images')
        condition = request.form.get('condition')
        engine = request.form.get('engine')
        oil_type = request.form.get('fuel')
        name = request.form.get('name')
        model = request.form.get('model')
        desc = request.form.get('description')
        price = float(request.form.get('cost'))
        mfg_year = int(request.form.get('mfg_year'))
        manufacturer = request.form.get('manufacturer')
        hours = int(request.form.get('hours'))
        weight = float(request.form.get('weight'))
        machine_type = request.form.get('type')
        image_objects = []

        c = 0
        for img in images:
            file_path = f'machines/{model}___{img.filename}___{str(c)}'
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], file_path))
            img_obj = ImagePath(
                path=file_path,
            )
            db.session.add(img_obj)
            image_objects.append(img_obj)
            c += 1

        machine = Machine(
            name=name,
            desc=desc,
            price=price,
            mfg_year=mfg_year,
            manufacturer=manufacturer,
            hours=hours,
            weight=weight,
            images=image_objects,
            machine_type=machine_type,
            model=model,
            oil_type=oil_type,
            engine_type=engine,
            condition=condition,
        )

        db.session.add(machine)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('forms/add_machienes.html')


@app.route("/machines/delete/<int:machine_id>")
def machine_delete(machine_id: int):
    ...


@app.route("/machines/edit/<int:machine_id>")
def machine_edit(machine_id: int):
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