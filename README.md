# General Application Web Server Monitoring System
General purpose Django Web Server Monitoring and Failure Notification Application.

Secure Software Engineering Final Project

## General Guide the Code

### /admin

/admin contains the settings, url pathing, and other things that allow us to make Django work correctly. Generally speaking, you should only be touching URLs regularly while to change the pathing for functions. Ask if you need help to change something on settings.py.

### /components

/components contains the components of the project - it will contain both the tooling to use components and the main components that make this program function. It also contains views, models, and test python files - generally speaking admin.py here will not be used and apps.py will practically never be used unless we need a name change for components.

### manage.py

manage.py provides a command line interface to interact with the django application

## Starting the application

Within a secure shell to your cloud web server run:

```bash
# Create virtual environment
python3 -m venv .venv

# Start virtual environment
source ./.venv/bin/activate

# Install all requirements needed to run the application
pip install -r requirements.txt

# create the database tables
python manage.py makemigrations
python manage.py migrate

# Change run script for 
sudo chmod u+x ./runme.sh

./runme.sh
```

Running this command will open a prompt to insert environment variables including:
- ADMIN_EMAIL
- EMAIL_HOST_USER
- EMAIL_HOST_PASSWORD
- COMPRESSION_PASSWORD

The AES_KEY used to encrypt your files will be generated and printed out to stdout. Make sure to save this key locally when you go to decrypt. 

For this instance of the server, you will never get the AES_KEY again.

You will need to 

## Diagrams:

```mermaid
---
title: Database Entity Relation Diagram
---
erDiagram
    USER ||--o{ ENDPOINT : has
    ENDPOINT ||--o{ ENDPOINT_LOG : logs
    USER {
        char user_id PK
        string email
        string password
    }
    ENDPOINT {
        char endpoint_id PK
        string endpoint_name
        string endpoint_path
        char user_id FK
    }
    ENDPOINT_LOG {
        int endpoint_status
        datetime event_time
        char endpoint_id FK
    }
    CPU_DIAGNOSTICS {
        float cpu_percent_usage
        datetime event_time
    }
    MEMORY_DIAGNOSTICS {
        float memory_percent_usage
        float memory_GB_usage
        float memory_GB_total
        datetime event_time
    }
    DISK_DIAGNOSTICS {
        float disk_percent_usage
        float disk_GB_usage
        float disk_GB_total
        datetime event_time
    }
```
```mermaid
---
title: Monitor System Class Diagram
---
classDiagram
    class Monitor {
        -int _num_of_failures
        -Event _stop_event
        -int _time_weight
        -int _tolerance
        -str _database_path
        -void _tally_fault()
        -bool _over_tolerance()
        -void _log(conn, sql, parameters)
        -void _fail_monitor(conn)
        -dict _send_mail(subject, message)
        +run()*
    }

    class CPU_Monitor {
        -float _tolerated_cpu_usage
        -int _time_to_gather_cpu
        -bool _over_used_cpu(current_cpu_usage)
        +run()
    }

    class Memory_Monitor {
        -float _tolerated_memory_usage
        -bool _over_used_memory(memory_percent)
        +run()
    }

    class Disk_Monitor {
        -float _tolerated_disk_usage
        -str _path
        -bool _over_used_disk(disk_percent)
        +run()
    }

    class Endpoint_Monitor {
        -str _endpoint_id
        -str endpoint_id
        -str _url
        -int _expected_code
        -str _certificate_path
        -str _diagnosis
        -bool _check_response_code(response)
        -void _build_diagnosis(log)
        +run()
    }

    Monitor <|-- CPU_Monitor
    Monitor <|-- Memory_Monitor
    Monitor <|-- Disk_Monitor
    Monitor <|-- Endpoint_Monitor

```
