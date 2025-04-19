import os
import threading
import psutil
import time
import shutil
import requests
import sqlite3
import json
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Monitor(threading.Thread):
    def __init__(self, time_weight: int, tolerance: int, database_path: str):
        super().__init__()
        self._num_of_failures = 0
        self._stop_event = threading.Event()
        self._time_weight = time_weight
        self._tolerance = tolerance
        self._database_path = database_path
        self.daemon = True

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
            print(f"A Programming error occurred: {p}")
        except sqlite3.OperationalError as e:
            print(f"An sqlite3 operational error occurred: {e}")
        except sqlite3.Error as e:
            print(f"An sqlite3 error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def _fail_monitor(self, conn):
        print("Monitor Failed — shutting down thread.")
        conn.close()

    def _send_mail(self, subject: str, message: str):
        try:
            # build the base payload
            payload = {
                "subject": subject,
                "message": message,
            }
            # if this monitor has an endpoint_id, include it
            if hasattr(self, "_endpoint_id"):
                payload["endpoint_id"] = self._endpoint_id

            response = requests.post(
                "http://127.0.0.1:8000/v2/api/email",
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                verify=False  # we're disabling warnings above; in prod remove this
            )
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                return {"result": response.text}

        except requests.exceptions.RequestException as e:
            return {"result": f"Error sending request: {e}"}


class CPU_Monitor(Monitor):
    def __init__(self, time_weight: int, tolerance: int,
                 tolerated_cpu_usage: float, time_to_gather_cpu: int,
                 database_path: str):
        super().__init__(time_weight, tolerance, database_path)
        self._tolerated_cpu_usage = tolerated_cpu_usage
        self._time_to_gather_cpu = time_to_gather_cpu

    def _over_used_cpu(self, current_cpu_usage: float) -> bool:
        return current_cpu_usage > self._tolerated_cpu_usage

    def run(self):
        conn = sqlite3.connect(self._database_path)
        while True:
            cpu_percent = psutil.cpu_percent(self._time_to_gather_cpu)
            cur_time = datetime.now()
            self._log(
                conn,
                "INSERT INTO components_cpu_diagnostics(cpu_percent_usage, event_time) VALUES (?, ?)",
                (cpu_percent, cur_time)
            )

            if self._over_used_cpu(cpu_percent):
                self._tally_fault()

            if self._over_tolerance():
                self._send_mail(
                    "CPU",
                    f"Tolerated CPU usage of {self._tolerated_cpu_usage}% exceeded {self._tolerance} times"
                )
                self._fail_monitor(conn)
                return

            time.sleep(self._time_weight)


class Memory_Monitor(Monitor):
    def __init__(self, time_weight: int, tolerance: int,
                 tolerated_memory_usage: float, database_path: str):
        super().__init__(time_weight, tolerance, database_path)
        self._tolerated_memory_usage = tolerated_memory_usage

    def _over_used_memory(self, memory_percent: float) -> bool:
        return memory_percent > self._tolerated_memory_usage

    def run(self):
        conn = sqlite3.connect(self._database_path)
        while True:
            vm = psutil.virtual_memory()
            memory_percent = vm.percent
            total_gb = vm.total / (1024**3)
            usage_gb = memory_percent * total_gb * 0.01
            cur_time = datetime.now()
            self._log(
                conn,
                "INSERT INTO components_memory_diagnostics(memory_percent_usage, memory_GB_total, memory_GB_usage, event_time) VALUES (?, ?, ?, ?)",
                (memory_percent, total_gb, usage_gb, cur_time)
            )

            if self._over_used_memory(memory_percent):
                self._tally_fault()

            if self._over_tolerance():
                self._send_mail(
                    "MEMORY",
                    f"Tolerated memory usage of {self._tolerated_memory_usage}% exceeded {self._tolerance} times"
                )
                self._fail_monitor(conn)
                return

            time.sleep(self._time_weight)


class Disk_Monitor(Monitor):
    def __init__(self, time_weight: int, tolerance: int,
                 tolerated_disk_usage: float, path: str, database_path: str):
        super().__init__(time_weight, tolerance, database_path)
        self._tolerated_disk_usage = tolerated_disk_usage
        self._path = path

    def _over_used_disk(self, disk_percent: float) -> bool:
        return disk_percent > self._tolerated_disk_usage

    def run(self):
        conn = sqlite3.connect(self._database_path)
        while True:
            usage = shutil.disk_usage(self._path)
            disk_percent = usage.used / usage.total * 100
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            cur_time = datetime.now()
            self._log(
                conn,
                "INSERT INTO components_disk_diagnostics(disk_percent_usage, disk_GB_total, disk_GB_usage, event_time) VALUES (?, ?, ?, ?)",
                (disk_percent, total_gb, used_gb, cur_time)
            )

            if self._over_used_disk(disk_percent):
                self._tally_fault()

            if self._over_tolerance():
                self._send_mail(
                    "DISK",
                    f"Tolerated disk usage of {self._tolerated_disk_usage}% exceeded {self._tolerance} times"
                )
                self._fail_monitor(conn)
                return

            time.sleep(self._time_weight)


class Endpoint_Monitor(Monitor):
    def __init__(self, time_weight: int, tolerance: int,
                 endpoint_id: str, url: str, expected_code: int,
                 database_path: str, certificate_path: str):
        super().__init__(time_weight, tolerance, database_path)
        self._endpoint_id = endpoint_id
        self.endpoint_id = endpoint_id    # expose publicly for _send_mail
        self._url = url
        self._expected_code = expected_code
        self._certificate_path = certificate_path
        self._diagnosis = ""

    def _check_response_code(self, response: requests.Response) -> bool:
        return response.status_code == self._expected_code

    def _build_diagnosis(self, log: str):
        self._diagnosis += log

    def run(self):
        conn = sqlite3.connect(self._database_path)
        while True:
            cur_time = datetime.now()
            try:
                response = requests.get(self._url, verify=False)
                self._log(
                    conn,
                    "INSERT INTO components_endpoint_log(endpoint_status, event_time, endpoint_id_id) VALUES (?, ?, ?)",
                    (response.status_code, cur_time, self._endpoint_id)
                )

                if not self._check_response_code(response):
                    self._tally_fault()
                    self._build_diagnosis(
                        f"{cur_time}: Expected {self._expected_code}, got {response.status_code}\n"
                    )
                response.close()

            except requests.exceptions.SSLError as s:
                self._build_diagnosis(f"{cur_time}: SSL error: {s}\n")
                self._send_mail("SSL", self._diagnosis)
                self._fail_monitor(conn)
                return

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.HTTPError) as e:
                self._build_diagnosis(f"{cur_time}: Connection/HTTP error: {e}\n")
                self._tally_fault()

            except Exception as e:
                self._build_diagnosis(f"{cur_time}: Unknown error: {e}\n")
                self._send_mail("HTTP", self._diagnosis)
                self._fail_monitor(conn)
                return

            finally:
                if self._over_tolerance():
                    self._send_mail("ENDPOINT", self._diagnosis)
                    self._fail_monitor(conn)
                    return

            time.sleep(self._time_weight)


def main():
    db_path = os.path.join(os.path.dirname(__file__), "../db.sqlite3")
    cpu_mon = CPU_Monitor(time_weight=2, tolerance=1,
                          tolerated_cpu_usage=80.0,
                          time_to_gather_cpu=3,
                          database_path=db_path)
    cpu_mon.start()

    # Uncomment to run other monitors:
    # mem_mon = Memory_Monitor(2, 1, 80.0, db_path)
    # mem_mon.start()
    # disk_mon = Disk_Monitor(2, 1, 80.0, "/", db_path)
    # disk_mon.start()
    # endpoint_mon = Endpoint_Monitor(2, 1, "endpoint-123", "https://example.com/health", 200, db_path, "/path/to/cert.pem")
    # endpoint_mon.start()

    time.sleep(20)


if __name__ == "__main__":
    main()