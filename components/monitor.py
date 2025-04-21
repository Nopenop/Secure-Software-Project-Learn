import json
import os
import threading
import psutil
import time
import shutil
import requests
import sqlite3
from datetime import datetime
import urllib3
from dotenv import load_dotenv


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

            response = requests.post(
                "http://127.0.0.1:8000/v2/api/email/",
                data=json.dumps(payload),
            )
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                return {"result": response.text}

        except requests.exceptions.RequestException as e:
            return {"result": f"Error sending request: {e}"}
        
        
    def _send_mail_monitor(
        self,
        subject: str,
        message: str,
        endpoint_id:str,
    ):
        try:
            # Prepare the payload
            payload = {
                "subject": subject,
                "message": message,
                "endpoint_id": endpoint_id
            }

            response = requests.post(
                "http://127.0.0.1:8000/v2/api/email/",
                data=json.dumps(payload),
            )
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                return {"result": response.text}

        except requests.exceptions.RequestException as e:
            return {"result": f"Error sending request: {e}"}


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

    def _over_used_cpu(self, current_cpu_usage: float) -> bool:
        return current_cpu_usage > self._tolerated_cpu_usage

    def run(self):
        print("Starting cpu monitor")
        conn = sqlite3.connect(self._database_path)
        while True:
            cpu_percent = psutil.cpu_percent(self._time_to_gather_cpu)
            event_time = datetime.fromtimestamp(time.time())
            sql_string = """INSERT INTO components_cpu_diagnostics(cpu_percent_usage, event_time) VALUES ( ?, ?)"""
            sql_parameters = (cpu_percent, event_time)
            try:
                self._log(conn, sql_string, sql_parameters)
            except Exception:
                self._fail_monitor(conn)
                return

            if self._over_used_cpu(cpu_percent):
                self._tally_fault()

            if self._over_tolerance():
                self._send_mail(
                    "CPU",
                    f"Tolerated CPU usage of {self._tolerated_cpu_usage}% exceeded {self._tolerance} times",
                )
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

    def _over_used_memory(self, memory_percent: float) -> bool:
        return memory_percent > self._tolerated_memory_usage

    def run(self):
        print("Starting memory monitor")
        conn = sqlite3.connect(self._database_path)
        while True:
            vm = psutil.virtual_memory()
            memory_percent = vm.percent
            memory_gb_total = vm.total / 1073741824
            memory_gb_usage = memory_percent * memory_gb_total * 0.01
            event_time = datetime.fromtimestamp(time.time())
            sql_string = """INSERT INTO components_memory_diagnostics(memory_percent_usage, memory_GB_total, memory_GB_usage, event_time) VALUES ( ?, ?, ?, ?)"""
            sql_parameters = (
                memory_percent,
                memory_gb_total,
                memory_gb_usage,
                event_time,
            )
            try:
                self._log(
                    conn,
                    "INSERT INTO components_memory_diagnostics(memory_percent_usage, memory_GB_total, memory_GB_usage, event_time) VALUES ( ?, ?, ?, ?)",
                    (memory_percent, memory_gb_total, memory_gb_usage, event_time),
                )
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
        self._path = path

    def _over_used_disk(self, disk_percent: float) -> bool:
        return disk_percent > self._tolerated_disk_usage

    def run(self):
        print("Starting disk monitor")
        conn = sqlite3.connect(self._database_path)
        while True:
            disk_usage = shutil.disk_usage(self._path)
            disk_percent = disk_usage.used / disk_usage.total
            disk_gb_usage = disk_usage.used / 1073741824
            disk_gb_total = disk_usage.total / 1073741824
            event_time = datetime.fromtimestamp(time.time())
            sql_string = """INSERT INTO components_disk_diagnostics(disk_percent_usage, disk_GB_total, disk_GB_usage, event_time) VALUES ( ?, ?, ?, ?)"""
            sql_parameters = (
                disk_percent,
                disk_gb_total,
                disk_gb_usage,
                event_time,
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
        self.endpoint_id = endpoint_id  # expose publicly for _send_mail
        self._url = url
        self._expected_code = expected_code
        self._certificate_path = certificate_path
        self._diagnosis = ""

    def _check_response_code(self, response: requests.Response) -> bool:
        return response.status_code == self._expected_code

    def _build_diagnosis(self, log: str):
        self._diagnosis += log
        
    def update_status(self, status:int):
        payload = {"endpoint_id":self.endpoint_id,
                "endpoint_status":status}
            
        response = requests.post(
                os.environ.get("HOST_URL")+"v2/api/update-status/",
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                verify=False
        )


    def run(self):
        print("Starting endpoint monitor")
        conn = sqlite3.connect(self._database_path)
        while True:
            event_time = datetime.fromtimestamp(time.time())
            try:
                response = requests.get(self._url)
                sql_string = """INSERT INTO components_endpoint_log(endpoint_status, event_time, endpoint_id_id) VALUES ( ?, ?, ?)"""
                sql_parameters = (
                    response.status_code,
                    event_time,
                    self._endpoint_id,
                )
                try:
                    self._log(conn, sql_string, sql_parameters)
                    self.update_status(0)

                except Exception:
                    self._fail_monitor(conn)
                    self.update_status(1)
                    return

                if not self._check_response_code(response):
                    self._tally_fault()
                    self._build_diagnosis(
                        f"{event_time}: Code expected {self._expected_code}: Code received: {response.status_code}\n"
                    )
                response.close()

            except requests.exceptions.SSLError as s:
                self.update_status(1)
                
                # fail endpoint monitor
                self._build_diagnosis(
                    f"{event_time}: Ceritificate invalid. Error: {s}\n"
                )
                self._send_mail_monitor(
                    "SSL",
                    f"{self._diagnosis}",
                    self.endpoint_id
                )
                self._fail_monitor(conn)
                return
            except requests.exceptions.ConnectionError as c:
   
                self._build_diagnosis(f"{event_time}: Connection Error: {c}\n")
                self._tally_fault()
            except requests.exceptions.HTTPError as h:

                self._build_diagnosis(f"{event_time}: HTTPError: {h}\n")
                self._tally_fault()
            except Exception as e:
          
                self._build_diagnosis(f"{event_time}: Unknown Error: {e}\n")
                self._send_mail_monitor(
                    "HTTP",
                    f"{self._diagnosis}",
                    self.endpoint_id,
                )
                self._fail_monitor(conn)
                return
            finally:
                if self._over_tolerance():
       
                    self._send_mail_monitor(
                        "ENDPOINT",
                        f"{self._diagnosis}",
                        self.endpoint_id,
                    )
                    self._fail_monitor(conn)
                    return

            time.sleep(self._time_weight)


def main():
    cpu_mon = CPU_Monitor(
        time_weight=2,
        tolerance=1,
        tolerated_cpu_usage=0,
        time_to_gather_cpu=3,
        database_path="../db.sqlite3",
    )
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
