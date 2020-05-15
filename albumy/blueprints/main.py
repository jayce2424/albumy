# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
import datetime
import os
import random
import time
import uuid
import hashlib

import xlrd
import pymysql

from flask import render_template, flash, redirect, url_for, current_app, \
    send_from_directory, request, abort, Blueprint, session
from flask_login import login_required, current_user
from flask_mail import Message
from markupsafe import Markup
from sqlalchemy.sql.expression import func

from albumy.decorators import confirm_required, permission_required
from albumy.extensions import db, mail
from albumy.forms.main import DescriptionForm, TagForm, CommentForm, Can_commentForm, PostForm, UploadForm, EmailForm, \
    UploadOweForm, UploadReceiveForm, OweSearchForm
from albumy.models import User, Photo, Tag, Follow, Collect, Comment, Notification, Post, Category, Order_info, Owenum
from albumy.notifications import push_comment_notification, push_collect_notification
from albumy.utils import rename_image, resize_image, redirect_back, flash_errors, allowed_file
from flask_ckeditor import upload_success, upload_fail
import requests
import json
from threading import Thread

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
        pagination = Photo.query \
            .join(Follow, Follow.followed_id == Photo.author_id) \
            .filter(Follow.follower_id == current_user.id) \
            .order_by(Photo.timestamp.desc()) \
            .paginate(page, per_page)
        photos = pagination.items
    else:
        pagination = None
        photos = None
    tags = Tag.query.join(Tag.photos).group_by(Tag.id).order_by(func.count(Photo.id).desc()).limit(10)
    return render_template('main/index.html', pagination=pagination, photos=photos, tags=tags, Collect=Collect)


@main_bp.route('/explore')
def explore():
    photos = Photo.query.order_by(func.random()).limit(12)
    return render_template('main/explore.html', photos=photos)


@main_bp.route('/explore2')
def explore2():
    URL_IP = 'http://httpbin.org/ip'
    response = requests.get(URL_IP)
    print('response headers:')
    print(response.headers)
    print('response body:')
    print(response.text)
    return response.text


@main_bp.route('/aikucun_get_token')
def aikucun_get_token():
    noncestr = ''.join(random.sample(
        ['z', 'y', 'x', 'w', 'v', 'u', 't', 's', 'r', 'q', 'p', 'o', 'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g', 'f', 'e',
         'd', 'c', 'b', 'a'], 5))
    dtime = datetime.datetime.now()
    ans_time = time.mktime(dtime.timetuple())
    print(ans_time)
    return noncestr
    # URL_IP = 'http://www.baidu.com'
    # response = requests.get(URL_IP)
    # print('response headers:')
    # print(response.headers)
    # print('response body:')
    # print(response.text)
    # return response.text


@main_bp.route('/aikucun_get_token1')
def aikucun_get_token1():
    dtime = datetime.datetime.now()
    ans_time = time.mktime(dtime.timetuple())
    dict2 = {'appid': '2c9089946996c698016999cac22b4265',
             'appsecret': '2c9089946996c698016999cac22b4266',
             'noncestr': ''.join(random.sample(
                 ['z', 'y', 'x', 'w', 'v', 'u', 't', 's', 'r', 'q', 'p', 'o', 'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g',
                  'f', 'e', 'd', 'c', 'b', 'a'], 5)),
             'timestamp': str(ans_time),  # python并不能像java一样，在做拼接的时候自动把类型转换为string类型
             'erp': 'E3',
             'erpversion': '20180226',
             'status': '9'
             }
    # 遍历字典的几种方法  https://www.cnblogs.com/stuqx/p/7291948.html
    for (key, value) in dict2.items():
        print(key + ':' + value)
    dict3 = sorted(dict2.items(), key=lambda dict2: dict2[0], reverse=False)  # False为升序
    url = ""
    # for (key, value) in dict3:
    #     print(key + ':' + value)
    url += '&'.join([str(key) + '=' + str(value) for key, value in dict3])
    print(url)
    sha = hashlib.sha1(url.encode('utf-8'))
    encrypts = sha.hexdigest()
    print(encrypts)
    bb = 'https://openapi.aikucun.com/api/v2/activity/list?'
    url = bb + url + '&sign=' + encrypts
    print(url)
    response = requests.get(url)
    return response.text


