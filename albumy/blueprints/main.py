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
import xlwt
import pymysql

from flask import render_template, flash, redirect, url_for, current_app, \
    send_from_directory, request, abort, Blueprint, session
from flask_login import login_required, current_user
from flask_mail import Message
from markupsafe import Markup
from sqlalchemy.sql.expression import func, text, distinct

from albumy.decorators import confirm_required, permission_required
from albumy.extensions import db, mail, cache
from albumy.forms.main import DescriptionForm, TagForm, CommentForm, Can_commentForm, PostForm, UploadForm, EmailForm, \
    UploadOweForm, UploadReceiveForm, OweSearchForm, DxlSearchForm
from albumy.models import User, Photo, Tag, Follow, Collect, Comment, Notification, Post, Category, Order_info, Owenum, \
    Ab_jqx_dxl, Jxc_rj_202005, Jxc_rj_202004, Jxc_rj_202003, Jxc_rj_202002, Spjgb, Jxc_rj_202001, Jxc_rj_201912, \
    Jxc_rj_202006, Jxc_rj_202007, Jxc_rj_202008, Jxc_rj_202009, Jxc_rj_201911, Jxc_rj_201910, Jxc_rj_201909, Jxc_rj_201908
from albumy.notifications import push_comment_notification, push_collect_notification
from albumy.utils import rename_image, resize_image, redirect_back, flash_errors, allowed_file
from flask_ckeditor import upload_success, upload_fail
import requests
import json
from threading import Thread
from decimal import getcontext, Decimal
from jinja2 import Markup, Environment, FileSystemLoader

main_bp = Blueprint('main', __name__)


# 通过e3的计划任务变相实现albumy的计划任务
# 输出目前的时间
@main_bp.route('/e3')
def e3():
    order_info = Order_info(tid=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    db.session.add(order_info)
    db.session.commit()
    return 'e3'


@main_bp.route('/calc_dxl_JD_3')
def calc_dxl_JD_3():
    # lls = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sku).distinct().limit(30)
    lls = Jxc_rj_202008.query.with_entities(Jxc_rj_202008.sku, Jxc_rj_202008.sku_id).distinct().filter_by(
        ck_id=4).filter_by(date='2020-08-31').filter(Jxc_rj_202008.sl_qm != 0).all()
    # print(lls)
    i = 0
    for ll in lls:
        print(ll.sku)
        print(ll.sku_id)
        i = i + 1
        # return str(i)
        bbs = Jxc_rj_202006.query.filter_by(ck_id=4).filter_by(date='2020-06-01').filter_by(
            sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        if bbs:
            # print('33')
            # print(bbs.sl_qc)  # 错误  print(bbs['sl_qm'])
            qc1 = bbs.sl_qc
        else:
            qc1 = 0
        bbss = Jxc_rj_202008.query.filter_by(ck_id=4).filter_by(date='2020-08-31').filter_by(sku=ll.sku).first()
        if bbss:
            # print('44')
            # print(bbss.sl_qm)  # 错误  print(bbs['sl_qm'])
            qm1 = bbss.sl_qm
        else:
            qm1 = 0
        # 求和  User.query.with_entities(func.sum(User.id)).all()
        # jh1 = Jxc_rj_202003.query.filter_by(ck_id=4).filter_by(sku=ll.sku).with_entities(
        #     func.sum(Jxc_rj_202003.sl0_pf)).all()
        jh2 = Jxc_rj_202007.query.filter_by(ck_id=4).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202007.sl0_pf)).all()
        jh3 = Jxc_rj_202008.query.filter_by(ck_id=4).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202008.sl0_pf)).all()
        jh4 = Jxc_rj_202006.query.filter_by(ck_id=4).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202006.sl0_pf)).all()
        # print(jh1[0][0])
        # print(jh2)
        # print(jh3)
        # print(jh4)
        # if jh1[0][0]:
        #     jh1 = jh1[0][0]
        # else:
        jh1 = 0
        if jh2[0][0]:
            jh2 = jh2[0][0]
        else:
            jh2 = 0
        if jh3[0][0]:
            jh3 = jh3[0][0]
        else:
            jh3 = 0
        if jh4[0][0]:
            jh4 = jh4[0][0]
        else:
            jh4 = 0
        xs_s = jh1 + jh2 + jh3 + jh4
        # print(xs_s)
        # 计算滞销量
        last = min(max(qc1 - xs_s, 0), qm1)
        # 同步最新成本价
        # jg1 = Spjgb.query.filter_by(goods_id=ll.goods_id).all()
        # ggd = Jxc_rj_202005.query.filter_by(sku=ll.sku).first()
        # print(ggd.sku_id)
        ggd = Spjgb.query.filter_by(sku_id=ll.sku_id).first()
        # print(ggd.jg1)
        # 计算动销率
        if qc1 * ggd.jg1 == 0:  # 被除数为0
            res = 0
        else:
            ssd = qc1 * ggd.jg1
            ssdds = float(xs_s) * float(ggd.jg1)
            # 迫使您将浮点数转换为小数， 更精确  float是会四舍五入
            # dxl = Decimal(str(ssdds))/Decimal(str(ssd))  注意decimal类型的数据不可以和普通浮点数进行运算。 TypeError: unsupported operand type(s) for +: 'float'and 'Decimal'
            res = format(ssdds / float(ssd), '.2f')
        print(res)
        # break
        # order_info = Order_info(tid=tid, delivery_province=delivery_province, delivery_city=delivery_city,
        #                         delivery_district=delivery_district, receiver_tel=receiver_tel,
        #                         delivery_address=delivery_address)
        # db.session.add(order_info)
        # db.session.commit()
        ab_jqx_dxl = Ab_jqx_dxl(sku=ll.sku, hjyear='2020', hjmn='08', ck_id='JD', qc=qc1, qm=qm1, xs_s=xs_s, weidu='3',
                                last=last, sku_id=ggd.sku_id, cbj=ggd.jg1, dxl=res)
        db.session.add(ab_jqx_dxl)
        print(i)
        print('---------------')
    db.session.commit()

    # print(ll[0])
    # owenums = Owenum.query.all()
    # print(owenums[0]['sku']) # TypeError: 'Owenum' object is not subscriptable
    # for owenum in owenums:
    #     print(owenum.sku)
    return str(i)


@main_bp.route('/calc_dxl_JD_4')
def calc_dxl_JD_4():
    # lls = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sku).distinct().limit(30)
    lls = Jxc_rj_202009.query.with_entities(Jxc_rj_202009.sku, Jxc_rj_202009.sku_id).distinct().filter_by(
        ck_id=4).filter_by(date='2020-09-30').filter(Jxc_rj_202009.sl_qm != 0).all()
    # print(lls)
    i = 0
    for ll in lls:
        print(ll.sku)
        print(ll.sku_id)
        i = i + 1
        # return str(i)
        bbs = Jxc_rj_202006.query.filter_by(ck_id=4).filter_by(date='2020-06-01').filter_by(
            sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        if bbs:
            # print('33')
            # print(bbs.sl_qc)  # 错误  print(bbs['sl_qm'])
            qc1 = bbs.sl_qc
        else:
            qc1 = 0
        bbss = Jxc_rj_202009.query.filter_by(ck_id=4).filter_by(date='2020-09-30').filter_by(sku=ll.sku).first()
        if bbss:
            # print('44')
            # print(bbss.sl_qm)  # 错误  print(bbs['sl_qm'])
            qm1 = bbss.sl_qm
        else:
            qm1 = 0
        # 求和  User.query.with_entities(func.sum(User.id)).all()
        jh1 = Jxc_rj_202006.query.filter_by(ck_id=4).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202006.sl0_pf)).all()
        jh2 = Jxc_rj_202007.query.filter_by(ck_id=4).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202007.sl0_pf)).all()
        jh3 = Jxc_rj_202008.query.filter_by(ck_id=4).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202008.sl0_pf)).all()
        jh4 = Jxc_rj_202009.query.filter_by(ck_id=4).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202009.sl0_pf)).all()
        # print(jh1[0][0])
        # print(jh2)
        # print(jh3)
        # print(jh4)
        if jh1[0][0]:
            jh1 = jh1[0][0]
        else:
            jh1 = 0
        if jh2[0][0]:
            jh2 = jh2[0][0]
        else:
            jh2 = 0
        if jh3[0][0]:
            jh3 = jh3[0][0]
        else:
            jh3 = 0
        if jh4[0][0]:
            jh4 = jh4[0][0]
        else:
            jh4 = 0
        xs_s = jh1 + jh2 + jh3 + jh4
        # print(xs_s)
        # 计算滞销量
        last = min(max(qc1 - xs_s, 0), qm1)
        # 同步最新成本价
        # jg1 = Spjgb.query.filter_by(goods_id=ll.goods_id).all()
        # ggd = Jxc_rj_202005.query.filter_by(sku=ll.sku).first()
        # print(ggd.sku_id)
        ggd = Spjgb.query.filter_by(sku_id=ll.sku_id).first()
        # print(ggd.jg1)
        # 计算动销率
        if qc1 * ggd.jg1 == 0:  # 被除数为0
            res = 0
        else:
            ssd = qc1 * ggd.jg1
            ssdds = float(xs_s) * float(ggd.jg1)
            # 迫使您将浮点数转换为小数， 更精确  float是会四舍五入
            # dxl = Decimal(str(ssdds))/Decimal(str(ssd))  注意decimal类型的数据不可以和普通浮点数进行运算。 TypeError: unsupported operand type(s) for +: 'float'and 'Decimal'
            res = format(ssdds / float(ssd), '.2f')
        print(res)
        # break
        # order_info = Order_info(tid=tid, delivery_province=delivery_province, delivery_city=delivery_city,
        #                         delivery_district=delivery_district, receiver_tel=receiver_tel,
        #                         delivery_address=delivery_address)
        # db.session.add(order_info)
        # db.session.commit()
        ab_jqx_dxl = Ab_jqx_dxl(sku=ll.sku, hjyear='2020', hjmn='09', ck_id='JD', qc=qc1, qm=qm1, xs_s=xs_s, weidu='4',
                                last=last, sku_id=ggd.sku_id, cbj=ggd.jg1, dxl=res)
        db.session.add(ab_jqx_dxl)
        print(i)
        print('---------------')
    db.session.commit()

    # print(ll[0])
    # owenums = Owenum.query.all()
    # print(owenums[0]['sku']) # TypeError: 'Owenum' object is not subscriptable
    # for owenum in owenums:
    #     print(owenum.sku)
    return str(i)


@main_bp.route('/calc_dxl_JD_6')
def calc_dxl_JD_6():
    # lls = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sku).distinct().limit(30)
    lls = Jxc_rj_202009.query.with_entities(Jxc_rj_202009.sku, Jxc_rj_202009.sku_id).distinct().filter_by(
        ck_id=4).filter_by(date='2020-09-30').filter(Jxc_rj_202009.sl_qm != 0).all()
    # print(lls)
    i = 0
    for ll in lls:
        print(ll.sku)
        print(ll.sku_id)
        i = i + 1
        # return str(i)
        bbs = Jxc_rj_202004.query.filter_by(ck_id=4).filter_by(date='2020-04-01').filter_by(
            sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        if bbs:
            # print('33')
            # print(bbs.sl_qc)  # 错误  print(bbs['sl_qm'])
            qc1 = bbs.sl_qc
        else:
            qc1 = 0
        bbss = Jxc_rj_202009.query.filter_by(ck_id=4).filter_by(date='2020-09-30').filter_by(sku=ll.sku).first()
        if bbss:
            # print('44')
            # print(bbss.sl_qm)  # 错误  print(bbs['sl_qm'])
            qm1 = bbss.sl_qm
        else:
            qm1 = 0
        # 求和  User.query.with_entities(func.sum(User.id)).all()
        jh1 = Jxc_rj_202004.query.filter_by(ck_id=4).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202004.sl0_pf)).all()
        jh2 = Jxc_rj_202005.query.filter_by(ck_id=4).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202005.sl0_pf)).all()
        jh3 = Jxc_rj_202006.query.filter_by(ck_id=4).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202006.sl0_pf)).all()
        jh4 = Jxc_rj_202007.query.filter_by(ck_id=4).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202007.sl0_pf)).all()
        jh5 = Jxc_rj_202008.query.filter_by(ck_id=4).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202008.sl0_pf)).all()
        jh6 = Jxc_rj_202009.query.filter_by(ck_id=4).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202009.sl0_pf)).all()
        # print(jh1[0][0])
        # print(jh2)
        # print(jh3)
        # print(jh4)
        if jh1[0][0]:
            jh1 = jh1[0][0]
        else:
            jh1 = 0
        if jh2[0][0]:
            jh2 = jh2[0][0]
        else:
            jh2 = 0
        if jh3[0][0]:
            jh3 = jh3[0][0]
        else:
            jh3 = 0
        if jh4[0][0]:
            jh4 = jh4[0][0]
        else:
            jh4 = 0
        if jh5[0][0]:
            jh5 = jh5[0][0]
        else:
            jh5 = 0
        if jh6[0][0]:
            jh6 = jh6[0][0]
        else:
            jh6 = 0
        xs_s = jh1 + jh2 + jh3 + jh4 + jh5 + jh6
        # print(xs_s)
        # 计算滞销量
        last = min(max(qc1 - xs_s, 0), qm1)
        # 同步最新成本价
        # jg1 = Spjgb.query.filter_by(goods_id=ll.goods_id).all()
        # ggd = Jxc_rj_202005.query.filter_by(sku=ll.sku).first()
        # print(ggd.sku_id)
        ggd = Spjgb.query.filter_by(sku_id=ll.sku_id).first()
        # print(ggd.jg1)
        # 计算动销率
        if qc1 * ggd.jg1 == 0:  # 被除数为0
            res = 0
        else:
            ssd = qc1 * ggd.jg1
            ssdds = float(xs_s) * float(ggd.jg1)
            # 迫使您将浮点数转换为小数， 更精确  float是会四舍五入
            # dxl = Decimal(str(ssdds))/Decimal(str(ssd))  注意decimal类型的数据不可以和普通浮点数进行运算。 TypeError: unsupported operand type(s) for +: 'float'and 'Decimal'
            res = format(ssdds / float(ssd), '.2f')
        print(res)
        # break
        # order_info = Order_info(tid=tid, delivery_province=delivery_province, delivery_city=delivery_city,
        #                         delivery_district=delivery_district, receiver_tel=receiver_tel,
        #                         delivery_address=delivery_address)
        # db.session.add(order_info)
        # db.session.commit()
        ab_jqx_dxl = Ab_jqx_dxl(sku=ll.sku, hjyear='2020', hjmn='09', ck_id='JD', qc=qc1, qm=qm1, xs_s=xs_s, weidu='6',
                                last=last, sku_id=ggd.sku_id, cbj=ggd.jg1, dxl=res)
        db.session.add(ab_jqx_dxl)
        print(i)
        print('---------------')
    db.session.commit()

    # print(ll[0])
    # owenums = Owenum.query.all()
    # print(owenums[0]['sku']) # TypeError: 'Owenum' object is not subscriptable
    # for owenum in owenums:
    #     print(owenum.sku)
    return str(i)


