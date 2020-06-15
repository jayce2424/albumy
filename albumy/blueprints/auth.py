# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from random import randrange

from flask import render_template, flash, redirect, url_for, Blueprint
from flask_login import login_user, logout_user, login_required, current_user, login_fresh, confirm_login

from albumy.emails import send_confirm_email, send_reset_password_email
from albumy.extensions import db
from albumy.forms.auth import LoginForm, RegisterForm, ForgetPasswordForm, ResetPasswordForm
from albumy.models import User
from albumy.settings import Operations
from albumy.utils import generate_token, validate_token, redirect_back
from pyecharts.globals import CurrentConfig
# 关于 CurrentConfig，可参考 [基本使用-全局变量]
# CurrentConfig.GLOBAL_ENV = Environment(loader=FileSystemLoader("./templates"))
from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType
from jinja2 import Markup, Environment, FileSystemLoader
from pyecharts.faker import Faker
from pyecharts.charts import Liquid
from pyecharts.globals import SymbolType
from pyecharts.charts import Pie
from pyecharts.charts import WordCloud
import json

auth_bp = Blueprint('auth', __name__)


def bar_base() -> Bar:
    c = (
        # Bar()
        Bar({"theme": ThemeType.MACARONS})  # 更换主题
            .add_xaxis(["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"])
            .add_yaxis("商家A", [5, 20, 36, 10, 75, 90])
            .add_yaxis("商家B", [15, 25, 16, 55, 48, 8])
            .set_global_opts(title_opts=opts.TitleOpts(title="Bar_rotate_xaxis_label", subtitle="我是副标题"))
    )
    return c


def bar_base3() -> Bar:
    c = (
        Bar()
            .add_xaxis(Faker.choose())
            .add_yaxis("商家A", Faker.values(), stack="stack1")
            .add_yaxis("商家B", Faker.values(), stack="stack1")
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
            .set_global_opts(title_opts=opts.TitleOpts(title="Bar-堆叠数据（全部）"))
    )
    return c


def bar_base5() -> Bar:
    c = (
        Liquid()
            .add("lq", [0.6, 0.7])
            .set_global_opts(title_opts=opts.TitleOpts(title="Liquid-基本示例"))
    )
    return c