@main_bp.route('/explore_token')
def explore_token():
    # headers没用到
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "client_id": "dfc5b278d1ff0d77c7",
        "client_secret": "a50f8ffd2276fae731c4f35dd8714bbd",
        "authorize_type": "silent",
        "grant_id": "108929"
    }
    url = "https://open.youzanyun.com/auth/token"
    response = requests.post(url, json=payload)
    gg = json.loads(response.text)
    # sha = hashlib.sha1(res.encode('utf-8'))
    # encrypts = sha.hexdigest()
    return gg['data']['access_token']


@main_bp.route('/explore3')
def explore3():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    access_token = explore_token()
    url = "https://open.youzanyun.com/api/youzan.items.onsale.get/3.0.0?access_token=%s" % access_token
    response = requests.post(url, headers)
    return response.text


@main_bp.route('/lfa')
def lfa():
    return render_template('main/lfa.html')


@main_bp.route('/explore4/<tid>')
def explore4(tid):
    # payload = {"tid": "E20200413162037038100001"}
    payload = {"tid": tid}
    access_token = explore_token()
    url = "https://open.youzanyun.com/api/youzan.trade.get/4.0.0?access_token=%s" % access_token
    response = requests.post(url, data=payload)
    gg = json.loads(response.text)
    # print(gg)
    tid = gg['data']['full_order_info']['order_info']['tid']
    delivery_province = gg['data']['full_order_info']['address_info']['delivery_province']
    delivery_city = gg['data']['full_order_info']['address_info']['delivery_city']
    delivery_district = gg['data']['full_order_info']['address_info']['delivery_district']
    receiver_tel = gg['data']['full_order_info']['address_info']['receiver_tel']
    delivery_address = gg['data']['full_order_info']['address_info']['delivery_address']
    body = 'aini'
    order_info = Order_info(tid=tid, delivery_province=delivery_province, delivery_city=delivery_city,
                            delivery_district=delivery_district, receiver_tel=receiver_tel,
                            delivery_address=delivery_address)
    db.session.add(order_info)
    db.session.commit()
    # return gg['data']['order_promotion']['adjust_fee']
    return 'ff'


@main_bp.route('/explore5/')
def explore5():
    college1 = {"E20200413162037038100001", "E20200416090257000600001"}
    for c in college1:
        explore4(c)
    return 'ff'


@main_bp.route('/post/manage')
@permission_required('POST')
@login_required
def manage_post():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['BLUELOG_MANAGE_POST_PER_PAGE'])
    posts = pagination.items
    return render_template('main/manage_post.html', page=page, pagination=pagination, posts=posts)


@main_bp.route('/owenum', methods=['GET', 'POST'])
# @permission_required('POST')
@login_required
def owenum():
    form = OweSearchForm()
    if form.validate_on_submit():
        page = request.args.get('page', 1, type=int)
        pagination = Owenum.query.filter_by(sku=form.sku.data).order_by(Owenum.id).paginate(
            page, per_page=current_app.config['BLUELOG_MANAGE_POST_PER_PAGE'])
        owenums = pagination.items
        # print(Post.query.filter_by(title=form.username.data).order_by(Post.timestamp.desc()))
        # return render_template('main/manage_post.html', page=page, pagination=pagination, posts=posts)
        # form.sku.data=form.sku.data
        return render_template('main/owenum.html', form=form, page=page, pagination=pagination, owenums=owenums)
    page = request.args.get('page', 1, type=int)
    pagination = Owenum.query.order_by(Owenum.sku, Owenum.id).paginate(
        page, per_page=current_app.config['BLUELOG_MANAGE_POST_PER_PAGE'])
    owenums = pagination.items
    return render_template('main/owenum.html', page=page, pagination=pagination, owenums=owenums, form=form)