@main_bp.route('/calc_dxl_TM_3')
def calc_dxl_TM_3():
    # lls = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sku).distinct().limit(30)
    lls = Jxc_rj_202008.query.with_entities(Jxc_rj_202008.sku, Jxc_rj_202008.sku_id).distinct().filter(
        Jxc_rj_202008.ck_id.in_(['2', '3'])).filter_by(date='2020-08-31').filter(Jxc_rj_202008.sl_qm != 0).all()
    # print(lls)
    i = 0
    for ll in lls:
        print(ll.sku)
        print(ll.sku_id)
        i = i + 1
        # return str(i)

        """
        bbs = Jxc_rj_202002.query.filter(Jxc_rj_202002.ck_id.in_(['2', '3'])).filter_by(date='2020-02-01').filter_by(
            sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        if bbs:
            # print('33')
            # print(bbs.sl_qc)  # 错误  print(bbs['sl_qm'])
            qc1 = bbs.sl_qc
        else:
            qc1 = 0
        bbss = Jxc_rj_202005.query.filter(Jxc_rj_202005.ck_id.in_(['2', '3'])).filter_by(date='2020-05-31').filter_by(
            sku=ll.sku).first()
        if bbss:
            # print('44')
            # print(bbss.sl_qm)  # 错误  print(bbs['sl_qm'])
            qm1 = bbss.sl_qm
        else:
            qm1 = 0
        """

        bbs = Jxc_rj_202006.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-06-01'). \
            filter(Jxc_rj_202006.ck_id.in_(['2', '3'])). \
            with_entities(func.sum(Jxc_rj_202006.sl_qc)).all()
        # print(bbs)
        # print(bbs[0])
        # print(bbs[0][0])
        if bbs[0][0]:
            qc1 = bbs[0][0]
        else:
            qc1 = 0
        print(qc1)

        bbss = Jxc_rj_202008.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-08-31'). \
            filter(Jxc_rj_202008.ck_id.in_(['2', '3'])). \
            with_entities(func.sum(Jxc_rj_202008.sl_qm)).all()
        print(bbss)
        if bbss[0][0]:
            qm1 = bbss[0][0]
        else:
            qm1 = 0
        print(qm1)

        # 求和  User.query.with_entities(func.sum(User.id)).all()
        jh1 = Jxc_rj_202006.query.filter(Jxc_rj_202006.ck_id.in_(['2', '3'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202006.sl0_ls)).all()
        # jh2 = Jxc_rj_202003.query.filter(Jxc_rj_202003.ck_id.in_(['2', '3'])).filter_by(sku=ll.sku).with_entities(
        #     func.sum(Jxc_rj_202003.sl0_ls)).all()
        jh3 = Jxc_rj_202007.query.filter(Jxc_rj_202007.ck_id.in_(['2', '3'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202007.sl0_ls)).all()
        jh4 = Jxc_rj_202008.query.filter(Jxc_rj_202008.ck_id.in_(['2', '3'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202008.sl0_ls)).all()
        # print(jh1[0][0])  #None   3
        # print(jh1[0])     #(None,) (Decimal('3'),)
        # print(jh2)
        # print(jh3)
        # print(jh4)
        if jh1[0][0]:
            jh1 = jh1[0][0]
        else:
            jh1 = 0
        # if jh2[0][0]:
        #     jh2 = jh2[0][0]
        # else:
        jh2 = 0
        if jh3[0][0]:
            jh3 = jh3[0][0]
        else:
            jh3 = 0
        if jh4[0][0]:
            jh4 = jh4[0][0]
        else:
            jh4 = 0
        xs_s = jh1 + jh2 + jh3 + jh4
        # print(xs_s)
        # 计算滞销量
        last = min(max(qc1 - xs_s, 0), qm1)
        # 同步最新成本价
        # jg1 = Spjgb.query.filter_by(goods_id=ll.goods_id).all()
        # ggd = Jxc_rj_202005.query.filter_by(sku=ll.sku).first()
        # print(ggd.sku_id)
        ggd = Spjgb.query.filter_by(sku_id=ll.sku_id).first()
        # print(ggd.jg1)
        # 计算动销率
        qc1 = float(qc1)
        if qc1 * ggd.jg1 == 0:  # 被除数为0
            res = 0
        else:
            ssd = qc1 * ggd.jg1
            ssdds = float(xs_s) * float(ggd.jg1)
            # 迫使您将浮点数转换为小数， 更精确  float是会四舍五入
            # dxl = Decimal(str(ssdds))/Decimal(str(ssd))  注意decimal类型的数据不可以和普通浮点数进行运算。 TypeError: unsupported operand type(s) for +: 'float'and 'Decimal'
            res = format(ssdds / float(ssd), '.2f')
        print(res)
        # break
        # order_info = Order_info(tid=tid, delivery_province=delivery_province, delivery_city=delivery_city,
        #                         delivery_district=delivery_district, receiver_tel=receiver_tel,
        #                         delivery_address=delivery_address)
        # db.session.add(order_info)
        # db.session.commit()
        ab_jqx_dxl = Ab_jqx_dxl(sku=ll.sku, hjyear='2020', hjmn='08', ck_id='TM', qc=qc1, qm=qm1, xs_s=xs_s, weidu='3',
                                last=last, sku_id=ggd.sku_id, cbj=ggd.jg1, dxl=res)
        db.session.add(ab_jqx_dxl)
        print(i)
        print('---------------')
    db.session.commit()

    # print(ll[0])
    # owenums = Owenum.query.all()
    # print(owenums[0]['sku']) # TypeError: 'Owenum' object is not subscriptable
    # for owenum in owenums:
    #     print(owenum.sku)
    return str(i)


@main_bp.route('/calc_dxl_TM_4')
def calc_dxl_TM_4():
    # lls = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sku).distinct().limit(30)
    lls = Jxc_rj_202009.query.with_entities(Jxc_rj_202009.sku, Jxc_rj_202009.sku_id).distinct().filter(
        Jxc_rj_202009.ck_id.in_(['2', '3'])).filter_by(date='2020-09-30').filter(Jxc_rj_202009.sl_qm != 0).all()
    # print(lls)
    i = 0
    for ll in lls:
        print(ll.sku)
        print(ll.sku_id)
        i = i + 1
        # return str(i)

        """
        bbs = Jxc_rj_202002.query.filter(Jxc_rj_202002.ck_id.in_(['2', '3'])).filter_by(date='2020-02-01').filter_by(
            sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        if bbs:
            # print('33')
            # print(bbs.sl_qc)  # 错误  print(bbs['sl_qm'])
            qc1 = bbs.sl_qc
        else:
            qc1 = 0
        bbss = Jxc_rj_202005.query.filter(Jxc_rj_202005.ck_id.in_(['2', '3'])).filter_by(date='2020-05-31').filter_by(
            sku=ll.sku).first()
        if bbss:
            # print('44')
            # print(bbss.sl_qm)  # 错误  print(bbs['sl_qm'])
            qm1 = bbss.sl_qm
        else:
            qm1 = 0
        """

        bbs = Jxc_rj_202006.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-06-01'). \
            filter(Jxc_rj_202006.ck_id.in_(['2', '3'])). \
            with_entities(func.sum(Jxc_rj_202006.sl_qc)).all()
        # print(bbs)
        # print(bbs[0])
        # print(bbs[0][0])
        if bbs[0][0]:
            qc1 = bbs[0][0]
        else:
            qc1 = 0
        print(qc1)

        bbss = Jxc_rj_202009.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-09-30'). \
            filter(Jxc_rj_202009.ck_id.in_(['2', '3'])). \
            with_entities(func.sum(Jxc_rj_202009.sl_qm)).all()
        print(bbss)
        if bbss[0][0]:
            qm1 = bbss[0][0]
        else:
            qm1 = 0
        print(qm1)

        # 求和  User.query.with_entities(func.sum(User.id)).all()
        jh1 = Jxc_rj_202006.query.filter(Jxc_rj_202006.ck_id.in_(['2', '3'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202006.sl0_ls)).all()
        jh2 = Jxc_rj_202007.query.filter(Jxc_rj_202007.ck_id.in_(['2', '3'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202007.sl0_ls)).all()
        jh3 = Jxc_rj_202008.query.filter(Jxc_rj_202008.ck_id.in_(['2', '3'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202008.sl0_ls)).all()
        jh4 = Jxc_rj_202009.query.filter(Jxc_rj_202009.ck_id.in_(['2', '3'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202009.sl0_ls)).all()
        # print(jh1[0][0])  #None   3
        # print(jh1[0])     #(None,) (Decimal('3'),)
        # print(jh2)
        # print(jh3)
        # print(jh4)
        if jh1[0][0]:
            jh1 = jh1[0][0]
        else:
            jh1 = 0
        if jh2[0][0]:
            jh2 = jh2[0][0]
        else:
            jh2 = 0
        if jh3[0][0]:
            jh3 = jh3[0][0]
        else:
            jh3 = 0
        if jh4[0][0]:
            jh4 = jh4[0][0]
        else:
            jh4 = 0
        xs_s = jh1 + jh2 + jh3 + jh4
        # print(xs_s)
        # 计算滞销量
        last = min(max(qc1 - xs_s, 0), qm1)
        # 同步最新成本价
        # jg1 = Spjgb.query.filter_by(goods_id=ll.goods_id).all()
        # ggd = Jxc_rj_202005.query.filter_by(sku=ll.sku).first()
        # print(ggd.sku_id)
        ggd = Spjgb.query.filter_by(sku_id=ll.sku_id).first()
        # print(ggd.jg1)
        # 计算动销率
        qc1 = float(qc1)
        if qc1 * ggd.jg1 == 0:  # 被除数为0
            res = 0
        else:
            ssd = qc1 * ggd.jg1
            ssdds = float(xs_s) * float(ggd.jg1)
            # 迫使您将浮点数转换为小数， 更精确  float是会四舍五入
            # dxl = Decimal(str(ssdds))/Decimal(str(ssd))  注意decimal类型的数据不可以和普通浮点数进行运算。 TypeError: unsupported operand type(s) for +: 'float'and 'Decimal'
            res = format(ssdds / float(ssd), '.2f')
        print(res)
        # break
        # order_info = Order_info(tid=tid, delivery_province=delivery_province, delivery_city=delivery_city,
        #                         delivery_district=delivery_district, receiver_tel=receiver_tel,
        #                         delivery_address=delivery_address)
        # db.session.add(order_info)
        # db.session.commit()
        ab_jqx_dxl = Ab_jqx_dxl(sku=ll.sku, hjyear='2020', hjmn='09', ck_id='TM', qc=qc1, qm=qm1, xs_s=xs_s, weidu='4',
                                last=last, sku_id=ggd.sku_id, cbj=ggd.jg1, dxl=res)
        db.session.add(ab_jqx_dxl)
        print(i)
        print('---------------')
    db.session.commit()

    # print(ll[0])
    # owenums = Owenum.query.all()
    # print(owenums[0]['sku']) # TypeError: 'Owenum' object is not subscriptable
    # for owenum in owenums:
    #     print(owenum.sku)
    return str(i)


@main_bp.route('/calc_dxl_TM_6')
def calc_dxl_TM_6():
    # lls = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sku).distinct().limit(30)
    lls = Jxc_rj_202009.query.with_entities(Jxc_rj_202009.sku, Jxc_rj_202009.sku_id).distinct().filter(
        Jxc_rj_202009.ck_id.in_(['2', '3'])).filter_by(date='2020-09-30').filter(Jxc_rj_202009.sl_qm != 0).all()
    # print(lls)
    i = 0
    for ll in lls:
        print(ll.sku)
        print(ll.sku_id)
        i = i + 1
        # return str(i)

        """
        bbs = Jxc_rj_202002.query.filter(Jxc_rj_202002.ck_id.in_(['2', '3'])).filter_by(date='2020-02-01').filter_by(
            sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        if bbs:
            # print('33')
            # print(bbs.sl_qc)  # 错误  print(bbs['sl_qm'])
            qc1 = bbs.sl_qc
        else:
            qc1 = 0
        bbss = Jxc_rj_202005.query.filter(Jxc_rj_202005.ck_id.in_(['2', '3'])).filter_by(date='2020-05-31').filter_by(
            sku=ll.sku).first()
        if bbss:
            # print('44')
            # print(bbss.sl_qm)  # 错误  print(bbs['sl_qm'])
            qm1 = bbss.sl_qm
        else:
            qm1 = 0
        """

        bbs = Jxc_rj_202004.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-04-01'). \
            filter(Jxc_rj_202004.ck_id.in_(['2', '3'])). \
            with_entities(func.sum(Jxc_rj_202004.sl_qc)).all()
        # print(bbs)
        # print(bbs[0])
        # print(bbs[0][0])
        if bbs[0][0]:
            qc1 = bbs[0][0]
        else:
            qc1 = 0
        print(qc1)

        bbss = Jxc_rj_202009.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-09-30'). \
            filter(Jxc_rj_202009.ck_id.in_(['2', '3'])). \
            with_entities(func.sum(Jxc_rj_202009.sl_qm)).all()
        print(bbss)
        if bbss[0][0]:
            qm1 = bbss[0][0]
        else:
            qm1 = 0
        print(qm1)

        # 求和  User.query.with_entities(func.sum(User.id)).all()
        jh1 = Jxc_rj_202004.query.filter(Jxc_rj_202004.ck_id.in_(['2', '3'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202004.sl0_ls)).all()
        jh2 = Jxc_rj_202005.query.filter(Jxc_rj_202005.ck_id.in_(['2', '3'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202005.sl0_ls)).all()
        jh3 = Jxc_rj_202006.query.filter(Jxc_rj_202006.ck_id.in_(['2', '3'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202006.sl0_ls)).all()
        jh4 = Jxc_rj_202007.query.filter(Jxc_rj_202007.ck_id.in_(['2', '3'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202007.sl0_ls)).all()
        jh5 = Jxc_rj_202008.query.filter(Jxc_rj_202008.ck_id.in_(['2', '3'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202008.sl0_ls)).all()
        jh6 = Jxc_rj_202009.query.filter(Jxc_rj_202009.ck_id.in_(['2', '3'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202009.sl0_ls)).all()
        # print(jh1[0][0])  #None   3
        # print(jh1[0])     #(None,) (Decimal('3'),)
        # print(jh2)
        # print(jh3)
        # print(jh4)
        if jh1[0][0]:
            jh1 = jh1[0][0]
        else:
            jh1 = 0
        if jh2[0][0]:
            jh2 = jh2[0][0]
        else:
            jh2 = 0
        if jh3[0][0]:
            jh3 = jh3[0][0]
        else:
            jh3 = 0
        if jh4[0][0]:
            jh4 = jh4[0][0]
        else:
            jh4 = 0
        if jh5[0][0]:
            jh5 = jh5[0][0]
        else:
            jh5 = 0
        if jh6[0][0]:
            jh6 = jh6[0][0]
        else:
            jh6 = 0
        xs_s = jh1 + jh2 + jh3 + jh4 + jh5 + jh6
        # print(xs_s)
        # 计算滞销量
        last = min(max(qc1 - xs_s, 0), qm1)
        # 同步最新成本价
        # jg1 = Spjgb.query.filter_by(goods_id=ll.goods_id).all()
        # ggd = Jxc_rj_202005.query.filter_by(sku=ll.sku).first()
        # print(ggd.sku_id)
        ggd = Spjgb.query.filter_by(sku_id=ll.sku_id).first()
        # print(ggd.jg1)
        # 计算动销率
        qc1 = float(qc1)
        if qc1 * ggd.jg1 == 0:  # 被除数为0
            res = 0
        else:
            ssd = qc1 * ggd.jg1
            ssdds = float(xs_s) * float(ggd.jg1)
            # 迫使您将浮点数转换为小数， 更精确  float是会四舍五入
            # dxl = Decimal(str(ssdds))/Decimal(str(ssd))  注意decimal类型的数据不可以和普通浮点数进行运算。 TypeError: unsupported operand type(s) for +: 'float'and 'Decimal'
            res = format(ssdds / float(ssd), '.2f')
        print(res)
        # break
        # order_info = Order_info(tid=tid, delivery_province=delivery_province, delivery_city=delivery_city,
        #                         delivery_district=delivery_district, receiver_tel=receiver_tel,
        #                         delivery_address=delivery_address)
        # db.session.add(order_info)
        # db.session.commit()
        ab_jqx_dxl = Ab_jqx_dxl(sku=ll.sku, hjyear='2020', hjmn='09', ck_id='TM', qc=qc1, qm=qm1, xs_s=xs_s, weidu='6',
                                last=last, sku_id=ggd.sku_id, cbj=ggd.jg1, dxl=res)
        db.session.add(ab_jqx_dxl)
        print(i)
        print('---------------')
    db.session.commit()

    # print(ll[0])
    # owenums = Owenum.query.all()
    # print(owenums[0]['sku']) # TypeError: 'Owenum' object is not subscriptable
    # for owenum in owenums:
    #     print(owenum.sku)
    return str(i)


@main_bp.route('/calc_dxl_XQD_3')
def calc_dxl_XQD_3():
    # lls = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sku).distinct().limit(30)
    lls = Jxc_rj_202008.query.with_entities(Jxc_rj_202008.sku, Jxc_rj_202008.sku_id).distinct().filter(
        Jxc_rj_202008.ck_id.in_(['11', '15'])).filter_by(date='2020-08-31').filter(Jxc_rj_202008.sl_qm != 0).all()
    # print(lls)
    i = 0
    for ll in lls:
        print(ll.sku)
        print(ll.sku_id)
        i = i + 1
        # return str(i)
        # bbs = Jxc_rj_202002.query.with_entities(Jxc_rj_202002.sl_qc).filter(
        #     Jxc_rj_202002.ck_id.in_(['11', '15'])).filter_by(date='2020-02-01').filter_by(
        #     sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        # exit()

        """   多行注释
        有点特殊哦 有两个仓库 所以下面的first就不能用了
        bbs = Jxc_rj_202002.query.with_entities(Jxc_rj_202002.sl_qc).filter(Jxc_rj_202002.ck_id.in_(['11', '15'])).filter_by(date='2020-02-01').filter_by(
            sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        if bbs:
            # print('33')
            # print(bbs.sl_qc)  # 错误  print(bbs['sl_qm'])
            qc1 = bbs.sl_qc
        else:
            qc1 = 0
        bbss = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sl_qm).filter(Jxc_rj_202005.ck_id.in_(['11', '15'])).filter_by(date='2020-05-31').filter_by(
            sku=ll.sku).first()
        if bbss:
            # print('44')
            # print(bbss.sl_qm)  # 错误  print(bbs['sl_qm'])
            qm1 = bbss.sl_qm
        else:
            qm1 = 0
        """

        bbs = Jxc_rj_202006.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-06-01'). \
            filter(Jxc_rj_202006.ck_id.in_(['11', '15'])). \
            with_entities(func.sum(Jxc_rj_202006.sl_qc)).all()
        # print(bbs)
        # print(bbs[0])
        # print(bbs[0][0])
        if bbs[0][0]:
            qc1 = bbs[0][0]
        else:
            qc1 = 0
        print(qc1)

        bbss = Jxc_rj_202008.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-08-31'). \
            filter(Jxc_rj_202008.ck_id.in_(['11', '15'])). \
            with_entities(func.sum(Jxc_rj_202008.sl_qm)).all()
        print(bbss)
        if bbss[0][0]:
            qm1 = bbss[0][0]
        else:
            qm1 = 0
        print(qm1)

        # exit()

        # 求和  User.query.with_entities(func.sum(User.id)).all()
        jh1 = Jxc_rj_202006.query.filter(Jxc_rj_202006.ck_id.in_(['11', '15'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202006.sl0_ls)).all()
        # jh2 = Jxc_rj_202003.query.filter(Jxc_rj_202003.ck_id.in_(['11', '15'])).filter_by(sku=ll.sku).with_entities(
        #     func.sum(Jxc_rj_202003.sl0_ls)).all()
        jh3 = Jxc_rj_202007.query.filter(Jxc_rj_202007.ck_id.in_(['11', '15'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202007.sl0_ls)).all()
        jh4 = Jxc_rj_202008.query.filter(Jxc_rj_202008.ck_id.in_(['11', '15'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202008.sl0_ls)).all()
        # print(jh1[0][0])  #None   3
        # print(jh1[0])     #(None,) (Decimal('3'),)
        # print(jh2)
        # print(jh3)
        # print(jh4)
        if jh1[0][0]:
            jh1 = jh1[0][0]
        else:
            jh1 = 0
        # if jh2[0][0]:
        #     jh2 = jh2[0][0]
        # else:
        jh2 = 0
        if jh3[0][0]:
            jh3 = jh3[0][0]
        else:
            jh3 = 0
        if jh4[0][0]:
            jh4 = jh4[0][0]
        else:
            jh4 = 0
        xs_s = jh1 + jh2 + jh3 + jh4
        # print(xs_s)
        # 计算滞销量
        last = min(max(qc1 - xs_s, 0), qm1)
        # 同步最新成本价
        # jg1 = Spjgb.query.filter_by(goods_id=ll.goods_id).all()
        # ggd = Jxc_rj_202005.query.filter_by(sku=ll.sku).first()
        # print(ggd.sku_id)
        ggd = Spjgb.query.filter_by(sku_id=ll.sku_id).first()
        # print(ggd.jg1)
        # 计算动销率
        qc1 = float(qc1)
        if qc1 * ggd.jg1 == 0:  # 被除数为0
            res = 0
        else:
            ssd = qc1 * ggd.jg1
            ssdds = float(xs_s) * float(ggd.jg1)
            # 迫使您将浮点数转换为小数， 更精确  float是会四舍五入
            # dxl = Decimal(str(ssdds))/Decimal(str(ssd))  注意decimal类型的数据不可以和普通浮点数进行运算。 TypeError: unsupported operand type(s) for +: 'float'and 'Decimal'
            res = format(ssdds / float(ssd), '.2f')
        print(res)
        # break
        # order_info = Order_info(tid=tid, delivery_province=delivery_province, delivery_city=delivery_city,
        #                         delivery_district=delivery_district, receiver_tel=receiver_tel,
        #                         delivery_address=delivery_address)
        # db.session.add(order_info)
        # db.session.commit()
        ab_jqx_dxl = Ab_jqx_dxl(sku=ll.sku, hjyear='2020', hjmn='08', ck_id='XQD', qc=qc1, qm=qm1, xs_s=xs_s,
                                weidu='3',
                                last=last, sku_id=ggd.sku_id, cbj=ggd.jg1, dxl=res)
        db.session.add(ab_jqx_dxl)
        print(i)
        print('---------------')
    db.session.commit()

    # print(ll[0])
    # owenums = Owenum.query.all()
    # print(owenums[0]['sku']) # TypeError: 'Owenum' object is not subscriptable
    # for owenum in owenums:
    #     print(owenum.sku)
    return str(i)


@main_bp.route('/calc_dxl_XQD_4')
def calc_dxl_XQD_4():
    # lls = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sku).distinct().limit(30)
    lls = Jxc_rj_202009.query.with_entities(Jxc_rj_202009.sku, Jxc_rj_202009.sku_id).distinct().filter(
        Jxc_rj_202009.ck_id.in_(['11', '15'])).filter_by(date='2020-09-30').filter(Jxc_rj_202009.sl_qm != 0).all()
    # print(lls)
    i = 0
    for ll in lls:
        print(ll.sku)
        print(ll.sku_id)
        i = i + 1
        # return str(i)
        # bbs = Jxc_rj_202002.query.with_entities(Jxc_rj_202002.sl_qc).filter(
        #     Jxc_rj_202002.ck_id.in_(['11', '15'])).filter_by(date='2020-02-01').filter_by(
        #     sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        # exit()

        """   多行注释
        有点特殊哦 有两个仓库 所以下面的first就不能用了
        bbs = Jxc_rj_202002.query.with_entities(Jxc_rj_202002.sl_qc).filter(Jxc_rj_202002.ck_id.in_(['11', '15'])).filter_by(date='2020-02-01').filter_by(
            sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        if bbs:
            # print('33')
            # print(bbs.sl_qc)  # 错误  print(bbs['sl_qm'])
            qc1 = bbs.sl_qc
        else:
            qc1 = 0
        bbss = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sl_qm).filter(Jxc_rj_202005.ck_id.in_(['11', '15'])).filter_by(date='2020-05-31').filter_by(
            sku=ll.sku).first()
        if bbss:
            # print('44')
            # print(bbss.sl_qm)  # 错误  print(bbs['sl_qm'])
            qm1 = bbss.sl_qm
        else:
            qm1 = 0
        """

        bbs = Jxc_rj_202006.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-06-01'). \
            filter(Jxc_rj_202006.ck_id.in_(['11', '15'])). \
            with_entities(func.sum(Jxc_rj_202006.sl_qc)).all()
        # print(bbs)
        # print(bbs[0])
        # print(bbs[0][0])
        if bbs[0][0]:
            qc1 = bbs[0][0]
        else:
            qc1 = 0
        print(qc1)

        bbss = Jxc_rj_202009.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-09-30'). \
            filter(Jxc_rj_202009.ck_id.in_(['11', '15'])). \
            with_entities(func.sum(Jxc_rj_202009.sl_qm)).all()
        print(bbss)
        if bbss[0][0]:
            qm1 = bbss[0][0]
        else:
            qm1 = 0
        print(qm1)

        # exit()

        # 求和  User.query.with_entities(func.sum(User.id)).all()
        jh1 = Jxc_rj_202006.query.filter(Jxc_rj_202006.ck_id.in_(['11', '15'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202006.sl0_ls)).all()
        jh2 = Jxc_rj_202007.query.filter(Jxc_rj_202007.ck_id.in_(['11', '15'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202007.sl0_ls)).all()
        jh3 = Jxc_rj_202008.query.filter(Jxc_rj_202008.ck_id.in_(['11', '15'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202008.sl0_ls)).all()
        jh4 = Jxc_rj_202009.query.filter(Jxc_rj_202009.ck_id.in_(['11', '15'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202009.sl0_ls)).all()
        # print(jh1[0][0])  #None   3
        # print(jh1[0])     #(None,) (Decimal('3'),)
        # print(jh2)
        # print(jh3)
        # print(jh4)
        if jh1[0][0]:
            jh1 = jh1[0][0]
        else:
            jh1 = 0
        if jh2[0][0]:
            jh2 = jh2[0][0]
        else:
            jh2 = 0
        if jh3[0][0]:
            jh3 = jh3[0][0]
        else:
            jh3 = 0
        if jh4[0][0]:
            jh4 = jh4[0][0]
        else:
            jh4 = 0
        xs_s = jh1 + jh2 + jh3 + jh4
        # print(xs_s)
        # 计算滞销量
        last = min(max(qc1 - xs_s, 0), qm1)
        # 同步最新成本价
        # jg1 = Spjgb.query.filter_by(goods_id=ll.goods_id).all()
        # ggd = Jxc_rj_202005.query.filter_by(sku=ll.sku).first()
        # print(ggd.sku_id)
        ggd = Spjgb.query.filter_by(sku_id=ll.sku_id).first()
        # print(ggd.jg1)
        # 计算动销率
        qc1 = float(qc1)
        if qc1 * ggd.jg1 == 0:  # 被除数为0
            res = 0
        else:
            ssd = qc1 * ggd.jg1
            ssdds = float(xs_s) * float(ggd.jg1)
            # 迫使您将浮点数转换为小数， 更精确  float是会四舍五入
            # dxl = Decimal(str(ssdds))/Decimal(str(ssd))  注意decimal类型的数据不可以和普通浮点数进行运算。 TypeError: unsupported operand type(s) for +: 'float'and 'Decimal'
            res = format(ssdds / float(ssd), '.2f')
        print(res)
        # break
        # order_info = Order_info(tid=tid, delivery_province=delivery_province, delivery_city=delivery_city,
        #                         delivery_district=delivery_district, receiver_tel=receiver_tel,
        #                         delivery_address=delivery_address)
        # db.session.add(order_info)
        # db.session.commit()
        ab_jqx_dxl = Ab_jqx_dxl(sku=ll.sku, hjyear='2020', hjmn='09', ck_id='XQD', qc=qc1, qm=qm1, xs_s=xs_s,
                                weidu='4',
                                last=last, sku_id=ggd.sku_id, cbj=ggd.jg1, dxl=res)
        db.session.add(ab_jqx_dxl)
        print(i)
        print('---------------')
    db.session.commit()

    # print(ll[0])
    # owenums = Owenum.query.all()
    # print(owenums[0]['sku']) # TypeError: 'Owenum' object is not subscriptable
    # for owenum in owenums:
    #     print(owenum.sku)
    return str(i)


@main_bp.route('/calc_dxl_XQD_6')
def calc_dxl_XQD_6():
    # lls = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sku).distinct().limit(30)
    lls = Jxc_rj_202009.query.with_entities(Jxc_rj_202009.sku, Jxc_rj_202009.sku_id).distinct().filter(
        Jxc_rj_202009.ck_id.in_(['11', '15'])).filter_by(date='2020-09-30').filter(Jxc_rj_202009.sl_qm != 0).all()
    # print(lls)
    i = 0
    for ll in lls:
        print(ll.sku)
        print(ll.sku_id)
        i = i + 1
        # return str(i)
        # bbs = Jxc_rj_202002.query.with_entities(Jxc_rj_202002.sl_qc).filter(
        #     Jxc_rj_202002.ck_id.in_(['11', '15'])).filter_by(date='2020-02-01').filter_by(
        #     sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        # exit()

        """   多行注释
        有点特殊哦 有两个仓库 所以下面的first就不能用了
        bbs = Jxc_rj_202002.query.with_entities(Jxc_rj_202002.sl_qc).filter(Jxc_rj_202002.ck_id.in_(['11', '15'])).filter_by(date='2020-02-01').filter_by(
            sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        if bbs:
            # print('33')
            # print(bbs.sl_qc)  # 错误  print(bbs['sl_qm'])
            qc1 = bbs.sl_qc
        else:
            qc1 = 0
        bbss = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sl_qm).filter(Jxc_rj_202005.ck_id.in_(['11', '15'])).filter_by(date='2020-05-31').filter_by(
            sku=ll.sku).first()
        if bbss:
            # print('44')
            # print(bbss.sl_qm)  # 错误  print(bbs['sl_qm'])
            qm1 = bbss.sl_qm
        else:
            qm1 = 0
        """

        bbs = Jxc_rj_202004.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-04-01'). \
            filter(Jxc_rj_202004.ck_id.in_(['11', '15'])). \
            with_entities(func.sum(Jxc_rj_202004.sl_qc)).all()
        # print(bbs)
        # print(bbs[0])
        # print(bbs[0][0])
        if bbs[0][0]:
            qc1 = bbs[0][0]
        else:
            qc1 = 0
        print(qc1)

        bbss = Jxc_rj_202009.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-09-30'). \
            filter(Jxc_rj_202009.ck_id.in_(['11', '15'])). \
            with_entities(func.sum(Jxc_rj_202009.sl_qm)).all()
        print(bbss)
        if bbss[0][0]:
            qm1 = bbss[0][0]
        else:
            qm1 = 0
        print(qm1)

        # exit()

        # 求和  User.query.with_entities(func.sum(User.id)).all()
        jh1 = Jxc_rj_202004.query.filter(Jxc_rj_202004.ck_id.in_(['11', '15'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202004.sl0_ls)).all()
        jh2 = Jxc_rj_202005.query.filter(Jxc_rj_202005.ck_id.in_(['11', '15'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202005.sl0_ls)).all()
        jh3 = Jxc_rj_202006.query.filter(Jxc_rj_202006.ck_id.in_(['11', '15'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202006.sl0_ls)).all()
        jh4 = Jxc_rj_202007.query.filter(Jxc_rj_202007.ck_id.in_(['11', '15'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202007.sl0_ls)).all()
        jh5 = Jxc_rj_202008.query.filter(Jxc_rj_202008.ck_id.in_(['11', '15'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202008.sl0_ls)).all()
        jh6 = Jxc_rj_202009.query.filter(Jxc_rj_202009.ck_id.in_(['11', '15'])).filter_by(sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202009.sl0_ls)).all()
        # print(jh1[0][0])  #None   3
        # print(jh1[0])     #(None,) (Decimal('3'),)
        # print(jh2)
        # print(jh3)
        # print(jh4)
        if jh1[0][0]:
            jh1 = jh1[0][0]
        else:
            jh1 = 0
        if jh2[0][0]:
            jh2 = jh2[0][0]
        else:
            jh2 = 0
        if jh3[0][0]:
            jh3 = jh3[0][0]
        else:
            jh3 = 0
        if jh4[0][0]:
            jh4 = jh4[0][0]
        else:
            jh4 = 0
        if jh5[0][0]:
            jh5 = jh5[0][0]
        else:
            jh5 = 0
        if jh6[0][0]:
            jh6 = jh6[0][0]
        else:
            jh6 = 0
        xs_s = jh1 + jh2 + jh3 + jh4 + jh5 + jh6
        # print(xs_s)
        # 计算滞销量
        last = min(max(qc1 - xs_s, 0), qm1)
        # 同步最新成本价
        # jg1 = Spjgb.query.filter_by(goods_id=ll.goods_id).all()
        # ggd = Jxc_rj_202005.query.filter_by(sku=ll.sku).first()
        # print(ggd.sku_id)
        ggd = Spjgb.query.filter_by(sku_id=ll.sku_id).first()
        # print(ggd.jg1)
        # 计算动销率
        qc1 = float(qc1)
        if qc1 * ggd.jg1 == 0:  # 被除数为0
            res = 0
        else:
            ssd = qc1 * ggd.jg1
            ssdds = float(xs_s) * float(ggd.jg1)
            # 迫使您将浮点数转换为小数， 更精确  float是会四舍五入
            # dxl = Decimal(str(ssdds))/Decimal(str(ssd))  注意decimal类型的数据不可以和普通浮点数进行运算。 TypeError: unsupported operand type(s) for +: 'float'and 'Decimal'
            res = format(ssdds / float(ssd), '.2f')
        print(res)
        # break
        # order_info = Order_info(tid=tid, delivery_province=delivery_province, delivery_city=delivery_city,
        #                         delivery_district=delivery_district, receiver_tel=receiver_tel,
        #                         delivery_address=delivery_address)
        # db.session.add(order_info)
        # db.session.commit()
        ab_jqx_dxl = Ab_jqx_dxl(sku=ll.sku, hjyear='2020', hjmn='09', ck_id='XQD', qc=qc1, qm=qm1, xs_s=xs_s,
                                weidu='6',
                                last=last, sku_id=ggd.sku_id, cbj=ggd.jg1, dxl=res)
        db.session.add(ab_jqx_dxl)
        print(i)
        print('---------------')
    db.session.commit()

    # print(ll[0])
    # owenums = Owenum.query.all()
    # print(owenums[0]['sku']) # TypeError: 'Owenum' object is not subscriptable
    # for owenum in owenums:
    #     print(owenum.sku)
    return str(i)


@main_bp.route('/calc_dxl_ALL_3')
def calc_dxl_ALL_3():
    # lls = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sku).distinct().limit(30)
    lls = Jxc_rj_202008.query.with_entities(Jxc_rj_202008.sku, Jxc_rj_202008.sku_id).distinct().filter(
        Jxc_rj_202008.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(date='2020-08-31').filter(
        Jxc_rj_202008.sl_qm != 0).all()
    # print(lls)
    i = 0
    for ll in lls:
        print(ll.sku)
        print(ll.sku_id)
        i = i + 1


        bbs = Jxc_rj_202006.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-06-01'). \
            filter(Jxc_rj_202006.ck_id.in_(['2', '3', '4', '11', '15'])). \
            with_entities(func.sum(Jxc_rj_202006.sl_qc)).all()
        # print(bbs)
        # print(bbs[0])
        # print(bbs[0][0])
        if bbs[0][0]:
            qc1 = bbs[0][0]
        else:
            qc1 = 0
        print(qc1)

        bbss = Jxc_rj_202008.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-08-31'). \
            filter(Jxc_rj_202008.ck_id.in_(['2', '3', '4', '11', '15'])). \
            with_entities(func.sum(Jxc_rj_202008.sl_qm)).all()
        print(bbss)
        if bbss[0][0]:
            qm1 = bbss[0][0]
        else:
            qm1 = 0
        print(qm1)

        # 求和  User.query.with_entities(func.sum(User.id)).all()
        jh1 = Jxc_rj_202006.query.filter(Jxc_rj_202006.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202006.sl0_ls + Jxc_rj_202006.sl0_pf)).all()
        jh2 = Jxc_rj_202007.query.filter(Jxc_rj_202007.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202007.sl0_ls + Jxc_rj_202007.sl0_pf)).all()
        jh3 = Jxc_rj_202008.query.filter(Jxc_rj_202008.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202008.sl0_ls + Jxc_rj_202008.sl0_pf)).all()

        # print(jh1[0][0])  #None   3
        # print(jh1[0])     #(None,) (Decimal('3'),)
        # print(jh2)
        # print(jh3)
        # print(jh4)
        if jh1[0][0]:
            jh1 = jh1[0][0]
        else:
            jh1 = 0
        # if jh2[0][0]:
        #     jh2 = jh2[0][0]
        # else:
        if jh2[0][0]:
            jh2 = jh2[0][0]
        else:
            jh2 = 0
        if jh3[0][0]:
            jh3 = jh3[0][0]
        else:
            jh3 = 0

        xs_s = jh1 + jh2 + jh3
        # print(xs_s)
        # 计算滞销量
        last = min(max(qc1 - xs_s, 0), qm1)
        # 同步最新成本价
        # jg1 = Spjgb.query.filter_by(goods_id=ll.goods_id).all()
        # ggd = Jxc_rj_202005.query.filter_by(sku=ll.sku).first()
        # print(ggd.sku_id)
        ggd = Spjgb.query.filter_by(sku_id=ll.sku_id).first()
        # print(ggd.jg1)
        # 计算动销率
        qc1 = float(qc1)
        if qc1 * ggd.jg1 == 0:  # 被除数为0
            res = 0
        else:
            ssd = qc1 * ggd.jg1
            ssdds = float(xs_s) * float(ggd.jg1)
            # 迫使您将浮点数转换为小数， 更精确  float是会四舍五入
            # dxl = Decimal(str(ssdds))/Decimal(str(ssd))  注意decimal类型的数据不可以和普通浮点数进行运算。 TypeError: unsupported operand type(s) for +: 'float'and 'Decimal'
            res = format(ssdds / float(ssd), '.2f')
        print(res)
        # break
        # order_info = Order_info(tid=tid, delivery_province=delivery_province, delivery_city=delivery_city,
        #                         delivery_district=delivery_district, receiver_tel=receiver_tel,
        #                         delivery_address=delivery_address)
        # db.session.add(order_info)
        # db.session.commit()
        ab_jqx_dxl = Ab_jqx_dxl(sku=ll.sku, hjyear='2020', hjmn='08', ck_id='ALL', qc=qc1, qm=qm1, xs_s=xs_s, weidu='3',
                                last=last, sku_id=ggd.sku_id, cbj=ggd.jg1, dxl=res)
        db.session.add(ab_jqx_dxl)
        print(i)
        print('---------------')
    db.session.commit()

    # print(ll[0])
    # owenums = Owenum.query.all()
    # print(owenums[0]['sku']) # TypeError: 'Owenum' object is not subscriptable
    # for owenum in owenums:
    #     print(owenum.sku)
    return str(i)


@main_bp.route('/calc_dxl_ALL_4')
def calc_dxl_ALL_4():
    # lls = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sku).distinct().limit(30)
    lls = Jxc_rj_202006.query.with_entities(Jxc_rj_202006.sku, Jxc_rj_202006.sku_id).distinct().filter(
        Jxc_rj_202006.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(date='2020-06-30').filter(
        Jxc_rj_202006.sl_qm != 0).all()
    # print(lls)
    i = 0
    for ll in lls:
        print(ll.sku)
        print(ll.sku_id)
        i = i + 1
        # return str(i)

        """
        bbs = Jxc_rj_202002.query.filter(Jxc_rj_202002.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            date='2020-02-01').filter_by(
            sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        if bbs:
            # print('33')
            # print(bbs.sl_qc)  # 错误  print(bbs['sl_qm'])
            qc1 = bbs.sl_qc
        else:
            qc1 = 0
        bbss = Jxc_rj_202005.query.filter(Jxc_rj_202005.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            date='2020-05-31').filter_by(
            sku=ll.sku).first()
        if bbss:
            # print('44')
            # print(bbss.sl_qm)  # 错误  print(bbs['sl_qm'])
            qm1 = bbss.sl_qm
        else:
            qm1 = 0
        """

        bbs = Jxc_rj_202003.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-03-01'). \
            filter(Jxc_rj_202003.ck_id.in_(['2', '3', '4', '11', '15'])). \
            with_entities(func.sum(Jxc_rj_202003.sl_qc)).all()
        # print(bbs)
        # print(bbs[0])
        # print(bbs[0][0])
        if bbs[0][0]:
            qc1 = bbs[0][0]
        else:
            qc1 = 0
        print(qc1)

        bbss = Jxc_rj_202006.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-06-30'). \
            filter(Jxc_rj_202006.ck_id.in_(['2', '3', '4', '11', '15'])). \
            with_entities(func.sum(Jxc_rj_202006.sl_qm)).all()
        print(bbss)
        if bbss[0][0]:
            qm1 = bbss[0][0]
        else:
            qm1 = 0
        print(qm1)

        # 求和  User.query.with_entities(func.sum(User.id)).all()
        jh1 = Jxc_rj_202006.query.filter(Jxc_rj_202006.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202006.sl0_ls + Jxc_rj_202006.sl0_pf)).all()
        jh2 = Jxc_rj_202003.query.filter(Jxc_rj_202003.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202003.sl0_ls + Jxc_rj_202003.sl0_pf)).all()
        jh3 = Jxc_rj_202004.query.filter(Jxc_rj_202004.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202004.sl0_ls + Jxc_rj_202004.sl0_pf)).all()
        jh4 = Jxc_rj_202005.query.filter(Jxc_rj_202005.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202005.sl0_ls + Jxc_rj_202005.sl0_pf)).all()
        # print(jh1[0][0])  #None   3
        # print(jh1[0])     #(None,) (Decimal('3'),)
        # print(jh2)
        # print(jh3)
        # print(jh4)
        if jh1[0][0]:
            jh1 = jh1[0][0]
        else:
            jh1 = 0
        if jh2[0][0]:
            jh2 = jh2[0][0]
        else:
            jh2 = 0
        if jh3[0][0]:
            jh3 = jh3[0][0]
        else:
            jh3 = 0
        if jh4[0][0]:
            jh4 = jh4[0][0]
        else:
            jh4 = 0
        xs_s = jh1 + jh2 + jh3 + jh4
        # print(xs_s)
        # 计算滞销量
        last = min(max(qc1 - xs_s, 0), qm1)
        # 同步最新成本价
        # jg1 = Spjgb.query.filter_by(goods_id=ll.goods_id).all()
        # ggd = Jxc_rj_202005.query.filter_by(sku=ll.sku).first()
        # print(ggd.sku_id)
        ggd = Spjgb.query.filter_by(sku_id=ll.sku_id).first()
        # print(ggd.jg1)
        # 计算动销率
        qc1 = float(qc1)
        if qc1 * ggd.jg1 == 0:  # 被除数为0
            res = 0
        else:
            ssd = qc1 * ggd.jg1
            ssdds = float(xs_s) * float(ggd.jg1)
            # 迫使您将浮点数转换为小数， 更精确  float是会四舍五入
            # dxl = Decimal(str(ssdds))/Decimal(str(ssd))  注意decimal类型的数据不可以和普通浮点数进行运算。 TypeError: unsupported operand type(s) for +: 'float'and 'Decimal'
            res = format(ssdds / float(ssd), '.2f')
        print(res)
        # break
        # order_info = Order_info(tid=tid, delivery_province=delivery_province, delivery_city=delivery_city,
        #                         delivery_district=delivery_district, receiver_tel=receiver_tel,
        #                         delivery_address=delivery_address)
        # db.session.add(order_info)
        # db.session.commit()
        ab_jqx_dxl = Ab_jqx_dxl(sku=ll.sku, hjyear='2020', hjmn='06', ck_id='ALL', qc=qc1, qm=qm1, xs_s=xs_s, weidu='4',
                                last=last, sku_id=ggd.sku_id, cbj=ggd.jg1, dxl=res)
        db.session.add(ab_jqx_dxl)
        print(i)
        print('---------------')
    db.session.commit()

    # print(ll[0])
    # owenums = Owenum.query.all()
    # print(owenums[0]['sku']) # TypeError: 'Owenum' object is not subscriptable
    # for owenum in owenums:
    #     print(owenum.sku)
    return str(i)


@main_bp.route('/calc_dxl_ALL_6')
def calc_dxl_ALL_6():
    # lls = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sku).distinct().limit(30)
    lls = Jxc_rj_202007.query.with_entities(Jxc_rj_202007.sku, Jxc_rj_202007.sku_id).distinct().filter(
        Jxc_rj_202007.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(date='2020-07-31').filter(
        Jxc_rj_202007.sl_qm != 0).all()
    # print(lls)
    i = 0
    for ll in lls:
        print(ll.sku)
        print(ll.sku_id)
        i = i + 1
        # return str(i)

        """
        bbs = Jxc_rj_202002.query.filter(Jxc_rj_202002.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            date='2020-02-01').filter_by(
            sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        if bbs:
            # print('33')
            # print(bbs.sl_qc)  # 错误  print(bbs['sl_qm'])
            qc1 = bbs.sl_qc
        else:
            qc1 = 0
        bbss = Jxc_rj_202005.query.filter(Jxc_rj_202005.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            date='2020-05-31').filter_by(
            sku=ll.sku).first()
        if bbss:
            # print('44')
            # print(bbss.sl_qm)  # 错误  print(bbs['sl_qm'])
            qm1 = bbss.sl_qm
        else:
            qm1 = 0
        """

        bbs = Jxc_rj_202002.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-02-01'). \
            filter(Jxc_rj_202002.ck_id.in_(['2', '3', '4', '11', '15'])). \
            with_entities(func.sum(Jxc_rj_202002.sl_qc)).all()
        # print(bbs)
        # print(bbs[0])
        # print(bbs[0][0])
        if bbs[0][0]:
            qc1 = bbs[0][0]
        else:
            qc1 = 0
        print(qc1)

        bbss = Jxc_rj_202007.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-07-31'). \
            filter(Jxc_rj_202007.ck_id.in_(['2', '3', '4', '11', '15'])). \
            with_entities(func.sum(Jxc_rj_202007.sl_qm)).all()
        print(bbss)
        if bbss[0][0]:
            qm1 = bbss[0][0]
        else:
            qm1 = 0
        print(qm1)

        # 求和  User.query.with_entities(func.sum(User.id)).all()
        jh1 = Jxc_rj_202002.query.filter(Jxc_rj_202002.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202002.sl0_ls + Jxc_rj_202002.sl0_pf)).all()
        jh2 = Jxc_rj_202003.query.filter(Jxc_rj_202003.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202003.sl0_ls + Jxc_rj_202003.sl0_pf)).all()
        jh3 = Jxc_rj_202004.query.filter(Jxc_rj_202004.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202004.sl0_ls + Jxc_rj_202004.sl0_pf)).all()
        jh4 = Jxc_rj_202005.query.filter(Jxc_rj_202005.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202005.sl0_ls + Jxc_rj_202005.sl0_pf)).all()
        jh5 = Jxc_rj_202007.query.filter(Jxc_rj_202007.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202007.sl0_ls + Jxc_rj_202007.sl0_pf)).all()
        jh6 = Jxc_rj_202006.query.filter(Jxc_rj_202006.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202006.sl0_ls + Jxc_rj_202006.sl0_pf)).all()
        # print(jh1[0][0])  #None   3
        # print(jh1[0])     #(None,) (Decimal('3'),)
        # print(jh2)
        # print(jh3)
        # print(jh4)
        if jh1[0][0]:
            jh1 = jh1[0][0]
        else:
            jh1 = 0
        if jh2[0][0]:
            jh2 = jh2[0][0]
        else:
            jh2 = 0
        if jh3[0][0]:
            jh3 = jh3[0][0]
        else:
            jh3 = 0
        if jh4[0][0]:
            jh4 = jh4[0][0]
        else:
            jh4 = 0
        if jh5[0][0]:
            jh5 = jh5[0][0]
        else:
            jh5 = 0
        if jh6[0][0]:
            jh6 = jh6[0][0]
        else:
            jh6 = 0
        xs_s = jh1 + jh2 + jh3 + jh4 + jh5 + jh6
        # print(xs_s)
        # 计算滞销量
        last = min(max(qc1 - xs_s, 0), qm1)
        # 同步最新成本价
        # jg1 = Spjgb.query.filter_by(goods_id=ll.goods_id).all()
        # ggd = Jxc_rj_202005.query.filter_by(sku=ll.sku).first()
        # print(ggd.sku_id)
        ggd = Spjgb.query.filter_by(sku_id=ll.sku_id).first()
        # print(ggd.jg1)
        # 计算动销率
        qc1 = float(qc1)
        if qc1 * ggd.jg1 == 0:  # 被除数为0
            res = 0
        else:
            ssd = qc1 * ggd.jg1
            ssdds = float(xs_s) * float(ggd.jg1)
            # 迫使您将浮点数转换为小数， 更精确  float是会四舍五入
            # dxl = Decimal(str(ssdds))/Decimal(str(ssd))  注意decimal类型的数据不可以和普通浮点数进行运算。 TypeError: unsupported operand type(s) for +: 'float'and 'Decimal'
            res = format(ssdds / float(ssd), '.2f')
        print(res)
        # break
        # order_info = Order_info(tid=tid, delivery_province=delivery_province, delivery_city=delivery_city,
        #                         delivery_district=delivery_district, receiver_tel=receiver_tel,
        #                         delivery_address=delivery_address)
        # db.session.add(order_info)
        # db.session.commit()
        ab_jqx_dxl = Ab_jqx_dxl(sku=ll.sku, hjyear='2020', hjmn='07', ck_id='ALL', qc=qc1, qm=qm1, xs_s=xs_s, weidu='6',
                                last=last, sku_id=ggd.sku_id, cbj=ggd.jg1, dxl=res)
        db.session.add(ab_jqx_dxl)
        print(i)
        print('---------------')
    db.session.commit()

    # print(ll[0])
    # owenums = Owenum.query.all()
    # print(owenums[0]['sku']) # TypeError: 'Owenum' object is not subscriptable
    # for owenum in owenums:
    #     print(owenum.sku)
    return str(i)


@main_bp.route('/calc_dxl_ALL_12')
def calc_dxl_ALL_12():
    # lls = Jxc_rj_202005.query.with_entities(Jxc_rj_202005.sku).distinct().limit(30)
    lls = Jxc_rj_202007.query.with_entities(Jxc_rj_202007.sku, Jxc_rj_202007.sku_id).distinct().filter(
        Jxc_rj_202007.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(date='2020-07-31').filter(
        Jxc_rj_202007.sl_qm != 0).all()
    # print(lls)
    i = 0
    for ll in lls:
        print(ll.sku)
        print(ll.sku_id)
        i = i + 1
        # return str(i)

        """
        bbs = Jxc_rj_202002.query.filter(Jxc_rj_202002.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            date='2020-02-01').filter_by(
            sku=ll.sku).first()  # 这里虽然只有一条,但是也不能用one(),大于1或小于1丢会报错,估计一般还是用first
        # print(bbs)
        if bbs:
            # print('33')
            # print(bbs.sl_qc)  # 错误  print(bbs['sl_qm'])
            qc1 = bbs.sl_qc
        else:
            qc1 = 0
        bbss = Jxc_rj_202005.query.filter(Jxc_rj_202005.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            date='2020-05-31').filter_by(
            sku=ll.sku).first()
        if bbss:
            # print('44')
            # print(bbss.sl_qm)  # 错误  print(bbs['sl_qm'])
            qm1 = bbss.sl_qm
        else:
            qm1 = 0
        """

        bbs = Jxc_rj_202002.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-02-01'). \
            filter(Jxc_rj_202002.ck_id.in_(['2', '3', '4', '11', '15'])). \
            with_entities(func.sum(Jxc_rj_202002.sl_qc)).all()
        # print(bbs)
        # print(bbs[0])
        # print(bbs[0][0])
        if bbs[0][0]:
            qc1 = bbs[0][0]
        else:
            qc1 = 0
        print(qc1)

        bbss = Jxc_rj_202007.query. \
            filter_by(sku=ll.sku). \
            filter_by(date='2020-07-31'). \
            filter(Jxc_rj_202007.ck_id.in_(['2', '3', '4', '11', '15'])). \
            with_entities(func.sum(Jxc_rj_202007.sl_qm)).all()
        print(bbss)
        if bbss[0][0]:
            qm1 = bbss[0][0]
        else:
            qm1 = 0
        print(qm1)

        # 求和  User.query.with_entities(func.sum(User.id)).all()
        jh1 = Jxc_rj_202002.query.filter(Jxc_rj_202002.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202002.sl0_ls + Jxc_rj_202002.sl0_pf)).all()
        jh2 = Jxc_rj_202003.query.filter(Jxc_rj_202003.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202003.sl0_ls + Jxc_rj_202003.sl0_pf)).all()
        jh3 = Jxc_rj_202004.query.filter(Jxc_rj_202004.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202004.sl0_ls + Jxc_rj_202004.sl0_pf)).all()
        jh4 = Jxc_rj_202005.query.filter(Jxc_rj_202005.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202005.sl0_ls + Jxc_rj_202005.sl0_pf)).all()
        jh5 = Jxc_rj_202007.query.filter(Jxc_rj_202007.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202007.sl0_ls + Jxc_rj_202007.sl0_pf)).all()
        jh6 = Jxc_rj_202006.query.filter(Jxc_rj_202006.ck_id.in_(['2', '3', '4', '11', '15'])).filter_by(
            sku=ll.sku).with_entities(
            func.sum(Jxc_rj_202006.sl0_ls + Jxc_rj_202006.sl0_pf)).all()
        # print(jh1[0][0])  #None   3
        # print(jh1[0])     #(None,) (Decimal('3'),)
        # print(jh2)
        # print(jh3)
        # print(jh4)
        if jh1[0][0]:
            jh1 = jh1[0][0]
        else:
            jh1 = 0
        if jh2[0][0]:
            jh2 = jh2[0][0]
        else:
            jh2 = 0
        if jh3[0][0]:
            jh3 = jh3[0][0]
        else:
            jh3 = 0
        if jh4[0][0]:
            jh4 = jh4[0][0]
        else:
            jh4 = 0
        if jh5[0][0]:
            jh5 = jh5[0][0]
        else:
            jh5 = 0
        if jh6[0][0]:
            jh6 = jh6[0][0]
        else:
            jh6 = 0
        xs_s = jh1 + jh2 + jh3 + jh4 + jh5 + jh6
        # print(xs_s)
        # 计算滞销量
        last = min(max(qc1 - xs_s, 0), qm1)
        # 同步最新成本价
        # jg1 = Spjgb.query.filter_by(goods_id=ll.goods_id).all()
        # ggd = Jxc_rj_202005.query.filter_by(sku=ll.sku).first()
        # print(ggd.sku_id)
        ggd = Spjgb.query.filter_by(sku_id=ll.sku_id).first()
        # print(ggd.jg1)
        # 计算动销率
        qc1 = float(qc1)
        if qc1 * ggd.jg1 == 0:  # 被除数为0
            res = 0
        else:
            ssd = qc1 * ggd.jg1
            ssdds = float(xs_s) * float(ggd.jg1)
            # 迫使您将浮点数转换为小数， 更精确  float是会四舍五入
            # dxl = Decimal(str(ssdds))/Decimal(str(ssd))  注意decimal类型的数据不可以和普通浮点数进行运算。 TypeError: unsupported operand type(s) for +: 'float'and 'Decimal'
            res = format(ssdds / float(ssd), '.2f')
        print(res)
        # break
        # order_info = Order_info(tid=tid, delivery_province=delivery_province, delivery_city=delivery_city,
        #                         delivery_district=delivery_district, receiver_tel=receiver_tel,
        #                         delivery_address=delivery_address)
        # db.session.add(order_info)
        # db.session.commit()
        ab_jqx_dxl = Ab_jqx_dxl(sku=ll.sku, hjyear='2020', hjmn='07', ck_id='ALL', qc=qc1, qm=qm1, xs_s=xs_s, weidu='6',
                                last=last, sku_id=ggd.sku_id, cbj=ggd.jg1, dxl=res)
        db.session.add(ab_jqx_dxl)
        print(i)
        print('---------------')
    db.session.commit()

    # print(ll[0])
    # owenums = Owenum.query.all()
    # print(owenums[0]['sku']) # TypeError: 'Owenum' object is not subscriptable
    # for owenum in owenums:
    #     print(owenum.sku)
    return str(i)


@main_bp.route('/lfa')
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
    # URL_IP = 'https://www.v2ex.com/api/topics/hot.json'
    # response = requests.get(URL_IP)
    # gg = json.loads(response.text)
    # jayuu = gg[1]['title']
    # print(type(photos))
    URL_IP = 'https://www.v2ex.com/api/topics/hot.json'
    response = requests.get(URL_IP)
    gg = json.loads(response.text)
    # 把请求到的东西放在一个list里传给前端
    list1 = []
    for i in range(len(gg)):
        list1.append(dict(title=gg[i]['title'], url=gg[i]['url']))

    URL_IP = 'https://www.v2ex.com/api/topics/latest.json'
    response = requests.get(URL_IP)
    gg = json.loads(response.text)
    # 把请求到的东西放在一个list里传给前端
    list2 = []
    for i in range(len(gg)):
        list2.append(dict(title=gg[i]['title'], url=gg[i]['url']))
    return render_template('main/index.html', pagination=pagination, photos=photos, tags=tags, Collect=Collect,
                           list1=list1, list2=list2)


@main_bp.route('/explore')
def explore():
    photos = Photo.query.order_by(func.random()).limit(12)
    # print(photos)
    return render_template('main/explore.html', photos=photos)


# get请求
@main_bp.route('/explore2')
def explore2():
    # URL_IP = 'http://httpbin.org/ip'
    URL_IP = 'https://www.v2ex.com/api/topics/hot.json'
    response = requests.get(URL_IP)
    print('response headers:')
    print(response.headers)
    print('response body:')
    print(response.text)
    # print(response[0]['node']['title'])  # 去不到 各种报错
    gg = json.loads(response.text)
    print(gg[0]['node']['title'])
    return gg[0]['node']['title']


@main_bp.route('/zidian')
def zidian():
    URL_IP = 'https://www.v2ex.com/api/topics/hot.json'
    response = requests.get(URL_IP)
    gg = json.loads(response.text)
    list1 = []
    # 下面的方式无法判断总共有几个
    # for num in range(0, 8):
    #     # list1.append(gg[num]['node']['title'])
    #     # list1.append(gg[num]['title'])
    #     list1.append(dict(title=gg[num]['title'], url=gg[num]['url']))
    # list5 = ['张三', '李四', '王五']
    # dict1 = {i + 1: list5[i] for i in range(0, len(list5))}
    # # print(dict1)
    # for p in gg:
    #     list1.append(gg[p]['title'])
    for i in range(len(gg)):
        # print(i)
        # print(gg[i])
        list1.append(gg[i]['title'])
    return str(list1)


@main_bp.route('/tran_json')
def tran_json():
    str = '{"key": "wwww", "word": "qqqq"}'
    j = json.loads(str)
    print(j)
    return 'gg'


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


# MD5加密方法
def getmd5FromString(string):
    md5 = hashlib.md5()
    md5.update(string.encode(encoding='utf-8'))
    return md5.hexdigest()


@main_bp.route('/e3_get_user')
def e3_get_user():
    dtime = datetime.datetime.now()
    ans_time = time.mktime(dtime.timetuple())
    str_jay = '{"pageNo": 1, "sd_id": 117,"startModifiedTime":"2020-06-11 00:00:00"}'
    # jay2 = json.loads(str_jay)
    dict2 = {'key': '9iGuxYN',
             'requestTime': str(int(ans_time)),  # python并不能像java一样，在做拼接的时候自动把类型转换为string类型  把后面的.0去掉
             'secret': '5347e465cfb487c3515199a2df710e95',
             'version': '1.0',
             'serviceType': 'user.list.get',
             'data': str(str_jay)
             }
    # 遍历字典的几种方法  https://www.cnblogs.com/stuqx/p/7291948.html
    for (key, value) in dict2.items():
        print(key + ':' + value)
    # dict3 = sorted(dict2.items(), key=lambda dict2: dict2[0], reverse=False)  # False为升序   这里无需排序
    url = ""
    # for (key, value) in dict3:
    #     print(key + ':' + value)
    url += '&'.join([str(key) + '=' + str(value) for key, value in dict2.items()])
    print(url)
    # sha = hashlib.sha1(url.encode('utf-8'))
    # encrypts = sha.hexdigest()
    # url = url[1:]   截取字符串 从第二位开始截到最后
    # print(url)
    encrypts = getmd5FromString(url)  # 由SHA1改为MD5排序
    print(encrypts)
    bb = 'http://e3.mgmos.com.cn/e3/webopm/web/?app_act=api/ec&app_mode=func&'
    url = bb + url + '&sign=' + encrypts
    print(url)
    response = requests.get(url)
    return response.text


@main_bp.route('/delete_all', methods=['POST'])  # 这个必须要有,即使没有具体的页面,只是执行一段sql
def delete_all():
    try:
        db = pymysql.connect(host="10.10.19.6", port=5000, user="root",
                             passwd="qwer1234.",
                             db="flask_albumy2")
    except:
        print("could not connect to mysql server")
    cursor = db.cursor()
    sql = "delete from owenum"
    cursor.execute(sql)  # 执行sql语句
    db.commit()
    cursor.close()  # 关闭连接
    db.close()  # 关闭数据
    message = Markup(
        '已删除')
    flash(message, 'info')
    # 下面的两种跳转回去都可以yeah
    return redirect(url_for('main.owenum'))
    # return redirect_back()


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


@main_bp.route('/')
def lfa():
    return render_template('main/lfa.html')


@main_bp.route('/lfa2')
def lfa2():
    return render_template('main/lfa2.html')


@main_bp.route('/lfa3')
def lfa3():
    return render_template('main/lfa3.html')


# http://127.0.0.1:5010/explore4/E20200413162037038100001   没有问号的带参数
# url_for('main.explore4', _external=True, tid='E20200413162037038100001')
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
    flash('两单插入order_info成功', 'info')
    # 下面的两种跳转回去都可以yeah
    return redirect(url_for('main.lfa'))
    # return redirect_back()
    # return 'ff'


@main_bp.route('/post/manage')
@permission_required('POST')
@login_required
# @cache.cached(timeout=10 * 60)
@cache.cached(timeout=10 * 60, query_string=True)  # 包含查询参数的路由  10min后过期
def manage_post():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['BLUELOG_MANAGE_POST_PER_PAGE'])
    posts = pagination.items
    return render_template('main/manage_post.html', page=page, pagination=pagination, posts=posts)


@main_bp.route('/delete_cache')
def delete_cache():
    # cache.delete('view/%s' % url_for('main.manage_post'))  传了page = request.args.get('page', 1, type=int)就不行
    # print(url_for('main.manage_post', page=3))   传了page = request.args.get('page', 1, type=int)就不行
    cache.clear()  # 清除所有缓存 行
    return 'ss'


@main_bp.route('/owenum', methods=['GET', 'POST'])
# @permission_required('POST')
@login_required
def owenum():
    form = OweSearchForm()
    if form.validate_on_submit():
        page = 1  # 按不然找不到该页面
        pagination = Owenum.query.filter_by(sku=form.sku.data).order_by(Owenum.id).paginate(
            page, per_page=current_app.config['BLUELOG_MANAGE_POST_PER_PAGE'])
        owenums = pagination.items
        # print(Post.query.filter_by(title=form.username.data).order_by(Post.timestamp.desc()))
        # return render_template('main/manage_post.html', page=page, pagination=pagination, posts=posts)
        # form.sku.data=form.sku.data
        return render_template('main/owenum.html', form=form, page=page, pagination=pagination, owenums=owenums)
    page = request.args.get('page', 1, type=int)
    pagination = Owenum.query.order_by(Owenum.id).paginate(
        page, per_page=current_app.config['BLUELOG_MANAGE_POST_PER_PAGE'])
    owenums = pagination.items
    return render_template('main/owenum.html', page=page, pagination=pagination, owenums=owenums, form=form)


@main_bp.route('/dxl', methods=['GET', 'POST'])
# @permission_required('POST')
@login_required
def dxl():
    form = DxlSearchForm()
    if form.validate_on_submit():
        if form.submit.data:
            # page = 1  # 按不然找不到该页面
            page = request.args.get('page', 1, type=int)
            # 最初
            # pagination = Ab_jqx_dxl.query.filter_by(hjyear=form.hjyear.data).filter_by(hjmn=form.hjmn.data).filter_by(weidu=form.weidu.data).order_by(Ab_jqx_dxl.id).paginate(
            #     page, per_page=current_app.config['BLUELOG_MANAGE_POST_PER_PAGE'])
            # 感觉还不够满足
            # if form.sku.data:
            #     pagination = Ab_jqx_dxl.query.filter_by(sku=form.sku.data).filter_by(hjyear=form.hjyear.data).filter_by(hjmn=form.hjmn.data).filter_by(
            #         weidu=form.weidu.data).order_by(Ab_jqx_dxl.id).paginate(
            #         page, per_page=current_app.config['BLUELOG_MANAGE_POST_PER_PAGE'])
            # else:
            #     pagination = Ab_jqx_dxl.query.filter_by(hjyear=form.hjyear.data).filter_by(
            #         hjmn=form.hjmn.data).filter_by(
            #         weidu=form.weidu.data).order_by(Ab_jqx_dxl.id).paginate(
            #         page, per_page=current_app.config['BLUELOG_MANAGE_POST_PER_PAGE'])
            # 终于找到了最终解决方案 sqlalchemy多条件查询 https://blog.csdn.net/mxj588love/article/details/80729790 filter牛逼于filter_by
            textsql = " 1=1 "
            if form.sku.data:
                textsql += " and sku='" + form.sku.data + "' "
            if form.weidu.data:
                textsql += " and weidu='" + form.weidu.data + "' "
            if form.hjyear.data:
                textsql += " and hjyear='" + form.hjyear.data + "' "
            if form.hjmn.data:
                textsql += " and hjmn='" + form.hjmn.data + "' "
            if form.ck_id.data:
                textsql += " and ck_id='" + form.ck_id.data + "' "
            pagination = Ab_jqx_dxl.query.filter(Ab_jqx_dxl.last != 0).filter(text(textsql)).order_by(
                Ab_jqx_dxl.id).paginate(
                page, per_page=10000)
            dxls = pagination.items
            # print(Post.query.filter_by(title=form.username.data).order_by(Post.timestamp.desc()))
            # return render_template('main/manage_post.html', page=page, pagination=pagination, posts=posts)
            # form.sku.data=form.sku.data
            return render_template('main/dxl.html', form=form, page=page, pagination=pagination, dxls=dxls)
        if form.submit_excel.data:
            # 按条件开始取数据,开始下载到upload里
            export_dxl()
            # page = 1  # 按不然找不到该页面
            page = request.args.get('page', 1, type=int)
            textsql = " 1=1 "
            if form.sku.data:
                textsql += " and sku='" + form.sku.data + "' "
            if form.weidu.data:
                textsql += " and weidu='" + form.weidu.data + "' "
            if form.hjyear.data:
                textsql += " and hjyear='" + form.hjyear.data + "' "
            if form.hjmn.data:
                textsql += " and hjmn='" + form.hjmn.data + "' "
            if form.ck_id.data:
                textsql += " and ck_id='" + form.ck_id.data + "' "
            pagination = Ab_jqx_dxl.query.filter(Ab_jqx_dxl.last != 0).filter(text(textsql)).order_by(
                Ab_jqx_dxl.id).paginate(
                page, per_page=10000)
            dxls = pagination.items
            return render_template('main/dxl.html', form=form, page=page, pagination=pagination, dxls=dxls)
    page = request.args.get('page', 1, type=int)
    pagination = Ab_jqx_dxl.query.filter(Ab_jqx_dxl.last != 0).order_by(Ab_jqx_dxl.id).paginate(
        page, per_page=current_app.config['BLUELOG_MANAGE_POST_PER_PAGE'])
    dxls = pagination.items
    return render_template('main/dxl.html', page=page, pagination=pagination, dxls=dxls, form=form)


@main_bp.route('/post/<int:post_id>')
def show_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('main/post.html', post=post)


def random_filename(filename):
    ext = os.path.splitext(filename)[1]
    new_filename = uuid.uuid4().hex + ext
    return new_filename


# def open_excel(ss):
#     try:
#         book = xlrd.open_workbook(ss)  # 文件名，把文件与py文件放在同一目录下
#     except:
#         print("open excel file failed!")
#     try:
#         sheet = book.sheet_by_name("Sheet1")  # execl里面的worksheet1
#         return sheet
#     except:
#         print("locate worksheet in excel failed!")


def open_excel(filename):
    try:
        LUJIN = os.getenv('LUJIN')
        name = r"albumy\uploads\%s" % filename
        name = LUJIN + name
        print(name)
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
        shiji = int(sheet.cell(i, 1).value)  # 取第i行第1列，下面依次类推
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
        # sum = ret[0]
        sum = int(ret[0] or 0)
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
                value = (sku)
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
                value = (owe2, left, left, sku, id2)
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
            print(sheet)
            insert_owe_process(sheet, filename)

    return render_template('main/upload_owe.html', form=form)


@main_bp.route('/export_owe', methods=['GET', 'POST'])
def export_owe():
    wb = xlwt.Workbook()
    # 添加一个表
    ws = wb.add_sheet('Sheet1')

    # 3个参数分别为行号，列号，和内容
    # 需要注意的是行号和列号都是从0开始的
    ws.write(0, 0, 'id')
    ws.write(0, 1, 'sku')
    ws.write(0, 2, 'yao')
    ws.write(0, 3, 'shiji')
    ws.write(0, 4, 'owe')
    ws.write(0, 5, 'receive_date')
    owenums = Owenum.query.all()
    print(owenums[0])
    i = 1
    for owenum in owenums:
        ws.write(i, 0, owenum.id)
        ws.write(i, 1, owenum.sku)
        ws.write(i, 2, owenum.yao)
        ws.write(i, 3, owenum.shiji)
        ws.write(i, 4, owenum.owe)
        ws.write(i, 5, owenum.receive_date)
        i = i + 1

    # 保存excel文件
    wb.save('./uploads/export.xls')
    return render_template('main/export_excel.html')


@main_bp.route('/export_117', methods=['GET', 'POST'])
def export_117():
    wb = xlwt.Workbook()
    # 添加一个表
    ws = wb.add_sheet('Sheet1', cell_overwrite_ok=True)

    # 3个参数分别为行号，列号，和内容
    # 需要注意的是行号和列号都是从0开始的
    ws.write(0, 0, 'goods_sn')
    ws.write(0, 1, 'sku')
    ws.write(0, 2, 'outer_goods_name')
    ws.write(0, 3, 'goods_barcode')
    ws.write(0, 4, 'STATUS')
    ws.write(0, 5, 'approve_status')
    ws.write(0, 6, 'outer_goods_id')
    ws.write(0, 7, 'outer_goods_url')
    # owenums = Owenum.query.all()
    # print(owenums[0])
    # i = 1
    # for owenum in owenums:
    #     ws.write(i, 0, owenum.id)
    #     ws.write(i, 1, owenum.sku)
    #     ws.write(i, 2, owenum.yao)
    #     ws.write(i, 3, owenum.shiji)
    #     ws.write(i, 4, owenum.owe)
    #     ws.write(i, 5, owenum.receive_date)
    #     i = i + 1
    try:
        db = pymysql.connect(host="192.168.10.22", port=9966, user="jusrrjd76hud",
                             passwd="MgBaIsOn20191022AbYz",
                             db="mg_e3")
    except:
        print("could not connect to mysql server")
    cursor = db.cursor()

    sql = '''SELECT
 goods_sn,
  sku,
 outer_goods_name,
 goods_barcode,
 CASE STATUS
WHEN 0 THEN
 '禁止同步'
WHEN 1 THEN
 '自动同步'
END AS STATUS,
 CASE approve_status
WHEN 'onsale' THEN
 '在售'
WHEN 'instock' THEN
 '下架'
END AS approve_status,
 outer_goods_id,
 outer_goods_url
FROM
 (SELECT a.sku,a.goods_sn,g.goods_sn as goods_barcode,kehu_id,g.outer_goods_name,g.outer_goods_id,g.outer_goods_url,g.approve_status,g.status
FROM goods_sku a  LEFT JOIN goods_outer_sku g ON a.sku_id=g.goods_sku_id ,
kehu
WHERE is_tc=0
AND is_gd=0
AND g.kehu_id=kehu.Id
-- 非套餐非商品级
union all
SELECT a.sku,a.goods_sn,g.goods_sn as goods_barcode,kehu_id,g.outer_goods_name,g.outer_goods_id,g.outer_goods_url,g.approve_status,g.status
FROM goods_sku a  LEFT JOIN goods_outer_sku g ON a.goods_sn=g.goods_sku,
kehu
WHERE is_gd=1
AND g.kehu_id=kehu.Id
GROUP BY a.sku,status,khmc
-- 商品级
union all
SELECT t.sku,t.goods_sn,t.tc_sku as goods_barcode,kehu_id,g.outer_goods_name,g.outer_goods_id,g.outer_goods_url,g.approve_status,g.status
FROM goods_outer_sku g LEFT JOIN taocan_goods_mx t ON t.tc_sku=g.goods_sku,
kehu
WHERE is_tc=1
AND g.kehu_id=kehu.Id) a
WHERE
 kehu_id = 117
ORDER BY
 goods_sn,
 sku;'''
    cursor.execute(sql)  # 执行sql语句
    ret = cursor.fetchall()
    # print(ret)
    i = 1
    for row in ret:
        # print(row[0])
        ws.write(i, 0, row[0])
        ws.write(i, 1, row[1])
        ws.write(i, 2, row[2])
        ws.write(i, 3, row[3])
        ws.write(i, 4, row[4])
        ws.write(i, 5, row[5])
        ws.write(i, 6, row[6])
        ws.write(i, 7, row[7])
        i = i + 1
    # 保存excel文件
    wb.save('./uploads/export_shg.xls')
    cursor.close()
    db.close()
    return render_template('main/export_117.html')


@main_bp.route('/export_3', methods=['GET', 'POST'])
def export_3():
    wb = xlwt.Workbook()
    # 添加一个表
    ws = wb.add_sheet('Sheet1', cell_overwrite_ok=True)

    # 3个参数分别为行号，列号，和内容
    # 需要注意的是行号和列号都是从0开始的
    ws.write(0, 0, 'goods_sn')
    ws.write(0, 1, 'sku')
    ws.write(0, 2, 'outer_goods_name')
    ws.write(0, 3, 'goods_barcode')
    ws.write(0, 4, 'STATUS')
    ws.write(0, 5, 'approve_status')
    ws.write(0, 6, 'outer_goods_id')
    ws.write(0, 7, 'outer_goods_url')
    # owenums = Owenum.query.all()
    # print(owenums[0])
    # i = 1
    # for owenum in owenums:
    #     ws.write(i, 0, owenum.id)
    #     ws.write(i, 1, owenum.sku)
    #     ws.write(i, 2, owenum.yao)
    #     ws.write(i, 3, owenum.shiji)
    #     ws.write(i, 4, owenum.owe)
    #     ws.write(i, 5, owenum.receive_date)
    #     i = i + 1
    try:
        db = pymysql.connect(host="192.168.10.22", port=9966, user="jusrrjd76hud",
                             passwd="MgBaIsOn20191022AbYz",
                             db="mg_e3")
    except:
        print("could not connect to mysql server")
    cursor = db.cursor()

    sql = '''SELECT
 goods_sn,
  sku,
 outer_goods_name,
 goods_barcode,
 CASE STATUS
WHEN 0 THEN
 '禁止同步'
WHEN 1 THEN
 '自动同步'
END AS STATUS,
 CASE approve_status
WHEN 'onsale' THEN
 '在售'
WHEN 'instock' THEN
 '下架'
END AS approve_status,
 outer_goods_id,
 outer_goods_url
FROM
 (SELECT a.sku,a.goods_sn,g.goods_sn as goods_barcode,kehu_id,g.outer_goods_name,g.outer_goods_id,g.outer_goods_url,g.approve_status,g.status
FROM goods_sku a  LEFT JOIN goods_outer_sku g ON a.sku_id=g.goods_sku_id ,
kehu
WHERE is_tc=0
AND is_gd=0
AND g.kehu_id=kehu.Id
-- 非套餐非商品级
union all
SELECT a.sku,a.goods_sn,g.goods_sn as goods_barcode,kehu_id,g.outer_goods_name,g.outer_goods_id,g.outer_goods_url,g.approve_status,g.status
FROM goods_sku a  LEFT JOIN goods_outer_sku g ON a.goods_sn=g.goods_sku,
kehu
WHERE is_gd=1
AND g.kehu_id=kehu.Id
GROUP BY a.sku,status,khmc
-- 商品级
union all
SELECT t.sku,t.goods_sn,t.tc_sku as goods_barcode,kehu_id,g.outer_goods_name,g.outer_goods_id,g.outer_goods_url,g.approve_status,g.status
FROM goods_outer_sku g LEFT JOIN taocan_goods_mx t ON t.tc_sku=g.goods_sku,
kehu
WHERE is_tc=1
AND g.kehu_id=kehu.Id) a
WHERE
 kehu_id = 3
ORDER BY
 goods_sn,
 sku;'''
    cursor.execute(sql)  # 执行sql语句
    ret = cursor.fetchall()
    # print(ret)
    i = 1
    for row in ret:
        # print(row[0])
        ws.write(i, 0, row[0])
        ws.write(i, 1, row[1])
        ws.write(i, 2, row[2])
        ws.write(i, 3, row[3])
        ws.write(i, 4, row[4])
        ws.write(i, 5, row[5])
        ws.write(i, 6, row[6])
        ws.write(i, 7, row[7])
        i = i + 1
    # 保存excel文件
    wb.save('./uploads/export_qjd.xls')
    cursor.close()
    db.close()
    return render_template('main/export_3.html')


#pymysql获得单条数据
@main_bp.route('/pymysql1', methods=['GET', 'POST'])
def pymysql1():

    # 连接database
    conn = pymysql.connect(host="192.168.10.22", port=9966, user="jusrrjd76hud",
                             passwd="MgBaIsOn20191022AbYz",
                             db="mg_e3")
    # 得到一个可以执行SQL语句的光标对象
    cursor = conn.cursor()
    # 查询数据的SQL语句
    sql = "SELECT khdm,khmc from kehu;"
    # 执行SQL语句
    cursor.execute(sql)
    # 获取单条查询数据
    ret = cursor.fetchone()
    cursor.close()
    conn.close()
    # 打印下查询结果
    print(ret)
    # return str(ret)
    return render_template('main/dxl2.html', ret2=ret[1])


#pymysql获得单条数据
@main_bp.route('/pymysql3', methods=['GET', 'POST'])
def pymysql3():

    # 连接database
    conn = pymysql.connect(host="192.168.10.22", port=9966, user="jusrrjd76hud",
                             passwd="MgBaIsOn20191022AbYz",
                             db="mg_e3")
    # 得到一个可以执行SQL语句的光标对象
    cursor = conn.cursor()
    # 查询数据的SQL语句
    sql = """SELECT COUNT(*) as yzrds,sum(case when `order_status`=1 then 1 else 0 end) as yskds,
		sum(case when `shipping_status`=3 then 1 else 0 end) as ytzphds,sum(case when `shipping_status`=7 then 1 else 0 end) as yfhds,
		sum(case when `is_write_back`=1 then 1 else 0 end) as yhxds,sum(case when `is_sync_to_wms` =1 then 1 else 0 end) as ytbwmsds
		FROM order_info WHERE lylx =1 AND is_combine_new=0 and is_split_new=0 AND is_shougong=0  AND is_copy=0 AND is_sh_ship=0
		AND FROM_UNIXTIME(add_time,'%Y-%m-%d %H:%i:%s') >= '2020-10-27 00:00:00' AND FROM_UNIXTIME(add_time,'%Y-%m-%d %H:%i:%s') <= '2020-10-28 00:00:00' ;"""
    # 执行SQL语句
    cursor.execute(sql)
    # 获取单条查询数据
    ret = cursor.fetchone()
    cursor.close()
    conn.close()
    # 打印下查询结果
    print(ret)
    # return str(ret)
    return render_template('main/dxl3.html', ret2=ret)


#pymysql获得多条数据
@main_bp.route('/pymysql2', methods=['GET', 'POST'])
def pymysql2():
    # 导入pymysql模块
    import pymysql
    # 连接database
    conn = pymysql.connect(host="192.168.10.22", port=9966, user="jusrrjd76hud",
                           passwd="MgBaIsOn20191022AbYz",
                           db="mg_e3")
    # 得到一个可以执行SQL语句的光标对象
    cursor = conn.cursor()
    # 查询数据的SQL语句
    sql = "SELECT khdm,khmc from kehu ;"
    # 执行SQL语句
    cursor.execute(sql)
    # 获取多条查询数据
    ret = cursor.fetchall()
    cursor.close()
    conn.close()
    # 打印下查询结果
    print(ret)
    return render_template('main/dxl2.html', ret2=ret)
    # return str(ret)

#pymysql获得多条数据
@main_bp.route('/pymysql4', methods=['GET', 'POST'])
def pymysql4():
    # 导入pymysql模块
    import pymysql
    # 连接database
    conn = pymysql.connect(host="192.168.10.22", port=9966, user="jusrrjd76hud",
                           passwd="MgBaIsOn20191022AbYz",
                           db="mg_e3")
    # 得到一个可以执行SQL语句的光标对象
    cursor = conn.cursor()
    # 查询数据的SQL语句
    sql = """select hh.*,h.khmc from (SELECT sd_id,COUNT(*) as yzrds,sum(case when `order_status`=1 then 1 else 0 end) as yskds,
		sum(case when `shipping_status`=3 then 1 else 0 end) as ytzphds,sum(case when `shipping_status`=7 then 1 else 0 end) as yfhds,
		sum(case when `is_write_back`=1 then 1 else 0 end) as yhxds,sum(case when `is_sync_to_wms` =1 then 1 else 0 end) as ytbwmsds
		FROM order_info WHERE 1 =1 AND is_combine_new=0 and is_split_new=0 AND is_shougong=0  AND is_copy=0 AND is_sh_ship=0  
		AND FROM_UNIXTIME(add_time,'%Y-%m-%d %H:%i:%s') >= '2020-11-01 00:00:00' AND FROM_UNIXTIME(add_time,'%Y-%m-%d %H:%i:%s') <= '2020-11-12 00:00:00'
		group by sd_id) hh ,kehu h where h.id=hh.sd_id order by 2 desc"""
    # 执行SQL语句
    cursor.execute(sql)
    # 获取多条查询数据
    ret = cursor.fetchall()
    cursor.close()
    conn.close()
    # 打印下查询结果
    print(ret)
    # 连接database
    conn = pymysql.connect(host="192.168.10.22", port=9966, user="jusrrjd76hud",
                           passwd="MgBaIsOn20191022AbYz",
                           db="mg_e3")
    # 得到一个可以执行SQL语句的光标对象
    cursor = conn.cursor()
    # 查询数据的SQL语句
    sql = """select sum(payment) dt from order_info where FROM_UNIXTIME(pay_time)>='2020-11-01 00:00:00'and FROM_UNIXTIME(pay_time)<='2020-11-11 23:59:59' and order_status!='3';"""
    # 执行SQL语句
    cursor.execute(sql)
    # 获取多条查询数据
    ret2 = cursor.fetchone()
    cursor.close()
    conn.close()
    # 打印下查询结果
    print(ret2)
    print(ret2[0])
    return render_template('main/dxl4.html', ret4=ret, ret2=ret2[0])
    # return str(ret)



@main_bp.route('/export_dxl', methods=['GET', 'POST'])
def export_dxl():
    wb = xlwt.Workbook()
    # 添加一个表
    ws = wb.add_sheet('Sheet1')

    # 3个参数分别为行号，列号，和内容
    # 需要注意的是行号和列号都是从0开始的
    ws.write(0, 0, 'No.')
    ws.write(0, 1, 'sku')
    ws.write(0, 2, '期初数量')
    ws.write(0, 3, '年')
    ws.write(0, 4, '月')
    ws.write(0, 5, '仓库')
    ws.write(0, 6, '期末数量')
    ws.write(0, 7, '销售数量')
    ws.write(0, 8, '滞销数量')
    ws.write(0, 9, '成本价')
    ws.write(0, 10, '动销率')
    ws.write(0, 11, '计算维度')
    form = DxlSearchForm()
    if form.validate_on_submit():
        if form.submit_excel.data:
            textsql = " 1=1 "
            if form.sku.data:
                textsql += " and sku='" + form.sku.data + "' "
            if form.weidu.data:
                textsql += " and weidu='" + form.weidu.data + "' "
            if form.hjyear.data:
                textsql += " and hjyear='" + form.hjyear.data + "' "
            if form.hjmn.data:
                textsql += " and hjmn='" + form.hjmn.data + "' "
            if form.ck_id.data:
                textsql += " and ck_id='" + form.ck_id.data + "' "
            dxls = Ab_jqx_dxl.query.filter(Ab_jqx_dxl.last != 0).filter(text(textsql)).order_by(
                Ab_jqx_dxl.id).all()
    else:
        dxls = Ab_jqx_dxl.query.all()
    print(dxls[0])
    i = 1
    for dxl in dxls:
        ws.write(i, 0, dxl.id)
        ws.write(i, 1, dxl.sku)
        ws.write(i, 2, dxl.qc)
        ws.write(i, 3, dxl.hjyear)
        ws.write(i, 4, dxl.hjmn)
        ws.write(i, 5, dxl.ck_id)
        ws.write(i, 6, dxl.qm)
        ws.write(i, 7, dxl.xs_s)
        ws.write(i, 8, dxl.last)
        ws.write(i, 9, dxl.cbj)
        ws.write(i, 10, dxl.dxl)
        ws.write(i, 11, dxl.weidu)
        i = i + 1

    # 保存excel文件
    wb.save('./uploads/export.xls')
    return render_template('main/export_excel.html')


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
        cache.clear()
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
    cache.clear()
    flash('Post deleted.', 'success')
    return redirect_back()


@main_bp.route('/owenum/<int:owe_id>/delete', methods=['POST'])
@login_required
def delete_owe(owe_id):
    owenum = Owenum.query.get_or_404(owe_id)
    db.session.delete(owenum)
    db.session.commit()
    flash('Owe deleted.', 'success')
    return redirect_back()


@main_bp.route('/postupload', methods=['POST'])
def upload_image():
    f = request.files.get('upload')
    if not allowed_file(f.filename):
        return upload_fail('Image only!')
    f.save(os.path.join(current_app.config['BLUELOG_UPLOAD_PATH'], f.filename))
    url = url_for('.get_image', filename=f.filename)
    return upload_success(url, f.filename)


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
