# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired, Optional, Length, Email
from flask_ckeditor import upload_success, upload_fail
from flask_wtf.file import FileField, FileRequired, FileAllowed

from albumy.models import Category


class DescriptionForm(FlaskForm):
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    submit = SubmitField()


class Can_commentForm(FlaskForm):
    can_comment = BooleanField('Can_comment', validators=[Optional()])
    submit = SubmitField()


class TagForm(FlaskForm):
    tag = StringField('Add Tag (use space to separate)', validators=[Optional(), Length(0, 64)])
    submit = SubmitField()


class CommentForm(FlaskForm):
    body = TextAreaField('', validators=[DataRequired()])
    submit = SubmitField()


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(1, 60)])
    category = SelectField('Category', coerce=int, default=1)
    body = CKEditorField('Body', validators=[DataRequired()])
    submit = SubmitField()

    # 下面这段在form里用来出select框
    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(category.id, category.name)
                                 for category in Category.query.order_by(Category.name).all()]


class UploadForm(FlaskForm):
    excel = FileField('Upload Excel', validators=[FileRequired(),
                                                  FileAllowed(['xlsx'])])
    # submit = SubmitField()
    # 单个表单多个提交按钮
    save = SubmitField('Save')
    publish = SubmitField('Publish')


class EmailForm(FlaskForm):
    to = StringField('To', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired()])
    body = TextAreaField('Body', validators=[DataRequired()])
    submit_smtp = SubmitField('Send with SMTP')
    submit_async = SubmitField('Send with SMTP asynchronously异步发送')