@main_bp.route('/post/<int:post_id>')
def show_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('main/post.html', post=post)


def random_filename(filename):
    ext = os.path.splitext(filename)[1]
    new_filename = uuid.uuid4().hex + ext
    return new_filename


def open_excel(ss):
    try:
        book = xlrd.open_workbook(ss)  # 文件名，把文件与py文件放在同一目录下
    except:
        print("open excel file failed!")
    try:
        sheet = book.sheet_by_name("Sheet1")  # execl里面的worksheet1
        return sheet
    except:
        print("locate worksheet in excel failed!")


def open_excel(filename):
    try:
        name = r"D:\NIO\albumy\uploads\%s" % filename
        book = xlrd.open_workbook(name)  # 文件名，把文件与py文件放在同一目录下
    except:
        print("open excel file failed!")
    try:
        sheet = book.sheet_by_name("Sheet1")  # execl里面的worksheet1
        return sheet
    except:
        print("locate worksheet in excel failed!")


def inserrt_process(sheet, filename):
    try:
        db = pymysql.connect(host="10.10.19.6", port=5000, user="root",
                             passwd="qwer1234.",
                             db="flask_albumy2")
    except:
        print("could not connect to mysql server")
    cursor = db.cursor()
    for i in range(1, sheet.nrows):  # 第一行是标题名，对应表中的字段名所以应该从第二行开始，计算机以0开始计数，所以值是1

        name = sheet.cell(i, 0).value  # 取第i行第0列
        data = sheet.cell(i, 1).value  # 取第i行第1列，下面依次类推
        print(name)
        print(data)
        value = (name, data)
        print(value)
        sql = "INSERT INTO gg(id,name)VALUES(%s,%s)"
        cursor.execute(sql, value)  # 执行sql语句
        db.commit()
    cursor.close()  # 关闭连接
    db.close()  # 关闭数据
    message = Markup(
        'Upload publish success:'
        '%s' % filename)
    flash(message, 'info')


def insert_owe_process(sheet, filename):
    try:
        db = pymysql.connect(host="10.10.19.6", port=5000, user="root",
                             passwd="qwer1234.",
                             db="flask_albumy2")
    except:
        print("could not connect to mysql server")
    cursor = db.cursor()
    for i in range(1, sheet.nrows):  # 第一行是标题名，对应表中的字段名所以应该从第二行开始，计算机以0开始计数，所以值是1

        sku = sheet.cell(i, 0).value  # 取第i行第0列
        yao = sheet.cell(i, 1).value  # 取第i行第1列，下面依次类推
        print(sku)
        print(yao)
        value = (sku, yao, yao)
        print(value)
        sql = "INSERT INTO owenum(sku,yao,owe)VALUES(%s,%s,%s)"
        print(sql)
        cursor.execute(sql, value)  # 执行sql语句
        db.commit()
    cursor.close()  # 关闭连接
    db.close()  # 关闭数据
    message = Markup(
        'Insert yao success:'
        '%s' % filename)
    flash(message, 'info')


