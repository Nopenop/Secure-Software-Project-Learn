#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys

import components.monitor


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "serverMonitoring.settings")

    try:
        # On production, create cpu, disk, and memory monitors
        if os.environ.get("CREATE_OS_MONITORS") == "true":
            cpu_usage = int(os.environ.get("CPU_USAGE"))
            memory_usage = int(os.environ.get("MEMORY_USAGE"))
            disk_usage = int(os.environ.get("DISK_USAGE"))
            cpu_monitor = components.monitor.CPU_Monitor(
                2, 3, cpu_usage, 3, "./db.sqlite3"
            )
            memory_monitor = components.monitor.Memory_Monitor(
                5, 3, memory_usage, "./db.sqlite3"
            )
            disk_monitor = components.monitor.Disk_Monitor(
                5, 3, disk_usage, "/", "./db.sqlite3"
            )

            # Start OS diagnostic monitors
            cpu_monitor.start()
            disk_monitor.start()
            memory_monitor.start()

            # Ensure monitors are created only once
            os.environ["CREATE_OS_MONITORS"] = "false"
    except ValueError as e:
        # Raise exception when non-integer value is input for usage
        raise e
    except Exception:
        os.environ["CREATE_OS_MONITORS"] = "false"

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
