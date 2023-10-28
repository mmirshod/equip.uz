from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField, FileRequired


class NewsForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired()])
    content = CKEditorField(label="Content")
    img = FileField(label="Picture", validators=[FileRequired()])
    submit = SubmitField(label="Submit")


# class MachineForm(FlaskForm):
#     name
