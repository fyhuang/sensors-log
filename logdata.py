import threading
import sqlite3
from contextlib import closing

features_to_log = {
        'coretemp-isa': ['Core '],
        'w83627thf': ['temp1'],
        }
log_lock = threading.Lock()

class LogData(object):
    def __init__(self):
        self.DBNAME = 'logdata.db'
        self.cf_to_ix = {}

    def connect(self):
        return sqlite3.connect(self.DBNAME)

    def add_time(self, dt):
        conn = self.connect()
        with closing(conn.cursor()) as c:
            c.execute('INSERT INTO LogTimes VALUES(NULL, ?)', (str(dt),))
            time_id = c.lastrowid
        conn.commit()
        conn.close()

        return time_id

    def add_feature_value(self, time_id, chip_name, feature):
        conn = self.connect()

        chip_feat = (chip_name, feature.label)
        with closing(conn.cursor()) as c:
            cf_id = -1
            if chip_feat not in self.cf_to_ix:
                c.execute('SELECT cf_id FROM ChipFeatures WHERE chip_name=? AND feature_name=?', chip_feat)
                row = c.fetchone()
                if row is None:
                    c.execute('INSERT INTO ChipFeatures VALUES(NULL,?, ?, 0.0, 45.0)', chip_feat)
                    cf_id = c.lastrowid
                else:
                    cf_id = row[0]
                self.cf_to_ix[chip_feat] = cf_id
            else:
                cf_id = self.cf_to_ix[chip_feat]

            #data.log_values[full_name].append(feature.get_value())
            c.execute('INSERT INTO LogValues VALUES(NULL, ?, ?, ?)', (time_id, cf_id, feature.get_value()))

        conn.commit()
        conn.close()

data = LogData()

