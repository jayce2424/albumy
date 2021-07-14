# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
import pymysql
from random import randrange

from flask import render_template, flash, redirect, url_for, Blueprint
from flask_login import login_user, logout_user, login_required, current_user, login_fresh, confirm_login

from albumy.emails import send_confirm_email, send_reset_password_email
from albumy.extensions import db
from albumy.forms.auth import LoginForm, RegisterForm, ForgetPasswordForm, ResetPasswordForm
from albumy.models import User, Xs
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
from pyecharts.charts import Line
from decimal import Decimal
import json
import redis

auth_bp = Blueprint('auth', __name__)

# redis 取出的结果默认是字节，我们可以设定 decode_responses=True 改成字符串。
pool = redis.ConnectionPool(host='10.10.19.6', port=6379, decode_responses=True)
r = redis.Redis(connection_pool=pool)


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


def bar_base10() -> Bar:
    c = (
        Pie()
            # .add("", [list(z) for z in zip(Faker.choose(), Faker.values())])
            # .add("", [('小米', 88), ('三星', 38), ('华为', 57), ('苹果', 102), ('魅族', 77), ('VIVO', 53),('OPPO', 105)])
            .add("", [('天猫', 88), ('京东', 80), ('新渠道', 16.8), ('分销', 355),])
            .set_colors(["blue", "green", "yellow", "red", "pink", "orange", "purple"])
            .set_global_opts(title_opts=opts.TitleOpts(title="Pie-设置颜色"))
            .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
        # .render("pie_set_color.html")
    )
    # print(c)  # 是个对象 看不出啥
    return c


@auth_bp.route("/ss")
def ss():
    for z in zip(Faker.choose(), Faker.values()):
        print(z)
        print(z[0])#列表 元组都能通过这种方式取数据
    a = [1, 2, 3]
    b = [4, 5, 6]
    zipped = zip(a, b) #[(1, 4), (2, 5), (3, 6)]
    print(zipped)
    return 'hh'


# Bar - Mixed_bar_and_line
def bar_base88() -> Bar:
    x_data = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]

    c = (
        # Bar()
        # Bar({"theme": ThemeType.MACARONS})  # 更换主题
        Bar(init_opts=opts.InitOpts(width="1600px", height="800px"))
            .add_xaxis(xaxis_data=x_data)
            .add_yaxis(
            series_name="蒸发量",
            # 由于版本更新的问题，方法的相关使用一直在变化，对y轴进行赋值最新版本不能用yaxis_data，要用y_axis
            y_axis=[
                2.0,
                4.9,
                7.0,
                23.2,
                25.6,
                76.7,
                135.6,
                162.2,
                32.6,
                20.0,
                6.4,
                3.3,
            ],
            label_opts=opts.LabelOpts(is_show=False),
        )
            .add_yaxis(
            series_name="降水量",
            # 由于版本更新的问题，方法的相关使用一直在变化，对y轴进行赋值最新版本不能用yaxis_data，要用y_axis
            y_axis=[
                2.6,
                5.9,
                9.0,
                26.4,
                28.7,
                70.7,
                175.6,
                182.2,
                48.7,
                18.8,
                6.0,
                2.3,
            ],
            label_opts=opts.LabelOpts(is_show=False),
        )
            .extend_axis(
            yaxis=opts.AxisOpts(
                name="温度",
                type_="value",
                min_=0,
                max_=25,
                interval=5,
                axislabel_opts=opts.LabelOpts(formatter="{value} °C"),
            )
        )
            .set_global_opts(
            tooltip_opts=opts.TooltipOpts(
                is_show=True, trigger="axis", axis_pointer_type="cross"
            ),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                axispointer_opts=opts.AxisPointerOpts(is_show=True, type_="shadow"),
            ),
            yaxis_opts=opts.AxisOpts(
                name="水量",
                type_="value",
                min_=0,
                max_=250,
                interval=50,
                axislabel_opts=opts.LabelOpts(formatter="{value} ml"),
                axistick_opts=opts.AxisTickOpts(is_show=True),
                splitline_opts=opts.SplitLineOpts(is_show=True),
            ),
        )
    )

    line = (
        Line()
            .add_xaxis(xaxis_data=x_data)
            .add_yaxis(
            series_name="平均温度",
            yaxis_index=1,
            y_axis=[2.0, 2.2, 3.3, 4.5, 6.3, 10.2, 20.3, 23.4, 23.0, 16.5, 12.0, 6.2],
            # label_opts=opts.LabelOpts(is_show=False),
        )
    )
    # .render("bar_waterfall_plot.html")
    # bar.overlap(line).render("mixed_bar_and_line.html")
    c.overlap(line)  # 关键：柱状图叠加到线行图
    return c