def insert_receive_process(sheet, filename):
    try:
        db = pymysql.connect(host="10.10.19.6", port=5000, user="root",
                             passwd="qwer1234.",
                             db="flask_albumy2")
    except:
        print("could not connect to mysql server")
    cursor = db.cursor()
    # 先预检查
    for i in range(1, sheet.nrows):
        sku = sheet.cell(i, 0).value  # 取第i行第0列
        shiji = sheet.cell(i, 1).value  # 取第i行第1列，下面依次类推
        receive_date = sheet.cell(i, 2).value  # 取第i行第1列，下面依次类推
        # receive_date = int(receive_date)
        print(sku)
        print(shiji)
        print(receive_date)
        # exit()
        value = sku
        # print(value)
        sql = "select sum(owe) as sum from owenum where sku=%s ;"
        cursor.execute(sql, value)  # 执行sql语句
        ret = cursor.fetchone()
        # print(ret)  # 输出的ret是个tuple元组
        sum = ret[0]
        # 报错情况 555+443=998<4444  来的太多了   欠量永远比到货多
        if sum < shiji:
            message = Markup(
                'Insert yao %s error:'
                '欠量合计%s<本次入库%s' % (sku, sum, shiji))
            flash(message, 'danger')
            cursor.close()  # 关闭连接
            db.close()  # 关闭数据
            return 'error'
    for i in range(1, sheet.nrows):  # 第一行是标题名，对应表中的字段名所以应该从第二行开始，计算机以0开始计数，所以值是1

        sku = sheet.cell(i, 0).value  # 取第i行第0列
        shiji = sheet.cell(i, 1).value  # 取第i行第1列，下面依次类推
        receive_date = sheet.cell(i, 2).value  # 取第i行第1列，下面依次类推
        # receive_date = int(receive_date)
        print(sku)
        print(shiji)
        print(receive_date)
        # exit()
        value = sku
        # print(value)
        sql = "select sum(owe) as sum from owenum where sku=%s ;"
        cursor.execute(sql, value)  # 执行sql语句
        ret = cursor.fetchone()
        # print(ret)  # 输出的ret是个tuple元组
        sum = ret[0]
        # 报错情况 555+443=998<4444  来的太多了   欠量永远比到货多
        if sum < shiji:
            message = Markup(
                'Insert yao %s error:'
                '欠量合计%s<本次入库%s' % (sku, sum, shiji))
            flash(message, 'danger')
            cursor.close()  # 关闭连接
            db.close()  # 关闭数据
            return 'error'
        if sum >= shiji:
            sql = "select owe,id  from owenum where sku=%s and owe!=0 order by id limit 1;"
            cursor.execute(sql, value)  # 执行sql语句
            ret = cursor.fetchone()
            # print(ret)
            owe = ret[0]  # 这个查到的是最近第一笔欠量
            id = ret[1]
            # print(owe)
            # print(id)
            # exit()
            # 一次update就能搞定  555 > 444  欠量还存在 结束
            if owe >= shiji:
                value = (owe, shiji, receive_date, shiji, sku, id)
                sql = "update owenum set owe=%s-%s,receive_date=%s, shiji=%s where sku=%s  and id=%s "
                # print(sql)
                cursor.execute(sql, value)  # 执行sql语句
                db.commit()
                message = Markup(
                    'Update yao %s success:'
                    '欠量合计%s>本次入库%s并且一次就能满足' % (sku, owe, shiji))
                flash(message, 'success')
            # 一次update不能搞定  555 > 558  最近一笔欠量满足掉 第二笔没满足
            if owe < shiji:
                # 先满足掉第一笔  receive_date记录首次到货的时间
                value = (receive_date, shiji, sku, id)
                sql = "update owenum set owe=0,receive_date=%s,shiji=%s where sku=%s  and id=%s "
                # print(sql)
                cursor.execute(sql, value)  # 执行sql语句
                db.commit()
                # 开始处理第二笔
                left = shiji - owe  # 剩余待处理的 3 多了3
                value=(sku)
                sql = "select owe,id  from owenum where sku=%s and owe!=0 order by id limit 1;"
                cursor.execute(sql, value)  # 执行sql语句
                ret2 = cursor.fetchone()
                owe2 = ret2[0]  # 443
                id2 = ret2[1]  # 63
                while left > owe2:
                    value = (sku)
                    sql = "select owe,id  from owenum where sku=%s and owe!=0 order by id limit 1;"
                    cursor.execute(sql, value)  # 执行sql语句
                    ret = cursor.fetchone()
                    owe2 = ret2[0]  # 443
                    id2 = ret2[1]  # 63
                    value = (left, sku, id2)
                    sql = "update owenum set owe=0,receive_date=%s where sku=%s  and id=%s "
                    # print(sql)
                    cursor.execute(sql, value)  # 执行sql语句
                    db.commit()
                    left = left - owe2
                    value = (sku)
                    sql = "select owe,id  from owenum where sku=%s and owe!=0 order by id limit 1;"
                    cursor.execute(sql, value)  # 执行sql语句
                    ret2 = cursor.fetchone()
                    owe2 = ret2[0]  # 443
                    id2 = ret2[1]  # 63
                    # left= left - owe2
                # 结束 本次到货全部覆盖到欠量  3<443
                value = (owe2, left, left,sku, id2)
                sql = "update owenum set owe=%s-%s,receive_date=%s  where sku=%s  and id=%s "
                # print(sql)
                cursor.execute(sql, value)  # 执行sql语句
                db.commit()

    cursor.close()  # 关闭连接
    db.close()  # 关闭数据
    message = Markup(
        'Insert yao success:'
        '%s' % filename)
    flash(message, 'info')


