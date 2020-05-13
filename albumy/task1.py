import celery
from flask import current_app, Blueprint
from flask_mail import Message

from albumy.extensions import db, mail



@celery.task
def add(x, y):
    # gg=explore5()
    return x + y


#
# @celery.task
# def send_smtp_mail(subject, to, body):
#     app = current_app._get_current_object()
#     message = Message(subject, recipients=[to], body=body)
#     app_ctx = app.app_context()
#     app_ctx.push()
#     with app.app_context():
#         mail.send(message)
#     app_ctx.pop()
