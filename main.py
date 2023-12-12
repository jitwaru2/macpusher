import time
import plistlib
import pprint
import logging
import subprocess
import os.path
import pathlib
import time
import sqlite3
import os
import datetime
from handlers import pushbullet_forwarder
from os.path import expanduser
import json


home = expanduser("~")
config_path = os.path.join(home, ".macpusher_config")

with open(config_path) as f:
    CONFIG = json.load(f)


if not CONFIG.get("verify_ssl"):
    os.environ["CURL_CA_BUNDLE"] = ""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    darwin_user_folder = subprocess.run(
        ['getconf', 'DARWIN_USER_DIR'], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).stdout.decode("utf-8").strip()

    db_folder = os.path.join(darwin_user_folder, "com.apple.notificationcenter", "db2")
    db_file = os.path.join(db_folder, "db")

    con = sqlite3.connect(db_file)
    cursor = con.cursor()

    sql = "select max(delivered_date) from record"
    last_delivered_date = [obj for obj in cursor.execute(sql)][0][0]

    while True:
        sql = "select data, delivered_date from record where delivered_date > {} order by delivered_date desc".format(last_delivered_date)
        objs = [
            {
                "record": col,
            }
            for col in cursor.execute(sql)
        ]
        
        if len(objs) > 0:
            last_delivered_date = objs[0]["record"][1]

            for obj in objs:
                obj["plist"] = plistlib.loads(obj["record"][0], fmt=plistlib.FMT_BINARY)
                obj["unix_time"] = obj["record"][1] + 978307200

                app = obj["plist"]["app"]
                app = CONFIG["app_map"].get(app) or app
                pushbullet_forwarder.handle(
                    CONFIG["domain"],
                    app,
                    obj["plist"]["req"]["titl"],
                    obj["plist"]["req"]["body"],
                )

        time.sleep(5)
