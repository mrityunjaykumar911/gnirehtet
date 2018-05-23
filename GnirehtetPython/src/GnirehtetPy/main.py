"""
    Copyright (C) 2018 Genymobile
    modifier (C) mrityunjayk

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""
import logging
import os
import subprocess
from subprocess import PIPE, TimeoutExpired

import sys
from pqueue import Queue
import time
from psutil import Popen

from GnirehtetPython.src.GnirehtetPy import CONFIG_FILE_NAME
from GnirehtetPython.src.GnirehtetPy.Config.ConfigLoader import get_common_config

config_object = get_common_config(CONFIG_FILE_NAME)

# config start
queue_name = config_object.get_queue_name()

TIMER_FOR_WAIT = config_object.get_max_timeout()

STAY_CONNECTED = "stay"

INIT_CONNECT = config_object.universal_init_adb_command()
ACTUAL_GNIREHTET_START = "./setup/gnirehtet run"
START_GNIREHTET = config_object.get_start_command()
STOP_GNIREHTET = config_object.get_end_command()
END = "kill"

# config end

logger = logging.getLogger("gnirehtet")
logger.setLevel(logging.INFO)

class UsbUtils:
    def _is_your_android_phone_still_connected(self):
        first = None
        try:
            dev = str(subprocess.check_output(["adb", "devices", "-l"])).split("\\n").pop(1).split().pop(0)
            assert dev.isalnum() is True
            first = dev
        except:
            pass

        return first is not None

    def is_usb_connected(self, queue):
        connected = self._is_your_android_phone_still_connected()
        if connected:
            if queue.empty():
                queue.put(STAY_CONNECTED)
            return True
        else:
            return False


class GnirehtetClient:
    def __init__(self):
        self.connected = False
        self.process_id = None
        self.device_name = self.get_conected_deivce()

    def kill_old(self):
        if self.process_id is not None:
            os.system("kill -9 %s" % self.process_id)
            self.process_id = None

    def get_conected_deivce(self):
        first = None
        dev = str(subprocess.check_output(["adb", "devices", "-l"])).split("\\n").pop(1).split().pop(0)
        try:
            first = dev
            assert dev.isalnum() is True
        except:
            raise Exception("No android device found exception")

        return first

    def check_connected(self):
        try:
            dev = str(subprocess.check_output(["adb", "devices", "-l"])).split("\\n").pop(1).split().pop(0)
        except:
            self.connected = False
            return
        self.connected = (dev == self.device_name) and (self.process_id is not None)


def process_gnirehtet(callback, client):
    q = Queue(queue_name)


    start = time.time()

    def startTimer(started_time):
        for _ in range(int(TIMER_FOR_WAIT * 60)):
            logger.info("sleeping .......")
            logger.info("Queue", q.info)
            # print("sleeping .......")
            # print("Queue", q.info)
            time.sleep(1)
            if q.empty() is False:
                yield True
            callback.is_usb_connected(queue=q)
        if q.empty() is True:
            yield False
        else:
            yield True
        end = time.time()
        logger.info("Waited till", (end - started_time) // 60, "minutes")
        # print("Waited till", (end - started_time) // 60, "minutes")

    for _ in startTimer(start):
        if q.empty():
            continue
        ans = q.get()
        if ans == END:
            sys.exit(0)
        elif ans == STAY_CONNECTED:
            time.sleep(1)
            client.kill_old()
            q.task_done()
            clear_prev_queue(q)
            q.put(ACTUAL_GNIREHTET_START)
            q.put(STOP_GNIREHTET)
            q.put(START_GNIREHTET)
            continue

        process = subprocess.Popen(ans.split())
        try:
            process.communicate(timeout=10)
        except TimeoutExpired:
            logger.info("answer is ", ans)
            # print("answer is ", ans)
            client.process_id = process.pid
            q.task_done()
            continue
        if process.poll() is True:
            # run command
            pass
        if ans != STOP_GNIREHTET:
            client.check_connected()
            while client.connected:
                client.check_connected()
                continue
        logger.info("answer is ", ans)

        # print("answer is ", ans)
        process.terminate()
        q.task_done()


def clear_prev_queue(q=None):
    if q is None:
        q = Queue(queue_name)
    while q.empty() is False:
        _ = q.get()
        q.task_done()


def start_gnirehtet():
    q = Queue(queue_name)
    assert q.empty() is True
    q.put(INIT_CONNECT)
    q.put(ACTUAL_GNIREHTET_START)
    q.put(STOP_GNIREHTET)
    q.put(START_GNIREHTET)
    del q


def end_gnirehtet():
    q = Queue(queue_name)
    q.put(STOP_GNIREHTET)
    q.put(END)
    del q


if __name__ == '__main__':
    client = GnirehtetClient()
    clear_prev_queue()
    os.system("rm -rf %s" % queue_name)

    try:
        callback = UsbUtils()
        start_gnirehtet()
        process_gnirehtet(callback,client)
        end_gnirehtet()
    except:
        client.kill_old()
