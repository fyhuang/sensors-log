# Runs in foreground

import os.path
import time
import datetime
import threading
import pickle

import sensors

from logdata import *

def chip_features(chip_name):
    for k in features_to_log.keys():
        if chip_name.startswith(k):
            return features_to_log[k]
    return None

def feature_enabled(features, feat_label):
    for f in features:
        if feat_label.startswith(f):
            return True
    return False

def log_one_iter():
    with log_lock:
        time_id = data.add_time(datetime.datetime.now())

        for chip in sensors.iter_detected_chips():
            chip_name = str(chip)
            features = chip_features(chip_name)
            if not features:
                continue

            print(chip_name)
            for feature in chip:
                if not feature_enabled(features, feature.label): continue
                print('  {}: {}'.format(feature.label, feature.get_value()))

                # Add to the log
                data.add_feature_value(time_id, chip_name, feature)

        #log_times.append(time.mktime(time.gmtime()))
        #data.log_times.append(datetime.datetime.now())

def run_log(interval):
    try:
        while True:
            log_one_iter()
            time.sleep(interval)
    finally:
        print("EXCEPTION in logging thread, cleaning up")
        # TODO? sensors.cleanup()

import http_viewer
def main():
    try:
        sensors.init()

        log_thread = threading.Thread(target=lambda: run_log(60.0))
        log_thread.daemon = True
        log_thread.start()

        http_viewer.run()
    finally:
        sensors.cleanup()

if __name__ == "__main__":
    main()
