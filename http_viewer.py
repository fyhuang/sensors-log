import time
from contextlib import closing
import datetime
import StringIO

import bottle
from bottle import route, request, response
import matplotlib.pyplot as plt
import matplotlib.dates

from logdata import *

bottle.debug(True)

TIME_FMT='%Y-%m-%d %H:%M:%S'

@route('/graph')
def graph():
    print("Graphing")
    multirows = []
    with log_lock:
        conn = data.connect()
        with closing(conn), closing(conn.cursor()) as c:
            c.execute('SELECT * FROM LogValues WHERE cf_id=1')
            multirows.append(c.fetchall())
            c.execute('SELECT * FROM LogValues WHERE cf_id=2')
            multirows.append(c.fetchall())
            c.execute('SELECT * FROM LogValues WHERE cf_id=3')
            multirows.append(c.fetchall())
            c.execute('SELECT * FROM LogTimes')
            time_rows = c.fetchall()

    iso_times = (x[1].split('.')[0] for x in time_rows)
    dts = [datetime.datetime.strptime(x, TIME_FMT) for x in iso_times]
    time_vals = matplotlib.dates.date2num(dts)

    cf1_vals = [x[3] for x in multirows[0]]
    cf2_vals = [x[3] for x in multirows[1]]
    cf3_vals = [x[3] for x in multirows[2]]

    plt.close('all')
    fig, ax = plt.subplots(1)
    ax.plot(dts, cf1_vals, 'r-', \
            dts, cf2_vals, 'g-', \
            dts, cf3_vals, 'b-')
    fig.autofmt_xdate()

    sio = StringIO.StringIO()
    plt.savefig(sio, format='png')
    sio.seek(0)
    response.content_type = "image/png"
    return sio

@route('/')
def index():
    return '<img src="{}/graph" />'.format(request['SCRIPT_NAME'])

class MyFlupFCGIServer(bottle.ServerAdapter):
    def run(self, handler): # pragma: no cover
        import flup.server.fcgi
        self.options.setdefault('bindAddress', '/run/lighttpd/sensors-log.sock')
        flup.server.fcgi.WSGIServer(handler, **self.options).run()

def run():
    bottle.run(server=MyFlupFCGIServer)