def bar_base7() -> Bar:
    data = [
        ("生活资源", "999"),
        ("供热管理", "888"),
        ("供气质量", "777"),
        ("生活用水管理", "688"),
        ("一次供水问题", "588"),
        ("交通运输", "516"),
        ("城市交通", "515"),
        ("环境保护", "483"),
        ("房地产管理", "462"),
        ("城乡建设", "449"),
        ("社会保障与福利", "429"),
        ("社会保障", "407"),
        ("文体与教育管理", "406"),
        ("公共安全", "406"),
        ("公交运输管理", "386"),
        ("出租车运营管理", "385"),
        ("供热管理", "375"),
        ("市容环卫", "355"),
        ("自然资源管理", "355"),
        ("粉尘污染", "335"),
        ("噪声污染", "324"),
        ("土地资源管理", "304"),
        ("物业服务与管理", "304"),
        ("医疗卫生", "284"),
        ("粉煤灰污染", "284"),
        ("占道", "284"),
        ("供热发展", "254"),
        ("农村土地规划管理", "254"),
        ("生活噪音", "253"),
        ("供热单位影响", "253"),
        ("城市供电", "223"),
        ("房屋质量与安全", "223"),
        ("大气污染", "223"),
        ("房屋安全", "223"),
        ("文化活动", "223"),
        ("拆迁管理", "223"),
        ("公共设施", "223"),
        ("供气质量", "223"),
        ("供电管理", "223"),
        ("燃气管理", "152"),
        ("教育管理", "152"),
        ("医疗纠纷", "152"),
        ("执法监督", "152"),
        ("设备安全", "152"),
        ("政务建设", "152"),
        ("县区、开发区", "152"),
        ("宏观经济", "152"),
        ("教育管理", "112"),
        ("社会保障", "112"),
        ("生活用水管理", "112"),
        ("物业服务与管理", "112"),
        ("分类列表", "112"),
        ("农业生产", "112"),
        ("二次供水问题", "112"),
        ("城市公共设施", "92"),
        ("拆迁政策咨询", "92"),
        ("物业服务", "92"),
        ("物业管理", "92"),
        ("社会保障保险管理", "92"),
        ("低保管理", "92"),
        ("文娱市场管理", "72"),
        ("城市交通秩序管理", "72"),
        ("执法争议", "72"),
        ("商业烟尘污染", "72"),
        ("占道堆放", "71"),
        ("地上设施", "71"),
        ("水质", "71"),
        ("无水", "71"),
        ("供热单位影响", "71"),
        ("人行道管理", "71"),
        ("主网原因", "71"),
        ("集中供热", "71"),
        ("客运管理", "71"),
        ("国有公交（大巴）管理", "71"),
        ("工业粉尘污染", "71"),
        ("治安案件", "71"),
        ("压力容器安全", "71"),
        ("身份证管理", "71"),
        ("群众健身", "41"),
        ("工业排放污染", "41"),
        ("破坏森林资源", "41"),
        ("市场收费", "41"),
        ("生产资金", "41"),
        ("生产噪声", "41"),
        ("农村低保", "41"),
        ("劳动争议", "41"),
        ("劳动合同争议", "41"),
        ("劳动报酬与福利", "41"),
        ("医疗事故", "21"),
        ("停供", "21"),
        ("基础教育", "21"),
        ("职业教育", "21"),
        ("物业资质管理", "21"),
        ("拆迁补偿", "21"),
        ("设施维护", "21"),
        ("市场外溢", "11"),
        ("占道经营", "11"),
        ("树木管理", "11"),
        ("农村基础设施", "11"),
        ("无水", "11"),
        ("供气质量", "11"),
        ("停气", "11"),
        ("市政府工作部门（含部门管理机构、直属单位）", "11"),
        ("燃气管理", "11"),
        ("市容环卫", "11"),
        ("新闻传媒", "11"),
        ("人才招聘", "11"),
        ("市场环境", "11"),
        ("行政事业收费", "11"),
        ("食品安全与卫生", "11"),
        ("城市交通", "11"),
        ("房地产开发", "11"),
        ("房屋配套问题", "11"),
        ("物业服务", "11"),
        ("物业管理", "11"),
        ("占道", "11"),
        ("园林绿化", "11"),
        ("户籍管理及身份证", "11"),
        ("公交运输管理", "11"),
        ("公路（水路）交通", "11"),
        ("房屋与图纸不符", "11"),
        ("有线电视", "11"),
        ("社会治安", "11"),
        ("林业资源", "11"),
        ("其他行政事业收费", "11"),
        ("经营性收费", "11"),
        ("食品安全与卫生", "11"),
        ("体育活动", "11"),
        ("有线电视安装及调试维护", "11"),
        ("低保管理", "11"),
        ("劳动争议", "11"),
        ("社会福利及事务", "11"),
        ("一次供水问题", "11"),
    ]

    c = (WordCloud()
        .add(series_name="热点分析", data_pair=data, word_size_range=[6, 66])
        .set_global_opts(
        title_opts=opts.TitleOpts(
            title="热点分析", title_textstyle_opts=opts.TextStyleOpts(font_size=23)
        ),
        tooltip_opts=opts.TooltipOpts(is_show=True),
    )

    )
    return c