# send email asynchronously
def _send_async_excel(app, sheet, filename):
    with app.app_context():
        inserrt_process(sheet, filename)


def send_async_excel(sheet, filename):
    app = current_app._get_current_object()  # if use factory (i.e. create_app()), get app like this
    thr = Thread(target=_send_async_excel, args=[app, sheet, filename])
    thr.start()
    return thr


@main_bp.route('/upload_excel', methods=['GET', 'POST'])
def upload_excel():
    form = UploadForm()
    if form.validate_on_submit():
        if form.save.data:  # 仅仅保存文件
            f = form.excel.data
            filename = random_filename(f.filename)  # 先定义 再使用 放前面
            f.save(os.path.join(current_app.config['BLUELOG_UPLOAD_PATH'], filename))
            message = Markup(
                'Upload success:'
                '%s' % filename)
            flash(message, 'info')
            # session['filenames'] = [filename]
        elif form.publish.data:  # 执行插入
            f = form.excel.data
            filename = random_filename(f.filename)  # 先定义 再使用 放前面
            f.save(os.path.join(current_app.config['BLUELOG_UPLOAD_PATH'], filename))

            sheet = open_excel(filename)

            inserrt_process(sheet, filename)
        else:
            f = form.excel.data
            filename = random_filename(f.filename)  # 先定义 再使用 放前面
            f.save(os.path.join(current_app.config['BLUELOG_UPLOAD_PATH'], filename))

            sheet = open_excel(filename)

            send_async_excel(sheet, filename)
            # flash从异步里挑出来
            message = Markup(
                'Upload publish success:'
                '%s' % filename)
            flash(message, 'info')

    return render_template('main/upload_excel.html', form=form)


@main_bp.route('/upload_owe', methods=['GET', 'POST'])
def upload_owe():
    form = UploadOweForm()
    if form.validate_on_submit():
        if form.save.data:  # 仅仅保存文件
            f = form.excel.data
            filename = random_filename(f.filename)  # 先定义 再使用 放前面
            f.save(os.path.join(current_app.config['BLUELOG_UPLOAD_PATH'], filename))

            sheet = open_excel(filename)

            insert_owe_process(sheet, filename)

    return render_template('main/upload_owe.html', form=form)


@main_bp.route('/upload_receive', methods=['GET', 'POST'])
def upload_receive():
    form = UploadReceiveForm()
    if form.validate_on_submit():
        if form.save.data:  # 仅仅保存文件
            f = form.excel.data
            filename = random_filename(f.filename)  # 先定义 再使用 放前面
            f.save(os.path.join(current_app.config['BLUELOG_UPLOAD_PATH'], filename))

            sheet = open_excel(filename)

            insert_receive_process(sheet, filename)

    return render_template('main/upload_receive.html', form=form)


# send over SMTP
def send_smtp_mail(subject, to, body):
    message = Message(subject, recipients=[to], body=body)
    mail.send(message)


# send email asynchronously
def _send_async_mail(app, message):
    with app.app_context():
        mail.send(message)