# Bar - Mixed_bar_and_line
def bar_base89() -> Bar:
    x_data = ["天猫生活馆", "天猫旗舰店", "天猫小计", "办公", "非办公", "京东小计", "京东前台", "POP", "拼多多", "抖音", "批发", "新渠道小计", "直营小计", "分销小计",
              "总计"]

    c = (
        # Bar()
        # Bar({"theme": ThemeType.MACARONS})  # 更换主题
        Bar(init_opts=opts.InitOpts(width="1600px", height="800px"))
            .add_xaxis(xaxis_data=x_data)
            .add_yaxis(
            series_name="当日目标",
            # 由于版本更新的问题，方法的相关使用一直在变化，对y轴进行赋值最新版本不能用yaxis_data，要用y_axis
            y_axis=[
                7,
                82,
                89,
                0,
                0,
                0,
                400,
                1,
                3,
                16,
                1,
                17,
                110,
                355,
                465,
            ],
            label_opts=opts.LabelOpts(is_show=False),
        )
            .add_yaxis(
            series_name="当日销售",
            # 由于版本更新的问题，方法的相关使用一直在变化，对y轴进行赋值最新版本不能用yaxis_data，要用y_axis
            y_axis=[
                7.25,
                81.34,
                88.59,
                54.88,
                25.45,
                80.34,
                323.95,
                1.25,
                0.62,
                16.78,
                0.02,
                16.80,
                187.6,
                423.44,
                611.03
            ],
            label_opts=opts.LabelOpts(is_show=False),
        )
            .extend_axis(
            yaxis=opts.AxisOpts(
                name="温度",
                type_="value",
                min_=0,
                max_=180,
                interval=5,
                axislabel_opts=opts.LabelOpts(formatter="{value} %"),
            )
        )
            .set_global_opts(
            tooltip_opts=opts.TooltipOpts(
                is_show=True, trigger="axis", axis_pointer_type="cross"
            ),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                axispointer_opts=opts.AxisPointerOpts(is_show=True, type_="shadow"),
            ),
            yaxis_opts=opts.AxisOpts(
                name="销售金额",
                type_="value",
                min_=0,
                max_=700,
                interval=50,
                axislabel_opts=opts.LabelOpts(formatter="{value} 万"),
                axistick_opts=opts.AxisTickOpts(is_show=True),
                splitline_opts=opts.SplitLineOpts(is_show=True),
            ),
        )
    )

    line = (
        Line()
            .add_xaxis(xaxis_data=x_data)
            .add_yaxis(
            series_name="日完成率",
            yaxis_index=1,
            y_axis=[112, 99, 100, 100, 100, 100, 81, 86, 18, 105, 2, 99, 170, 119, 131],
            # label_opts=opts.LabelOpts(is_show=False),
        )
    )
    # .render("bar_waterfall_plot.html")
    # bar.overlap(line).render("mixed_bar_and_line.html")
    c.overlap(line)  # 关键：柱状图叠加到线行图
    return c


