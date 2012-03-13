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


@route('/averages')
def averages():
    # Graph daily averages

@route('/graph')
def graph():
    print("Graphing")

    multirows = []
    with log_lock:
        conn = data.connect()
        with closing(conn), closing(conn.cursor()) as c:
            one_day_ago = datetime.datetime.now() - datetime.timedelta(1)

            c.execute('SELECT * FROM LogTimes WHERE timestamp > datetime(?)',
                    (one_day_ago.strftime(TIME_FMT),))
            time_rows = c.fetchall()

            cfids = request.query.cfids.split(',')
            for i in cfids:
                c.execute("SELECT lv.* FROM LogValues lv JOIN LogTimes lt ON lv.time_id = lt.time_id WHERE lv.cf_id=? AND lt.timestamp > datetime(?)",
                        (i, one_day_ago.strftime(TIME_FMT)))
                multirows.append(c.fetchall())

    iso_times = (x[1] for x in time_rows)
    dts = [datetime.datetime.strptime(x, TIME_FMT) for x in iso_times]
    time_vals = matplotlib.dates.date2num(dts)

    cf_vals = []
    for row in multirows:
        cf_vals.append([x[3] for x in row])

    graph_styles = ['r-', 'g-', 'b-']
    plt.close('all')
    fig, ax = plt.subplots(1)
    for (i,row) in enumerate(cf_vals):
        ax.plot(dts, row, graph_styles[i % len(graph_styles)])
    fig.autofmt_xdate()

    sio = StringIO.StringIO()
    plt.savefig(sio, format='png')
    sio.seek(0)
    response.content_type = "image/png"
    return sio

@route('/')
def index():
    return '<img src="{}/graph?cfids=1,2,3" />'.format(request['SCRIPT_NAME'])

class MyFlupFCGIServer(bottle.ServerAdapter):
    def run(self, handler): # pragma: no cover
        import flup.server.fcgi
        self.options.setdefault('bindAddress', '/run/lighttpd/sensors-log.sock')
        flup.server.fcgi.WSGIServer(handler, **self.options).run()

def run():
    bottle.run(server=MyFlupFCGIServer)