def send_async_mail(subject, to, body):
    app = current_app._get_current_object()  # if use factory (i.e. create_app()), get app like this
    message = Message(subject, recipients=[to], body=body)
    thr = Thread(target=_send_async_mail, args=[app, message])
    thr.start()
    return thr


@main_bp.route('/send_mail', methods=['GET', 'POST'])
def send_mail():
    form = EmailForm()
    if form.validate_on_submit():
        to = form.to.data
        subject = form.subject.data
        body = form.body.data
        if form.submit_smtp.data:
            send_smtp_mail(subject, to, body)
            method = request.form.get('submit_smtp')
        else:
            send_async_mail(subject, to, body)
            method = request.form.get('submit_async')

        flash('Email sent %s! Check your inbox.' % ' '.join(method.split()[1:]), 'info')
        return redirect(url_for('main.send_mail'))
    form.subject.data = 'Hello, World!'
    form.body.data = 'Across the Great Wall we can reach every corner in the world.'
    return render_template('main/send_mail.html', form=form)


@main_bp.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        title = form.title.data
        body = form.body.data
        category = Category.query.get(form.category.data)
        post = Post(title=title, body=body, category=category)
        # same with:
        # category_id = form.category.data
        # post = Post(title=title, body=body, category_id=category_id)
        db.session.add(post)
        db.session.commit()
        flash('Post created.', 'success')
        return redirect(url_for('main.show_post', post_id=post.id))
    return render_template('main/new_post.html', form=form)


@main_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    form = PostForm()
    post = Post.query.get_or_404(post_id)
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.body.data
        post.category = Category.query.get(form.category.data)
        db.session.commit()
        flash('Post updated.', 'success')
        return redirect(url_for('main.show_post', post_id=post.id))
    form.title.data = post.title
    form.body.data = post.body
    form.category.data = post.category_id
    return render_template('main/edit_post.html', form=form)


@main_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'success')
    return redirect_back()


@main_bp.route('/postupload', methods=['POST'])
def upload_image():
    f = request.files.get('upload')
    if not allowed_file(f.filename):
        return upload_fail('Image only!')
    f.save(os.path.join(current_app.config['BLUELOG_UPLOAD_PATH'], f.filename))
    url = url_for('.get_image', filename=f.filename)
    return upload_success(url, f.filename)


@main_bp.route('/')
def index_post():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_POST_PER_PAGE']
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=per_page)
    posts = pagination.items
    return render_template('main/index_post.html', pagination=pagination, posts=posts)


@main_bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if q == '':
        flash('Enter keyword about photo, user or tag.', 'warning')
        return redirect_back()

    category = request.args.get('category', 'photo')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_SEARCH_RESULT_PER_PAGE']
    if category == 'user':
        pagination = User.query.whooshee_search(q).paginate(page, per_page)
    elif category == 'tag':
        pagination = Tag.query.whooshee_search(q).paginate(page, per_page)
    else:
        pagination = Photo.query.whooshee_search(q).paginate(page, per_page)
    results = pagination.items
    return render_template('main/search.html', q=q, results=results, pagination=pagination, category=category)


@main_bp.route('/notifications')
@login_required
def show_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_NOTIFICATION_PER_PAGE']
    notifications = Notification.query.with_parent(current_user)
    filter_rule = request.args.get('filter')
    if filter_rule == 'unread':
        notifications = notifications.filter_by(is_read=False)

    pagination = notifications.order_by(Notification.timestamp.desc()).paginate(page, per_page)
    notifications = pagination.items
    return render_template('main/notifications.html', pagination=pagination, notifications=notifications)


@main_bp.route('/notification/read/<int:notification_id>', methods=['POST'])
@login_required
def read_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if current_user != notification.receiver:
        abort(403)

    notification.is_read = True
    db.session.commit()
    flash('Notification archived.', 'success')
    return redirect(url_for('.show_notifications'))


@main_bp.route('/notifications/read/all', methods=['POST'])
@login_required
def read_all_notification():
    for notification in current_user.notifications:
        notification.is_read = True
    db.session.commit()
    flash('All notifications archived.', 'success')
    return redirect(url_for('.show_notifications'))


