from flask import Flask  # 需自行下载Flask包，并导入这几个内容
from flask import jsonify
from flask import request
from mysql import mysql_operate

app = Flask(__name__)


# 初始化生成一个app对象，这个对 象就是Flask的当前实例对象，后面的各个方法调用都是这个实例
# Flask会进行一系列自己的初始化，比如web API路径初始化，web资源加载，日志模块创建等。然后返回这个创建好的对象给你


@app.route("/")  # 自定义路径
def index():
    return 'Hello World!'


def getCompany(comId):
    """获取所有用户信息"""
    # 查询公司是否存在
    sql = "select * from company where id =" + comId
    return mysql_operate.db.select_db(sql)  # 用mysql_operate文件中的db的select_db方法进行查询


def insert(company):
    """插入信息"""
    if getCompany(company.id):  # 判断是否有返回数据，如果有则表示已经存在
        return '已收藏'
    else:  # 如果没有，则插入新数据
        sql1 = "insert into company (id,name) values('" + company.id + "','" + company.name + "');"
        mysql_operate.db.execute_db(sql1)
        return '收藏成功'


@app.route("/delete", methods=["GET", "POST"])  #
def delete():
    """删除信息"""
    id = str(request.args.get('id'))
    sql = "SELECT * FROM favorites WHERE id =" + id
    data = mysql_operate.db.select_db(sql)
    if data:
        sql1 = "DELETE FROM favorites WHERE id =" + id
        mysql_operate.db.execute_db(sql1)
        return '删除成功'
    else:
        return '不存在此id'


if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8888)  #
# flask默认是没有开启debug模式的，开启debug模式，可以帮助我们查找代码里面的错误
# host = '127.0.0.1' 表示设置的ip，如果需要连接手机等设备，可以将手机和电脑连接同一个热点，将host设置成对应的ip
# port 为端口号，可自行设置
