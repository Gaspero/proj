import sqlite3
import requests
import re
import atexit
from flask import Flask
from flask import render_template
from werkzeug.contrib.fixers import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)
scheduler = BackgroundScheduler()

places = ['KLWB', 'KFIG', 'KIOB', 'MMQT', 'CYOY', 'KENL', 'SKSP', 'CWMM', 'KS52', 'KGYL', 'KSGJ', 'KEVU', 'VTCC',
          'GMFM', 'GMTN', 'KCTY', 'CYFO', 'CWID', 'PAVC', 'KSTC', 'SBGR', 'CXEC', 'YMTG', 'MTPP', 'KJVL', 'VEJH',
          'ROYN', 'SKIP', 'KTTA', 'NZFX']

def get_data(place):
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

    conn = sqlite3.connect("new.db")
    c = conn.cursor()
    c.execute("Create TABLE if not exists %s (date,cycle,pressure FLOAT,wind FLOAT,humidity FLOAT ,UNIQUE(date, cycle))"
              % place)

    try:
        c.execute("INSERT INTO %s VALUES (?,?,?,?,?)" % place, (date, cycle, pressure, wind, humidity))
        conn.commit()
    except Exception:
        pass

"""
@cron.interval_schedule(hours=1)
def job_function():
    for i in places:
        get_data(i)
"""


@app.route('/')
def hello_world():
    return render_template('page.html')

@app.route('/reports/')
@app.route('/reports/<name>')
def hello(name=None):
    with sqlite3.connect("new.db") as conn:
        c = conn.cursor()
        sql = """SELECT pressure,humidity,wind FROM %s WHERE rowid = (SELECT MAX(rowid) FROM %s) AND (pressure < 990 
        OR humidity > 60 OR wind > 10)"""
        c.execute(sql % (name,name))
        conn.commit()
        data = c.fetchall()
        if not data:
            return render_template('report2.html', name=name)
        else:
            return render_template('report1.html', name=name)

def job_function():
    for i in places:
        get_data(i)

scheduler.add_job(func=job_function, trigger="interval", minutes=15)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

app.wsgi_app = ProxyFix(app.wsgi_app)
if __name__ == '__main__':
    app.run()