def bar_base6() -> Bar:
    x_data = ["直接访问", "邮件营销", "联盟广告", "视频广告", "搜索引擎"]
    y_data = [335, 310, 274, 235, 400]
    data_pair = [list(z) for z in zip(x_data, y_data)]
    data_pair.sort(key=lambda x: x[1])
    c = (
        Pie(init_opts=opts.InitOpts(width="1600px", height="800px", bg_color="#2c343c"))
            .add(
            series_name="访问来源",
            data_pair=data_pair,
            rosetype="radius",
            radius="55%",
            center=["50%", "50%"],
            label_opts=opts.LabelOpts(is_show=False, position="center"),
        )
            .set_global_opts(
            title_opts=opts.TitleOpts(
                title="Customized Pie",
                pos_left="center",
                pos_top="20",
                title_textstyle_opts=opts.TextStyleOpts(color="#fff"),
            ),
            legend_opts=opts.LegendOpts(is_show=False),
        )
            .set_series_opts(
            tooltip_opts=opts.TooltipOpts(
                trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)"
            ),
            label_opts=opts.LabelOpts(color="rgba(255, 255, 255, 0.3)"),
        )
    )
    return c


def bar_base4() -> Bar:
    c = (
        Bar()
            .add_xaxis(Faker.choose())
            .add_yaxis("商家A", Faker.values())
            .add_yaxis("商家B", Faker.values())
            .set_global_opts(
            title_opts=opts.TitleOpts(title="Bar-Graphic 组件示例"),
            graphic_opts=[
                opts.GraphicGroup(
                    graphic_item=opts.GraphicItem(
                        rotation=JsCode("Math.PI / 4"),
                        bounding="raw",
                        right=110,
                        bottom=110,
                        z=100,
                    ),
                    children=[
                        opts.GraphicRect(
                            graphic_item=opts.GraphicItem(
                                left="center", top="center", z=100
                            ),
                            graphic_shape_opts=opts.GraphicShapeOpts(width=400, height=50),
                            graphic_basicstyle_opts=opts.GraphicBasicStyleOpts(
                                fill="rgba(0,0,0,0.3)"
                            ),
                        ),
                        opts.GraphicText(
                            graphic_item=opts.GraphicItem(
                                left="center", top="center", z=100
                            ),
                            graphic_textstyle_opts=opts.GraphicTextStyleOpts(
                                text="pyecharts bar chart",
                                font="bold 26px Microsoft YaHei",
                                graphic_basicstyle_opts=opts.GraphicBasicStyleOpts(
                                    fill="#fff"
                                ),
                            ),
                        ),
                    ],
                )
            ],
        )
    )
    return c


def bar_base2() -> Bar:
    list2 = [
        {"value": 12, "percent": 12 / (12 + 3)},
        {"value": 23, "percent": 23 / (23 + 21)},
        {"value": 33, "percent": 33 / (33 + 5)},
        {"value": 3, "percent": 3 / (3 + 52)},
        {"value": 33, "percent": 33 / (33 + 43)},
    ]

    list3 = [
        {"value": 3, "percent": 3 / (12 + 3)},
        {"value": 21, "percent": 21 / (23 + 21)},
        {"value": 5, "percent": 5 / (33 + 5)},
        {"value": 52, "percent": 52 / (3 + 52)},
        {"value": 43, "percent": 43 / (33 + 43)},
    ]

    c = (
        Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT))
            .add_xaxis([1, 2, 3, 4, 5])
            .add_yaxis("product1", list2, stack="stack1", category_gap="50%")
            .add_yaxis("product2", list3, stack="stack1", category_gap="50%")
            .set_global_opts(title_opts=opts.TitleOpts(title="Stack_bar_percent", subtitle="我是副标题"))
            .set_series_opts(
            label_opts=opts.LabelOpts(
                position="right",
                formatter=JsCode(
                    "function(x){return Number(x.data.percent * 100).toFixed() + '%';}"
                ),
            )
        )
    )
    return c


# echart 但是某个js挂了 用不了
@auth_bp.route("/ssdd")
def indexssdd():
    c = bar_base()
    return Markup(c.render_embed())
    # return render_template('auth/login.html', form=form)


@auth_bp.route("/ssdd2")
def indexssdd2():
    c = bar_base5()
    return Markup(c.render_embed())


