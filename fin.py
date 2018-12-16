import requests
import re
import atexit
import sqlite3
import json
from flask import Flask, render_template, g
from werkzeug.contrib.fixers import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
scheduler = BackgroundScheduler()
DATABASE = 'metar.db'

places = ['KLWB', 'KFIG', 'KIOB', 'MMQT', 'CYOY', 'KENL', 'SKSP', 'CWMM', 'KS52', 'KGYL', 'KSGJ', 'KEVU', 'VTCC',
          'GMFM', 'GMTN', 'KCTY', 'CYFO', 'CWID', 'PAVC', 'KSTC', 'SBGR', 'CXEC', 'YMTG', 'MTPP', 'KJVL', 'VEJH',
          'ROYN', 'SKIP', 'KTTA', 'NZFX']

def get_db():
    with app.app_context():
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect(DATABASE)
        return db

"""
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
"""

def get_data(place):
    with app.app_context():
        file_url = ('http://tgftp.nws.noaa.gov/data/observations/metar/decoded/%s.TXT' % place)
        try:
            resp = requests.get(file_url).text
        except:
            pass
        try:
            wind = float(re.search('([0-9]{0,5})( MPH)', resp, re.MULTILINE).group(1))
        except AttributeError:
            wind = float(re.search('(Calm:)(0)', resp, re.MULTILINE).group(2))
        except:
            wind = ''
        try:
            pressure = float(re.search('([0-9]{3,5})( hPa)', resp, re.MULTILINE).group(1))
        except:
            pressure = ''
        try:
            cycle = re.search('(cycle: )([0-9]{0,2})', resp, re.MULTILINE).group(2)
        except:
            cycle = ''
        try:
            date = re.search('[0-9]{4}\.[0-9]{2}\.[0-9]{2}', resp, re.MULTILINE).group(0)
        except:
            date = ''
        try:
            humidity = float(re.search('(Relative Humidity: )([0-9]{1,3})(%)', resp, re.MULTILINE).group(2))
        except:
            humidity = ''

        db = get_db()
        cur = db.cursor()
        cur.execute("""Create TABLE if not exists %s (date,cycle,pressure FLOAT,wind FLOAT,humidity FLOAT,
                               UNIQUE(date, cycle))""" % place)
        db.commit()
        # cur.close()

    try:
        cur.execute("INSERT INTO %s VALUES (?,?,?,?,?)" % place, (date, cycle, pressure, wind, humidity))
        db.commit()
        # cur.close()
    except Exception:
        pass

@app.route('/')
def hello_world():
    return render_template('page.html')

"""
@app.route('/reports/')
@app.route('/reports/<name>')
def hello(name=None):
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        #sql = "SELECT pressure,humidity,wind FROM %s WHERE rowid = (SELECT MAX(rowid) FROM %s) AND (pressure < 990 
        #        OR humidity > 60 OR wind > 10)"
        cur.execute(sql % (name,name))
        db.commit()
        data = cur.fetchall()
        if not data:
            return render_template('report2.html', name=name)
        else:
            return render_template('report1.html', name=name)
"""

def job_function():
    for i in places:
        get_data(i)

#@app.route("/reports/<name>/plot")
@app.route('/reports/')
@app.route('/reports/<name>')
def chart(name=None):
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        sql1 = """SELECT pressure FROM %s"""
        cur.execute(sql1 % (name))
        data1 = json.dumps(cur.fetchall())
        cur.execute(sql1 % (name))
        sql2 = """SELECT date, cycle FROM %s"""
        cur.execute(sql2 % (name))
        weeks = json.dumps(cur.fetchall())
        sql3 = """SELECT wind FROM %s"""
        cur.execute(sql3 % (name))
        data2 = json.dumps(cur.fetchall())
        sql4 = """SELECT humidity FROM %s"""
        cur.execute(sql4 % (name))
        data3 = json.dumps(cur.fetchall())
        #db.commit()
        sql5 = """SELECT pressure,humidity,wind FROM %s WHERE rowid = (SELECT MAX(rowid) FROM %s) AND (pressure < 990 
                        OR humidity > 60 OR wind > 10)"""
        cur.execute(sql5 % (name, name))
        db.commit()
        status = cur.fetchall()
        if not status:
            #data = True
            return render_template('plot1.html', weeks=weeks, data1=data1, data2=data2, data3=data3)
        else:
            data = "false"
            return render_template('plot1.html', weeks=weeks, data1=data1, data2=data2, data3=data3, data=data)
        #return render_template('plot1.html', weeks=weeks, data1=data1, data2=data2, data3=data3, data=data)

scheduler.add_job(func=job_function, trigger="interval", minutes=60)
scheduler.start()
# atexit.register(lambda: scheduler.shutdown())

app.wsgi_app = ProxyFix(app.wsgi_app)
if __name__ == '__main__':
    job_function()
    app.run()