import json
import os
import threading
import psutil
import time
import shutil
import requests
import sqlite3
from datetime import datetime


class Monitor(threading.Thread):
    def __init__(self, time_weight: int, tolerance: int, database_path: str):
        threading.Thread.__init__(self)
        self._num_of_failures = 0
        self._stop_event = threading.Event()
        self._time_weight = time_weight
        self._tolerance = tolerance
        self._database_path = database_path

    def _tally_fault(self):
        self._num_of_failures += 1

    def _restart_tally(self):
        self._num_of_failures = 0

    def _over_tolerance(self) -> bool:
        return self._num_of_failures > self._tolerance

    def _log(self, conn, sql: str, parameters: tuple):
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute(sql, parameters)
            conn.commit()
        except sqlite3.ProgrammingError as p:
            raise Exception(f"A Programming error occurred {p}")
        except sqlite3.OperationalError as e:
            raise Exception(f"An sqlite3 operationalerror error occurred: {e}")
        except sqlite3.IntegrityError as e:
            raise Exception(f"An sqlite3 error occurred: {e}")
        except sqlite3.Error as e:
            raise Exception(f"An sqlite3 error occurred: {e}")
        except Exception as e:
            raise Exception(f"An error occurred: {e}")

    def _fail_monitor(self, conn):
        # should send diagnosis to loggging api
        # should kill monitor
        print("Monitor Failed")
        conn.close()

    def _send_mail(
        self,
        subject: str,
        message: str,
    ):
        try:
            # Prepare the payload
            payload = {
                "subject": subject,
                "message": message,
            }

            # Send POST request
            response = requests.post(
                "http://127.0.0.1:8000/v2/api/email", data=json.dumps(payload)
            )

            # Check if request was successful
            response.raise_for_status()

            # Try to parse JSON response if the endpoint returns JSON
            try:
                return response.json()
            except ValueError:
                # If not JSON, return the text result
                return {"result": response.text}

        except requests.exceptions.RequestException as e:
            return {"result": f"Error sending request: {str(e)}"}


class CPU_Monitor(Monitor):
    def __init__(
        self,
        time_weight: int,
        tolerance: int,
        tolerated_cpu_usage: float,
        time_to_gather_cpu: int,
        database_path: str,
    ):
        super().__init__(time_weight, tolerance, database_path)
        self._tolerated_cpu_usage = tolerated_cpu_usage
        self._time_to_gather_cpu = time_to_gather_cpu
        self.daemon = True

    def _over_used_cpu(self, current_cpu_usage: float) -> bool:
        return current_cpu_usage > self._tolerated_cpu_usage

    def run(self):
        conn = sqlite3.connect(self._database_path)
        while True:
            cpu_percent = psutil.cpu_percent(self._time_to_gather_cpu)
            cur_time = datetime.fromtimestamp(time.time())
            sql_string = """INSERT INTO components_cpu_diagnostics(cpu_percent_usage, event_time) VALUES ( ?, ?)"""
            sql_parameters = (cpu_percent, cur_time)
            try:
                self._log(conn, sql_string, sql_parameters)
            except Exception:
                self._fail_monitor(conn)
                return

            if self._over_used_cpu(current_cpu_usage=cpu_percent):
                self._tally_fault()

            if self._over_tolerance():
                # call to logging api to notify failure and kill monitor
                self._send_mail(
                    "CPU",
                    f"Tolerated cpu usage of {self._tolerated_cpu_usage}% exceded {self._tolerance} times",
                )
                self._fail_monitor(conn)

            time.sleep(self._time_weight)


class Memory_Monitor(Monitor):
    def __init__(
        self,
        time_weight: int,
        tolerance: int,
        tolerated_memory_usage: float,
        database_path: str,
    ):
        super().__init__(time_weight, tolerance, database_path)
        self._tolerated_memory_usage = tolerated_memory_usage
        self.daemon = True

    def _over_used_memory(self, memory_percent: float) -> bool:
        return memory_percent > self._tolerated_memory_usage

    def run(self):
        conn = sqlite3.connect(self._database_path)
        while True:
            memory_percent = psutil.virtual_memory()[2]
            memory_gc_total = psutil.virtual_memory().total / 1073741824
            memory_gc_usage = memory_percent * memory_gc_total * 0.01
            cur_time = datetime.fromtimestamp(time.time())
            sql_string = """INSERT INTO components_memory_diagnostics(memory_percent_usage, memory_GB_total, memory_GB_usage, event_time) VALUES ( ?, ?, ?, ?)"""
            sql_parameters = (
                memory_percent,
                memory_gc_total,
                memory_gc_usage,
                cur_time,
            )
            try:
                self._log(conn, sql_string, sql_parameters)
            except Exception:
                self._fail_monitor(conn)
                return

            if self._over_used_memory(memory_percent=memory_percent):
                self._tally_fault()

            if self._over_tolerance():
                # call to logging api to notify failure and kill monitor
                self._send_mail(
                    "MEMORY",
                    f"Tolerated memory usage {self._tolerated_memory_usage} exceded {self._tolerance} times",
                )
                self._fail_monitor(conn)
                return

            time.sleep(self._time_weight)