@main_bp.route('/uploads/<path:filename>')
def get_image(filename):
    return send_from_directory(current_app.config['ALBUMY_UPLOAD_PATH'], filename)


@main_bp.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)


@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@confirm_required
@permission_required('UPLOAD')
def upload():
    if request.method == 'POST' and 'file' in request.files:
        f = request.files.get('file')
        filename = rename_image(f.filename)
        f.save(os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename))
        filename_s = resize_image(f, filename, current_app.config['ALBUMY_PHOTO_SIZE']['small'])
        filename_m = resize_image(f, filename, current_app.config['ALBUMY_PHOTO_SIZE']['medium'])
        photo = Photo(
            filename=filename,
            filename_s=filename_s,
            filename_m=filename_m,
            author=current_user._get_current_object()
        )
        db.session.add(photo)
        db.session.commit()
    return render_template('main/upload.html')


@main_bp.route('/photo/<int:photo_id>')
def show_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(photo).order_by(Comment.timestamp.asc()).paginate(page, per_page)
    comments = pagination.items

    comment_form = CommentForm()
    description_form = DescriptionForm()
    tag_form = TagForm()
    can_comment_form = Can_commentForm()

    description_form.description.data = photo.description
    can_comment_form.can_comment.data = photo.can_comment
    return render_template('main/photo.html', photo=photo, comment_form=comment_form,
                           description_form=description_form, tag_form=tag_form, can_comment_form=can_comment_form,
                           pagination=pagination, comments=comments)