def bar_base3() -> Bar:
    c = (
        Bar()
            .add_xaxis(Faker.choose())
            .add_yaxis("商家A", Faker.values(), stack="stack1")
            .add_yaxis("商家B", Faker.values(), stack="stack1")
            .add_yaxis("商家C", Faker.values(), stack="stack1")
            .add_yaxis("商家D", Faker.values(), stack="stack1")
            .add_yaxis("商家E", [106, -93, 121, 126, -76, 124, -140], stack="stack1")
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
            .set_global_opts(title_opts=opts.TitleOpts(title="Bar-堆叠数据（全部）"))
    )
    return c

# 就是很奇怪 有时间报错 Python OSError: [Errno 22] Invalid argument:
@auth_bp.route('/ssddhg')
def ssddhg():
    # c = Faker.values()
    g = Faker.choose()
    # print(c[0])
    print(type(g))
    # print(c)
    # print(g)
    return 'gg'



def bar_base11() -> Bar:
    # 这部分为我们的各个品牌的标签(名字随意弄的，不要见怪)
    label = ['孙悟空模型', '猪八戒模型', '沙和尚模型', '鲤鱼精模型', '花仙子模型', '土地公公模型', '车迟国王模型', '黑熊精模型']
    # 因为一个品牌标签对应有多个数值分析,所以每个数值给出一组数据列表
    mean_kh = [457.77, 258, 269, 147.5, 440.71, 302.8, 129, 313.63]
    max_kh = [1286, 258, 313, 156, 490, 345, 129, 339]
    min_kh = [259, 258, 225, 139, 429, 278, 129, 310]
    c = (

        Bar()
        .add_xaxis(label)
        .add_yaxis('平均价位', mean_kh)
        .add_yaxis('最高价位', max_kh)
        .add_yaxis('最低价位', min_kh)
        .reversal_axis()
        .set_series_opts(label_opts=opts.LabelOpts(position="right"))
        # .set_global_opts(title_opts=opts.TitleOpts(title="西游记娃娃价位对比"))
    )
    return c


def bar_base5() -> Bar:
    # # 连接database
    # conn = pymysql.connect(host="192.168.10.206", port=3306, user="root",
    #                          passwd="baison8888",
    #                          db="e3_20192020")
    # # 得到一个可以执行SQL语句的光标对象
    # cursor = conn.cursor()
    # # 查询数据的SQL语句
    # sql = """select sum(payment) dt from order_info where FROM_UNIXTIME(pay_time)>='2020-11-01 00:00:00'and FROM_UNIXTIME(pay_time)<='2020-11-13 23:59:59' and order_status!='3';"""
    # # 执行SQL语句
    # cursor.execute(sql)
    # # 获取多条查询数据
    # ret = cursor.fetchone()
    # cursor.close()
    # conn.close()
    # 打印下查询结果
    # print(ret)
    # print(ret[0])
    ll8 = 19288624.14
    gg = Decimal(ll8) / Decimal(280000000)
    c = (
        Liquid()
            .add("lq", [gg, 0.2])
            .set_global_opts(title_opts=opts.TitleOpts(title="已完成目标2.8亿的:"))
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


# 下面的两个是前后端分离的做法 写了两个链接 其中一个是空的 牛逼
@auth_bp.route("/ssddjj")
def indexssddjj():
    return render_template("auth/ssddjj.html")


def bar_basejjs_old() -> Bar:
    try:
        db = pymysql.connect(host="10.10.19.6", port=5000, user="root",
                             passwd="qwer1234.",
                             db="flask_albumy2")
    except:
        print("could not connect to mysql server")
    cursor = db.cursor()

    sql = "select * from xs order by 1 limit 1000;"
    cursor.execute(sql)  # 执行sql语句
    ret = cursor.fetchall()
    listd = []
    listxl = []
    for row in ret:
        listd.append(row[0])
        listxl.append(row[1])
    print(listd)
    c = (
        Bar()
            # .add_xaxis(["衬衫64", "羊毛衫3", "雪纺衫5", "裤子", "高跟鞋", "袜子"])
            .add_xaxis(listd)
            # .add_yaxis("商家A", [1,2,3,4,5,6,7,8,9,10])
            .add_yaxis("商家A", listxl)
            # .add_yaxis("商家B", [randrange(0, 100) for _ in range(6)])
            .set_global_opts(title_opts=opts.TitleOpts(title="Bar-基本示例", subtitle="我是副标题"))
    )
    return c


def bar_basejjs() -> Bar:
    xss = Xs.query.order_by(Xs.date).all()
    # print(xs)
    # exit()
    listd = []
    listxl = []
    for xs in xss:
        listd.append(xs.date)
        listxl.append(xs.sl)
    print(listd)
    c = (
        Bar()
            # .add_xaxis(["衬衫64", "羊毛衫3", "雪纺衫5", "裤子", "高跟鞋", "袜子"])
            .add_xaxis(listd)
            # .add_yaxis("商家A", [1,2,3,4,5,6,7,8,9,10])
            .add_yaxis("E3单日发货量", listxl, label_opts=opts.LabelOpts(is_show=False))
            # .add_yaxis("商家B", [randrange(0, 100) for _ in range(6)])
            .set_global_opts(title_opts=opts.TitleOpts(title="Bar-基本示例", subtitle="我是副标题"),
                             datazoom_opts=[opts.DataZoomOpts(), opts.DataZoomOpts(type_="inside")], )
    )
    return c


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
            .add("lq", [0.2], is_outline_show=False, shape=SymbolType.DIAMOND)
            .set_global_opts(title_opts=opts.TitleOpts(title="Liquid-Shape-Diamond"))
    )
    return c