class Disk_Monitor(Monitor):
    def __init__(
        self,
        time_weight: int,
        tolerance: int,
        tolerated_disk_usage: float,
        path: str,
        database_path: str,
    ):
        super().__init__(time_weight, tolerance, database_path)
        self._tolerated_disk_usage = tolerated_disk_usage
        self.daemon = True
        self._path = path

    def _over_used_disk(self, disk_percent: float) -> bool:
        return disk_percent > self._tolerated_disk_usage

    def run(self):
        conn = sqlite3.connect(self._database_path)
        while True:
            disk_percent = (
                shutil.disk_usage(self._path).used / shutil.disk_usage(self._path).total
            )
            disk_gc_usage = shutil.disk_usage(self._path).used / 1073741824
            disk_gc_total = shutil.disk_usage(self._path).total / 1073741824
            cur_time = datetime.fromtimestamp(time.time())
            sql_string = """INSERT INTO components_disk_diagnostics(disk_percent_usage, disk_GB_total, disk_GB_usage, event_time) VALUES ( ?, ?, ?, ?)"""
            sql_parameters = (
                disk_percent,
                disk_gc_total,
                disk_gc_usage,
                cur_time,
            )
            try:
                self._log(conn, sql_string, sql_parameters)
            except Exception:
                self._fail_monitor(conn)
                return

            if self._over_used_disk(disk_percent=disk_percent):
                self._tally_fault()

            if self._over_tolerance():
                # call to logging api to notify failure and kill monitor
                self._send_mail(
                    "DISK",
                    f"Tolerated disk usage {self._tolerated_disk_usage} exceded {self._tolerance} times",
                )
                self._fail_monitor(conn)
                return

            time.sleep(self._time_weight)


class Endpoint_Monitor(Monitor):
    def __init__(
        self,
        time_weight: int,
        tolerance: int,
        endpoint_id: str,
        url: str,
        expected_code: int,
        database_path: str,
        certificate_path: str,
    ):
        super().__init__(time_weight, tolerance, database_path)
        self._endpoint_id = endpoint_id
        self._expected_code = expected_code
        self._url = url
        self._certificate_path = certificate_path
        self._diagnosis = ""
        self.daemon = True

    # checks to see if the url is valid (returns something)
    def _check_url(self, response: requests.Response) -> bool:
        return False

    def _check_response_code(self, response: requests.Response) -> bool:
        return response.status_code == self._expected_code

    def _build_diagnosis(self, log: str):
        self._diagnosis += log

    def run(self):
        conn = sqlite3.connect(self._database_path)
        while True:
            cur_time = datetime.fromtimestamp(time.time())
            try:
                response = requests.get(self._url)
                sql_string = """INSERT INTO components_endpoint_log(endpoint_status, event_time, endpoint_id_id) VALUES ( ?, ?, ?)"""
                sql_parameters = (
                    response.status_code,
                    cur_time,
                    self._endpoint_id,
                )
                try:
                    self._log(conn, sql_string, sql_parameters)
                except Exception:
                    print("happiness")
                    self._fail_monitor(conn)
                    return

                if not self._check_response_code(response):
                    self._tally_fault()
                    self._build_diagnosis(
                        f"{cur_time}: Code expected {self._expected_code}: Code received: {response.status_code}\n"
                    )
                response.close()

            except requests.exceptions.SSLError as s:
                # fail endpoint monitor
                self._build_diagnosis(f"{cur_time}: Ceritificate invalid. Error: {s}\n")
                self._send_mail(
                    "SSL",
                    f"{self._diagnosis}",
                )
                self._fail_monitor(conn)
                return
            except requests.exceptions.ConnectionError as c:
                self._build_diagnosis(f"{cur_time}: Connection Error: {c}\n")
                self._tally_fault()
            except requests.exceptions.HTTPError as h:
                self._build_diagnosis(f"{cur_time}: HTTPError: {h}\n")
                self._tally_fault()
            except Exception as e:
                self._build_diagnosis(f"{cur_time}: Unknown Error: {e}\n")
                self._send_mail(
                    "HTTP",
                    f"{self._diagnosis}",
                )
                self._fail_monitor(conn)
                return
            finally:
                if self._over_tolerance():
                    self._send_mail(
                        "ENDPOINT",
                        f"{self._diagnosis}",
                    )
                    self._fail_monitor(conn)
                    return

            time.sleep(self._time_weight)


def main():
    my_cpu_monitor = CPU_Monitor(2, 1, 0, 3, "../db.sqlite3")
    # my_memory_monitor = Memory_Monitor(2, 1, 0, "../db.sqlite3")
    # my_disk_monitor = Disk_Monitor(2, 1, 0, "/", "../db.sqlite3")
    # my_endpoint_monitor = Endpoint_Monitor(
    #     2,
    #     1,
    #     "123",
    #     "https://www.geeksforgeeks.org/",
    #     204,
    #     "../db.sqlite3",
    #     "/Users/noahcampise/project/secure-software-project/monitor-thread/server.pem",
    # )

    my_cpu_monitor.start()
    # my_memory_monitor.start()
    # my_disk_monitor.start()
    # my_endpoint_monitor.start()

    time.sleep(20)


if __name__ == "__main__":
    main()
