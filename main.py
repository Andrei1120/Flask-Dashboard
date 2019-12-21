from flask import Flask, render_template, flash, redirect, session
from flask import request, jsonify
from forms import SubmitForm, LoginForm
from flask_mysqldb import MySQL
import os
import datetime

app = Flask(__name__,
            static_url_path='', 
            static_folder='static')

app.config['SECRET_KEY'] = os.urandom(32)

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'sqladmin'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_DB'] = 'dashboard'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


def register_ip():
    cur = mysql.connection.cursor()
    now = datetime.datetime.now()
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)    
    curdate_s = now.strftime("%Y-%m-%d 00:00:00")
    curdate_e = now.strftime("%Y-%m-%d 23:59:59")
    print('ip=%s, start=%s, end=%s' % (ip, curdate_s, curdate_e))
    cur.execute(''' SELECT ip FROM visitlog WHERE ip='%s' AND vdate>='%s' AND vdate<='%s' ''' % (ip, curdate_s, curdate_e))
    results = cur.fetchall()
    if len(results) == 0:
        cur.execute('''INSERT INTO visitlog (ip) VALUES ('%s')''' % ip)
        mysql.connection.commit()

def get_visitcount():
    cur = mysql.connection.cursor()
    now = datetime.datetime.now()
    curyear_s = now.strftime("%Y-01-01 00:00:00")
    curyear_e = now.strftime("%Y-12-31 23:59:59")
    curmonth_s = now.strftime("%Y-%m-01 00:00:00")
    curmonth_e = now.strftime("%Y-%m-31 23:59:59")
    curdate_s = now.strftime("%Y-%m-%d 00:00:00")
    curdate_e = now.strftime("%Y-%m-%d 23:59:59")
    cur.execute(''' SELECT ip FROM visitlog WHERE vdate>='%s' AND vdate<='%s' ''' % (curyear_s, curyear_e))
    yearcount = len(cur.fetchall())
    cur.execute(''' SELECT ip FROM visitlog WHERE vdate>='%s' AND vdate<='%s' ''' % (curmonth_s, curmonth_e))
    monthcount = len(cur.fetchall())
    cur.execute(''' SELECT ip FROM visitlog WHERE vdate>='%s' AND vdate<='%s' ''' % (curdate_s, curdate_e))
    daycount = len(cur.fetchall())
    return ('%s:%s:%s' % (yearcount, monthcount, daycount))


@app.route('/sell', methods=['GET', 'POST'])
def sell():
    register_ip()

    form = SubmitForm()
    if form.validate_on_submit():
        cur = mysql.connection.cursor()
        name = form.name.data
        address = form.address.data
        email = form.email.data
        phone = form.phone.data
        cur.execute('''SELECT email FROM info WHERE email='%s' ''' % email)
        results = cur.fetchall()
        if len(results) > 0:
            flash('Same email already exists!')
            return redirect('/sell')
        else:
            cur.execute('''INSERT INTO info VALUES ('%s', '%s', '%s', '%s', 'seller')''' % (email, name, address, phone))
            mysql.connection.commit()
            flash('Success!')
            return redirect('/sell')
    return render_template('sell.html', form=form, action='sell')

@app.route('/buy', methods=['GET', 'POST'])
def buy():
    register_ip()
    
    form = SubmitForm()
    if form.validate_on_submit():
        cur = mysql.connection.cursor()
        name = form.name.data
        address = form.address.data
        email = form.email.data
        phone = form.phone.data
        cur.execute('''SELECT email FROM info WHERE email='%s' ''' % email)
        results = cur.fetchall()
        if len(results) > 0:
            flash('Same email already exists!')
            return redirect('/buy')
        else:
            cur.execute('''INSERT INTO info VALUES ('%s', '%s', '%s', '%s', 'buyer')''' % (email, name, address, phone))
            mysql.connection.commit()
            flash('Success!')
            return redirect('/buy')
    return render_template('buy.html', form=form, action='buy')

@app.route('/admin')
def admin():
    if not session.get("logined") is None:
        cur = mysql.connection.cursor()
        cur.execute('''SELECT * FROM info''')
        results = cur.fetchall()
        index = 1
        ids, names, addresses, emails, phones, types = [], [], [], [], [], []
        for result in results:
            ids.append(index)
            names.append(result['name'])
            addresses.append(result['address'])
            emails.append(result['email'])
            phones.append(result['phone'])
            types.append(result['type'])
            index += 1
        datas = [{'id':id, 'name':name, 'address':address, 'email':email, 'phone':phone, 'type':type} for id, name, address, email, phone, type in zip(ids, names, addresses, emails, phones, types)]
        # datas = [{'id':'1', 'name':'a', 'address':'aaa', 'email':'a@a.com', 'phone':'123', 'type':'seller'},
        #         {'id':'2', 'name':'b', 'address':'bbb', 'email':'b@b.com', 'phone':'333', 'type':'buyer'}]
        visitcount_str = get_visitcount()
        varray = visitcount_str.split(':')
        return render_template('admin.html', datas=datas, yearcount=varray[0], monthcount=varray[1], daycount=varray[2], action='admin')
    else:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    register_ip()
    
    form = LoginForm()
    if form.validate_on_submit():
        name = form.name.data
        password = form.password.data
        if name == 'xxx' and password == 'yyy':
            session["logined"] = 'set'
            return redirect('/admin')
        else:
            flash('Wrong Access Info!')
            return redirect('/login')
    return render_template('login.html', form=form)

@app.route('/')
def index():
    return redirect('/sell')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/initdb')
def initdb():
    cur = mysql.connection.cursor()
    cur.execute('''DROP TABLE IF EXISTS `info`''')
    cur.execute('''DROP TABLE IF EXISTS `visitlog`''')
    cur.execute('''CREATE TABLE `info` (`email` varchar(50) NOT NULL,
                                        `name` varchar(50) NOT NULL,
                                        `address` varchar(128) NOT NULL,
                                        `phone` varchar(20) NOT NULL,
                                        `type` varchar(10) NOT NULL,
                                        PRIMARY KEY (`email`),
                                        UNIQUE KEY `email_UNIQUE` (`email`)
                                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;''')
    cur.execute('''CREATE TABLE `visitlog` (`id` int(11) NOT NULL AUTO_INCREMENT,
                                            `ip` varchar(20) NOT NULL,
                                            `vdate` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                            PRIMARY KEY (`id`)
                                            ) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;''')
    return 'Init Table Done!'

if __name__ == '__main__':
      app.run(host='192.168.1.102', port=8000, debug=True)

 