@main_bp.route('/photo/n/<int:photo_id>')
def photo_next(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo_n = Photo.query.with_parent(photo.author).filter(Photo.id < photo_id).order_by(Photo.id.desc()).first()

    if photo_n is None:
        flash('This is already the last one.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))
    return redirect(url_for('.show_photo', photo_id=photo_n.id))


@main_bp.route('/photo/p/<int:photo_id>')
def photo_previous(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo_p = Photo.query.with_parent(photo.author).filter(Photo.id > photo_id).order_by(Photo.id.asc()).first()

    if photo_p is None:
        flash('This is already the first one.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))
    return redirect(url_for('.show_photo', photo_id=photo_p.id))


@main_bp.route('/collect/<int:photo_id>', methods=['POST'])
@login_required
@confirm_required
@permission_required('COLLECT')
def collect(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user.is_collecting(photo):
        flash('Already collected.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))

    current_user.collect(photo)
    flash('Photo collected.', 'success')
    if current_user != photo.author and photo.author.receive_collect_notification:
        push_collect_notification(collector=current_user, photo_id=photo_id, receiver=photo.author)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/uncollect/<int:photo_id>', methods=['POST'])
@login_required
def uncollect(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if not current_user.is_collecting(photo):
        flash('Not collect yet.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))

    current_user.uncollect(photo)
    flash('Photo uncollected.', 'info')
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/report/comment/<int:comment_id>', methods=['POST'])
@login_required
@confirm_required
def report_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.flag += 1
    db.session.commit()
    flash('Comment reported.', 'success')
    return redirect(url_for('.show_photo', photo_id=comment.photo_id))


@main_bp.route('/report/photo/<int:photo_id>', methods=['POST'])
@login_required
@confirm_required
def report_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo.flag += 1
    db.session.commit()
    flash('Photo reported.', 'success')
    return redirect(url_for('.show_photo', photo_id=photo.id))


@main_bp.route('/photo/<int:photo_id>/collectors')
def show_collectors(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_USER_PER_PAGE']
    pagination = Collect.query.with_parent(photo).order_by(Collect.timestamp.asc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('main/collectors.html', collects=collects, photo=photo, pagination=pagination)


@main_bp.route('/photo/<int:photo_id>/description', methods=['POST'])
@login_required
def edit_description(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)

    form = DescriptionForm()
    if form.validate_on_submit():
        photo.description = form.description.data
        db.session.commit()
        flash('Description updated.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/photo/<int:photo_id>/can_comment', methods=['POST'])
@login_required
def edit_can_comment(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)

    form = Can_commentForm()
    if form.validate_on_submit():
        photo.can_comment = form.can_comment.data
        db.session.commit()
        flash('Can_comment updated.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/photo/<int:photo_id>/comment/new', methods=['POST'])
@login_required
@permission_required('COMMENT')
def new_comment(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)
    form = CommentForm()
    if form.validate_on_submit():
        body = form.body.data
        author = current_user._get_current_object()
        comment = Comment(body=body, author=author, photo=photo)

        replied_id = request.args.get('reply')
        if replied_id:
            comment.replied = Comment.query.get_or_404(replied_id)
            if comment.replied.author.receive_comment_notification:
                push_comment_notification(photo_id=photo.id, receiver=comment.replied.author)
        db.session.add(comment)
        db.session.commit()
        flash('Comment published.', 'success')

        if current_user != photo.author and photo.author.receive_comment_notification:
            push_comment_notification(photo_id, receiver=photo.author, page=page)

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id, page=page))


@main_bp.route('/photo/<int:photo_id>/tag/new', methods=['POST'])
@login_required
def new_tag(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)

    form = TagForm()
    if form.validate_on_submit():
        for name in form.tag.data.split():
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
            if tag not in photo.tags:
                photo.tags.append(tag)
                db.session.commit()
        flash('Tag added.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/set-comment/<int:photo_id>', methods=['POST'])
@login_required
def set_comment(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)

    if photo.can_comment:
        photo.can_comment = False
        flash('Comment disabled', 'info')
    else:
        photo.can_comment = True
        flash('Comment enabled.', 'info')
    db.session.commit()
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/reply/comment/<int:comment_id>')
@login_required
@permission_required('COMMENT')
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(
        url_for('.show_photo', photo_id=comment.photo_id, reply=comment_id,
                author=comment.author.name) + '#comment-form')


@main_bp.route('/delete/photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)

    db.session.delete(photo)
    db.session.commit()
    flash('Photo deleted.', 'info')

    photo_n = Photo.query.with_parent(photo.author).filter(Photo.id < photo_id).order_by(Photo.id.desc()).first()
    if photo_n is None:
        photo_p = Photo.query.with_parent(photo.author).filter(Photo.id > photo_id).order_by(Photo.id.asc()).first()
        if photo_p is None:
            return redirect(url_for('user.index', username=photo.author.username))
        return redirect(url_for('.show_photo', photo_id=photo_p.id))
    return redirect(url_for('.show_photo', photo_id=photo_n.id))


@main_bp.route('/delete/comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user != comment.author and current_user != comment.photo.author \
            and not current_user.can('MODERATE'):
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'info')
    return redirect(url_for('.show_photo', photo_id=comment.photo_id))


@main_bp.route('/tag/<int:tag_id>', defaults={'order': 'by_time'})
@main_bp.route('/tag/<int:tag_id>/<order>')
def show_tag(tag_id, order):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    order_rule = 'time'
    pagination = Photo.query.with_parent(tag).order_by(Photo.timestamp.desc()).paginate(page, per_page)
    photos = pagination.items

    if order == 'by_collects':
        photos.sort(key=lambda x: len(x.collectors), reverse=True)
        order_rule = 'collects'
    return render_template('main/tag.html', tag=tag, pagination=pagination, photos=photos, order_rule=order_rule)


@main_bp.route('/delete/tag/<int:photo_id>/<int:tag_id>', methods=['POST'])
@login_required
def delete_tag(photo_id, tag_id):
    tag = Tag.query.get_or_404(tag_id)
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)
    photo.tags.remove(tag)
    db.session.commit()

    if not tag.photos:
        db.session.delete(tag)
        db.session.commit()

    flash('Tag deleted.', 'info')
    return redirect(url_for('.show_photo', photo_id=photo_id))
