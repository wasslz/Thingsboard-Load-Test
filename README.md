# Thingsboard Load Test Tool

In this python script we are trying to create an automated load testing tool for Thingsboard, this tools has three main functions:
* Create a specified number of devices using API 
* Publish an MQTT using [ThingsBoard client Python SDK](https://github.com/thingsboard/thingsboard-python-client-sdk "ThingsBoard client Python SDK")
* Delete devices using API

We hope to make this tool to be in the form of Master  -> slaves schema, where the master creates devices and distribute the jobs and token to the slaves which may be located on a multi remote mahines.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

What things you need to install the software and how to install them.
The tool was written in Python3, so make sure that you have it install on your system also you need pip3 to install requirements.
```
 pip3 install -r requirements.txt
```
Also you need MySQL database to store devices IDs and tokens used by thingsboard, use following query to create the MySQL table

```sql
CREATE TABLE devices (devIndex INT , devID VARCHAR(255) , name VARCHAR(255), token VARCHAR(255) );
```
### Configuration
The configuration is in YAML formating, it is very clear and simple

```yaml
mysql: #MySQL connections parameters
    host: localhost
    user: db_user
    password: changeme
    db: db_name
http:
    http_host: https://demo.thingsboard.io #url to API backend of thingsboard
mqtt_node:
    mqtt_host: demo.thingsboard.io # mqtt host name
    auth_token: "" # Thingsboard authentication token*
devices:
    start_index: 0 # the index of the first device to be created 
    devices_count: 3 # number of devices be created
publish:
    delay: 5 # in seconds between every message
    messages_count: 3 # number of msgs to be published by each device
```
*For authentication token  Please refer to  [ThingsBoard API reference](https://thingsboard.io/docs/reference/rest-api/#rest-api-auth "ThingsBoard API reference")
## Usage

```
 python3 publisher.py -c config.yaml
```

## Contributing
The project is still on the PoC phase, the current script is doing the main jobs but it needs too much of working to be perfect, so all contribution are very welcomed.

## Roadmap
* create a job manager functions that creates jobs and distribute the tokens over the slaves
* create a communications mechanisism between the slave and the master (socket is sugested)