# 下面的两个是前后端分离的做法 写了两个链接 其中一个是空的
@auth_bp.route("/ssddjj")
def indexssddjj():
    return render_template("auth/ssddjj.html")


def bar_basejj() -> Bar:
    c = (
        Bar()
            .add_xaxis(["衬衫64", "羊毛衫3", "雪纺衫5", "裤子", "高跟鞋", "袜子"])
            .add_yaxis("商家A", [randrange(0, 100) for _ in range(6)])
            .add_yaxis("商家B", [randrange(0, 100) for _ in range(6)])
            .set_global_opts(title_opts=opts.TitleOpts(title="Bar-基本示例", subtitle="我是副标题"))
    )
    return c

def bar_basejjj() -> Bar:
    c = (
        Liquid()
            .add("lq", [0.3, 0.7], is_outline_show=False, shape=SymbolType.DIAMOND)
            .set_global_opts(title_opts=opts.TitleOpts(title="Liquid-Shape-Diamond"))
    )
    return c


@auth_bp.route("/barChart")
def get_bar_chart():
    c = bar_basejj()
    return c.dump_options_with_quotes()


@auth_bp.route("/barChartjjj")
def get_bar_chartjjj():
    c = bar_base5()
    return c.dump_options_with_quotes()


# 两个合并在一块 http://127.0.0.1:5010/auth/ssdd3
@auth_bp.route("/ssdd3")
def indexssdd3():
    c = bar_base()
    c2 = bar_base2()
    c3 = bar_base3()
    c4 = bar_base4()
    c5 = bar_base5()
    c6 = bar_base6()
    c7 = bar_base7()
    return Markup(
        c.render_embed() + c2.render_embed() + c3.render_embed() + c4.render_embed() + c5.render_embed() + c6.render_embed() + c7.render_embed())


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.validate_password(form.password.data):
            if login_user(user, form.remember_me.data):
                flash('Login success.', 'info')
                return redirect_back()
            else:
                flash('Your account is blocked.', 'warning')
                return redirect(url_for('main.index'))
        flash('Invalid email or password.', 'warning')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/re-authenticate', methods=['GET', 'POST'])
@login_required
def re_authenticate():
    if login_fresh():
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit() and current_user.validate_password(form.password.data):
        confirm_login()
        return redirect_back()
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout success.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data.lower()
        username = form.username.data
        password = form.password.data
        user = User(name=name, email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        token = generate_token(user=user, operation='confirm')
        send_confirm_email(user=user, token=token)
        flash('Confirm email sent, check your inbox.', 'info')
        return redirect(url_for('.login'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))

    if validate_token(user=current_user, token=token, operation=Operations.CONFIRM):
        flash('Account confirmed.', 'success')
        return redirect(url_for('main.index'))
    else:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('.resend_confirm_email'))


@auth_bp.route('/resend-confirm-email')
@login_required
def resend_confirm_email():
    if current_user.confirmed:
        return redirect(url_for('main.index'))

    token = generate_token(user=current_user, operation=Operations.CONFIRM)
    send_confirm_email(user=current_user, token=token)
    flash('New email sent, check your inbox.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/forget-password', methods=['GET', 'POST'])
def forget_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = ForgetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = generate_token(user=user, operation=Operations.RESET_PASSWORD)
            send_reset_password_email(user=user, token=token)
            flash('Password reset email sent, check your inbox.', 'info')
            return redirect(url_for('.login'))
        flash('Invalid email.', 'warning')
        return redirect(url_for('.forget_password'))
    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None:
            return redirect(url_for('main.index'))
        if validate_token(user=user, token=token, operation=Operations.RESET_PASSWORD,
                          new_password=form.password.data):
            flash('Password updated.', 'success')
            return redirect(url_for('.login'))
        else:
            flash('Invalid or expired link.', 'danger')
            return redirect(url_for('.forget_password'))
    return render_template('auth/reset_password.html', form=form)