def bar_basejjjh() -> Bar:
    # ff=Faker.choose()
    # print(ff)
    try:
        db = pymysql.connect(host="192.168.10.206", port=3306, user="root",
                             passwd="baison8888",
                             db="e3_20192020")
    except:
        print("could not connect to mysql server")
    cursor = db.cursor()

    sql = """select substring(FROM_UNIXTIME(trans_time),12,2) as DT, COUNT(*) as count 
from order_info where left(FROM_UNIXTIME(trans_time),10)>='2019-11-11'
and left(FROM_UNIXTIME(trans_time),10)<'2019-11-12' and sd_id in (3,117,187) and order_status!=3
group by substring(FROM_UNIXTIME(trans_time),12,2) order by DT ;"""
    cursor.execute(sql)  # 执行sql语句
    ret = cursor.fetchall()
    listd = []
    listxl = []
    for row in ret:
        listd.append(row[0])
        listxl.append(row[1])
    print(listd)
    print(listxl)
    cursor.close()
    db.close()

    try:
        db = pymysql.connect(host="192.168.10.206", port=3306, user="root",
                             passwd="baison8888",
                             db="e3_20192020")
    except:
        print("could not connect to mysql server")
    cursor = db.cursor()

    sql = """select substring(FROM_UNIXTIME(trans_time),12,2) as DT, COUNT(*) as count 
    from order_info where left(FROM_UNIXTIME(trans_time),10)>='2020-11-11'
    and left(FROM_UNIXTIME(trans_time),10)<'2020-11-12' and sd_id in (3,117,187) and order_status!=3
    group by substring(FROM_UNIXTIME(trans_time),12,2) order by DT ;"""
    cursor.execute(sql)  # 执行sql语句
    ret = cursor.fetchall()
    # listd = []
    listxl2 = []
    for row in ret:
        # listd.append(row[0])
        listxl2.append(row[1])
    print(listxl2)
    cursor.close()
    db.close()

    c = (
        Line()
            .add_xaxis(listd)
            .add_yaxis("19年", listxl, is_smooth=True)
            .add_yaxis("20年", listxl2, is_smooth=True)
            .set_series_opts(
            areastyle_opts=opts.AreaStyleOpts(opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
            .set_global_opts(
            title_opts=opts.TitleOpts(title="E3历年淘系进单速率对比"),
            xaxis_opts=opts.AxisOpts(
                axistick_opts=opts.AxisTickOpts(is_align_with_label=True),
                is_scale=False,
                boundary_gap=False,
            ),
        )
        # .render("line_areastyle_boundary_gap.html")
    )
    return c


@auth_bp.route("/barChart")
def get_bar_chart():
    c = bar_basejjs()
    return c.dump_options_with_quotes()


@auth_bp.route("/barChart2")
def get_bar_chart2():
    c = bar_basejj()
    return c.dump_options_with_quotes()


@auth_bp.route("/barChartjjj")
def get_bar_chartjjj():
    c = bar_base5()
    return c.dump_options_with_quotes()


@auth_bp.route("/barChartjjjh")
def get_bar_chartjjjh():
    c = bar_basejjjh()
    return c.dump_options_with_quotes()


# 两个合并在一块 http://127.0.0.1:5010/auth/ssdd3
@auth_bp.route("/ssdd3")
def indexssdd3():
    c11 = bar_base11()
    c10 = bar_base10()
    c = bar_base()
    c2 = bar_base2()
    c3 = bar_base3()
    c4 = bar_base4()
    c5 = bar_base5()
    c6 = bar_base6()
    c7 = bar_base7()
    c8 = bar_base88()
    c9 = bar_base89()
    return Markup(
        c11.render_embed()+c10.render_embed() + c8.render_embed() + c9.render_embed() + c.render_embed() + c2.render_embed() + c3.render_embed() + c4.render_embed() + c5.render_embed() + c6.render_embed() + c7.render_embed())


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


@auth_bp.route("/redis_find")
def redis_find():
    r.set('foo', 'bar')
    print(r.get('foo'))
    print(r.get('food'))
    print(r.get('fruit'))
    print(r['foo'])
    print(type(r['foo']))
    return 'testing'


@auth_bp.route("/redis_set")
def redis_set():
    """
    # r.set('foo', 'bar')
    r.set('food', 'mutton', ex=3)  # ex过期时间（秒） 键food的值就变成None
    r.setex("fruit2", 5, "orange")  # 同上

    r.set('food', 'mutton', px=3)  # px - 过期时间（毫秒） 键food的值就变成None
    r.psetex("fruit3", 5000, "apple")  # 同上

    print(r.set('fruit', 'watermelon', nx=True))  #只有name不存在时，当前set操作才执行（新建）
    print(r.setnx('fruit1', 'banana'))  # 同上
    print(r.set('fruit', 'watermelon2', xx=True))  #只有name存在时，当前set操作才执行 （修改）

    # 批量设置值
    # r.mget({'k1': 'v1', 'k2': 'v2'})
    r.mset(k1="v1", k2="v2")
    print(r.mget("foo", "fruit"))
    print(r.mget('k1', 'k2'))
    print(r.mget(['foo', 'fruit']))
    # print(r.mget({'k1': 'v1', 'k2': 'v2'}))
"""
    r.set("cn_name", "君惜大大")  # 汉字
    print(r.getrange("cn_name", 0, 2))  # 取索引号是0-2 前3位的字节 君 切片操作 （一个汉字3个字节 1个字母一个字节 每个字节8bit）
    print(r.getrange("cn_name", 0, -1))  # 取所有的字节 君惜大大 切片操作
    r.set("en_name", "junxi")  # 字母
    print(r.getrange("en_name", 0, 2))  # 取索引号是0-2 前3位的字节 jun 切片操作 （一个汉字3个字节 1个字母一个字节 每个字节8bit）
    print(r.getrange("en_name", 0, -1))  # 取所有的字节 junxi 切片操作

    return 'seting'
