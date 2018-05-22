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
import json
import os
import time


class JsonConfigReader:
    def __init__(self, filename):
        self.file_name = filename
        self.values = {}
        self.parse_all()

    def parse_all(self):
        try:
            data = json.load(open(self.file_name))
        except Exception as ex:
            raise Exception("Error while reading file %s with exception %s" % (self.file_name, ex))

        for key, val in data.items():
            self.values[key] = val

    def read(self, keyname):
        return self.values.get(keyname, None)


class CommonConfigReader(JsonConfigReader):
    def get_adb_commands(self):
        return self.read('adb')

    def universal_init_adb_command(self):
        all_adb_commands = self.get_adb_commands()
        params = all_adb_commands.get("reverse", "")
        return params

    def get_start_command(self):
        return self.read("start")

    def get_end_command(self):
        return self.read("stop")

    def get_queue_name(self):
        return self.read('queue_name')

    def get_max_timeout(self):
        return self.read('max_time_limit')


def get_common_config(filename=None):
    if filename is None:
        filename = 'config.json'
    common_config_class = CommonConfigReader(filename)
    return common_config_class


if __name__ == "__main__":
    cls = get_common_config()
    print(cls.get_queue_name())
