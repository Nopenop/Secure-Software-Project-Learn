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

    def _over_tolerance(self) -> bool:
        return self._num_of_failures > self._tolerance

    def _log(self, conn, sql: str, parameters: tuple):
        try:
            cursor = conn.cursor()
            cursor.execute(sql, parameters)
            conn.commit()
        except sqlite3.ProgrammingError as p:
            print(f"A Programming error occurred {p}")
        except sqlite3.OperationalError as e:
            print(f"An sqlite3 operationalerror error occurred: {e}")
        except sqlite3.Error as e:
            print(f"An sqlite3 error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def _fail_monitor(self, conn):
        # should send diagnosis to loggging api
        # should kill monitor
        print("Monitor Failed")
        conn.close()


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
            self._log(conn, sql_string, sql_parameters)

            if self._over_used_cpu(current_cpu_usage=cpu_percent):
                self._tally_fault()

            if self._over_tolerance():
                # call to logging api to notify failure and kill monitor
                self._fail_monitor(conn)
                return

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
            memory_percent = psutil.virtual_memory().percent
            memory_gc_usage = psutil.virtual_memory().used / 1048576
            memory_gc_total = psutil.virtual_memory().total / 1048576
            cur_time = datetime.fromtimestamp(time.time())
            sql_string = """INSERT INTO components_memory_diagnostics(memory_percent_usage, memory_GB_total, memory_GB_usage, event_time) VALUES ( ?, ?, ?, ?)"""
            sql_parameters = (
                memory_percent,
                memory_gc_usage,
                memory_gc_total,
                cur_time,
            )
            self._log(conn, sql_string, sql_parameters)

            if self._over_used_memory(memory_percent=memory_percent):
                self._tally_fault()

            if self._over_tolerance():
                # call to logging api to notify failure and kill monitor
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
            disk_gc_usage = shutil.disk_usage(self._path).used / 1048576
            disk_gc_total = shutil.disk_usage(self._path).total / 1048576
            cur_time = datetime.fromtimestamp(time.time())
            sql_string = """INSERT INTO components_disk_diagnostics(disk_percent_usage, disk_GB_total, disk_GB_usage, event_time) VALUES ( ?, ?, ?, ?)"""
            sql_parameters = (
                disk_percent,
                disk_gc_usage,
                disk_gc_total,
                cur_time,
            )
            self._log(conn, sql_string, sql_parameters)

            if self._over_used_disk(disk_percent=disk_percent):
                self._tally_fault()

            if self._over_tolerance():
                # call to logging api to notify failure and kill monitor
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
                response = requests.get(self._url, verify=self._certificate_path)
                sql_string = """INSERT INTO components_endpoint_log(endpoint_status, event_time, endpoint_id_id) VALUES ( ?, ?, ?)"""
                sql_parameters = (
                    response.status_code,
                    cur_time,
                    self._endpoint_id,
                )
                self._log(conn, sql_string, sql_parameters)
                if not self._check_response_code(response):
                    self._tally_fault()
                    self._build_diagnosis(
                        f"{cur_time}: Code expected {self._expected_code}: Code received: {response.status_code}\n"
                    )
                response.close()
            except requests.exceptions.SSLError as s:
                # fail endpoint monitor
                self._build_diagnosis(f"{cur_time}: Ceritificate invalid. Error: {s}\n")
                print(self._diagnosis)
                self._fail_monitor(conn)
                return
            except requests.exceptions.ConnectionError as c:
                # tally error
                self._build_diagnosis(f"{cur_time}: Connection Error: {c}\n")
                self._tally_fault()
            except requests.exceptions.HTTPError as h:
                # tally error
                self._build_diagnosis(f"{cur_time}: HTTPError: {h}\n")
                self._tally_fault()
            except Exception as e:
                # fail for unknown error type
                self._build_diagnosis(f"{cur_time}: Unknown Error: {e}\n")
                print(self._diagnosis)
                self._fail_monitor(conn)
                return
            finally:
                if self._over_tolerance():
                    # call to logging api to notify failure and kill monitor
                    print(self._diagnosis)
                    self._fail_monitor(conn)
                    return

            time.sleep(self._time_weight)


def main():
    my_cpu_monitor = CPU_Monitor(2, 1, 0, 3, "../db.sqlite3")
    my_memory_monitor = Memory_Monitor(2, 1, 0, "../db.sqlite3")
    my_disk_monitor = Disk_Monitor(2, 1, 0, "/", "../db.sqlite3")
    my_endpoint_monitor = Endpoint_Monitor(
        2,
        1,
        "123",
        "https://localhost:3000",
        200,
        "../db.sqlite3",
        "/Users/noahcampise/project/secure-software-project/monitor-thread/server.pem",
    )

    my_cpu_monitor.start()
    my_memory_monitor.start()
    my_endpoint_monitor.start()
    my_disk_monitor.start()

    time.sleep(20)


if __name__ == "__main__":
    main()
