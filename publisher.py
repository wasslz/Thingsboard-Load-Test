#!/usr/bin/python3
import logging
import random
import getopt
import requests
import json
import mysql.connector
import time
import sys
import yaml
from tb_device_mqtt import TBDeviceMqttClient, TBPublishInfo
import threading

# Variables
auth_token = ""
base_url = "https://demo.thingsboard.io"
headers = {
    "X-Authorization": auth_token,
    "Accept": "application/json",
    "Content-Type": "application/json"
}
db_host = "localhost"
db_name = "mqtt_load_test"
db_password = "password"
db_user = "root"
start_index = 0  # the index of the first device
devices_count = 3  # number of devices
delay = 3  # in seconds
messages_count = 20
thread_list = []
config_file = "config.yml"
all_done = False
mqtt_host = 'demo.thingsboard.io'
# Config
file_handler = logging.FileHandler(filename='app.log')
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    handlers=handlers, format='%(asctime)s : %(levelname)s : %(name)s : %(message)s', level=logging.ERROR)

logging.info("Test Starts")


# Functions

def welcoming():
    print('============================================================')
    print('===                                                      ===')
    print('===                                                      ===')
    print('===             This is a Load Test tool                 ===')
    print('===            for Thingsboard MQTT devices              ===')
    print('===                                                      ===')
    print('===           All right reserved for Wasslz              ===')
    print('===                                                      ===')
    print('===             Author: Mujahed Altahleh                 ===')
    print('===             email: mtahle@wasslz.com                 ===')
    print('===                                                      ===')
    print('===          Usage: master.py -c <config file>           ===')
    print('===                                                      ===')
    print('============================================================')


def finish():
    global flag
    flag = True

    while flag:
        if all_done == True:
            flag = False
            logging.warning("all done")
            delete_devices(start_index, devices_count)
            sys.exit(0)


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hc:")
    except getopt.GetoptError:
        welcoming()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            welcoming()
            sys.exit()
        elif opt in ("-c"):
            config_file = arg
            with open(config_file, 'r') as yml_file:
                cfg = yaml.safe_load(yml_file)
                global base_url, auth_token, db_host, db_name, db_password, db_user, start_index, devices_count, delay, messages_count, mqtt_host
                db_host = cfg['mysql']['host']
                db_name = cfg['mysql']['db']
                db_password = cfg['mysql']['password']
                db_user = cfg['mysql']['user']
                base_url = cfg['http']['http_host']
                mqtt_host = cfg['mqtt_node']['mqtt_host']
                auth_token = cfg['mqtt_node']['auth_token']
                start_index = cfg['devices']['start_index']
                devices_count = cfg['devices']['devices_count']
                delay = cfg['publish']['delay']
                messages_count = cfg['publish']['messages_count']


def connect_db():
    db_connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        passwd=db_password,
        database=db_name
    )
    # mycursor.execute("DROP TABLE devices")
    # mycursor.execute("CREATE TABLE devices (devIndex INT , devID VARCHAR(255) , name VARCHAR(255), token VARCHAR(255) )")
    # mycursor = db_connection.cursor()
    # print(mydb)
    logging.debug("Database connected:{}".format(db_connection))
    return db_connection


def add_devices(start_index, Number_of_devices):
    global device_name
    # try:
    for device_index in range(start_index, Number_of_devices + 1):
        device_name = "Testing_" + str(device_index)
        mydb = connect_db()
        sql = "SELECT devIndex from devices where devIndex=%s"
        sql_value = (device_index,)
        mycursor = mydb.cursor()
        mycursor.execute(sql, sql_value)
        results = mycursor.fetchall()
        mydb.disconnect()
        if len(results) > 0:
            logging.warn("results is not empty we need to check")
            for x in results:
                if device_index == x[0]:
                    logging.error("device index is exist")
                    return
                else:
                    logging.info("device index is not exist lets add it")
                    add_device(device_name=device_name,
                               device_index=device_index)
        else:
            add_device(device_name=device_name, device_index=device_index)
    # except requests.HTTPError as e:
    #     print('error{0}'.format(response.status_code))
    #     logging.warning('Error: {0}'.format(e))


def add_device(device_name, device_index):
    url = base_url + '/api/device'
    args = {"additionalInfo": "Testing Device",
            "name": device_name, "type": "MQTT Load Test"}
    logging.info("------Adding device name: {0}-------".format(device_name))
    response = requests.post(url, data=json.dumps(args), headers=headers)
    if response.status_code != 200:
        logging.debug(response.content)
        return
    data = response.json()
    if len(data) > 0 and device_name == data['name']:
        device_id = data['id']['id']
        token = get_device_token(device_id)
        mydb = connect_db()
        sql = "INSERT INTO devices (devID, name,devIndex,token) VALUES (%s, %s, %s,%s)"
        val = (device_id, device_name, device_index, token)
        mycursor = mydb.cursor()
        mycursor.execute(sql, val)
        mydb.commit()
        mydb.disconnect()
        logging.debug("record inserted.{}".format(mycursor.rowcount))


def delete_device(deviceID):
    url = base_url+'/api/device/{0}'.format(deviceID)
    try:
        dev_name = get_device_name(deviceID=deviceID)
        if len(dev_name) > 0:
            # logging.info("------Deleting device ID: {0}, Name: {1}-------".format(deviceID,dev_name))
            logging.warning(
                "------Deleting device ID: {0}, Name: {1}-------".format(deviceID, dev_name))
            response = requests.delete(url, headers=headers)
            logging.debug(response.content)

        else:
            print("Device Not Found with ID:{0}".format(deviceID))
        mydb = connect_db()
        sql_delete = "Delete from devices where devID = %s"
        sql_data = (deviceID,)
        mycursor = mydb.cursor()
        mycursor.execute(sql_delete, sql_data)
        mydb.commit()
        mydb.disconnect()
        logging.debug(mycursor.rowcount, "record(s) deleted")
    except requests.HTTPError as e:
        logging.debug('error{0}'.format(response.status_code))
        logging.warning('Error: {0}'.format(e))


def delete_devices(start_index, count):
    logging.info("Start deleting {0} devices".format(count))
    for device in range(count):
        logging.info("start for index: {0}".format(device + start_index))
        # sql = "SELECT MIN(devIndex) AS 'Minimum Value' FROM devices"
        # mycursor.execute(sql)
        # results = mycursor.fetchall()
        # minIndex = results[0][0]
        # if start_index < minIndex:
        # #     logging.info("index {0} out of range".format(start_index))
        #     return
        # else:
        mydb = connect_db()
        sql2 = "SELECT devID from devices where devIndex=%s"
        sql_value = (device + start_index,)
        mycursor = mydb.cursor()
        mycursor.execute(sql2, sql_value)
        results = mycursor.fetchall()
        mydb.disconnect()
        # logging.info(len(results))
        # if count > len(results):
        #     logging.info("count out of range")
        # else:
        dev_id = results[0][0]
        logging.warning("Device id:{0} going to be deleted".format(dev_id))
        delete_device(deviceID=dev_id)


def get_device_name(deviceID):
    url = base_url+'/api/devices?deviceIds={0}'.format(deviceID)
    try:
        logging.debug("------Querying device ID: {0}-------".format(deviceID))
        response = requests.get(url, headers=headers)
        data = response.json()
        if len(data) > 0:
            device_name = data[0]['name']
            return device_name
        else:
            return ""
    except requests.HTTPError as e:
        logging.debug('error{0}'.format(response.status_code))
        logging.warning('Error: {0}'.format(e))


def get_device_token(deviceID):
    url = base_url+"/api/device/{0}/credentials".format(deviceID)
    response = requests.get(url, headers=headers)
    data = response.json()
    token = data['credentialsId']
    return token


def publish():
    mydb = connect_db()
    mycursor = mydb.cursor()
    sql = "SELECT token FROM devices WHERE devIndex < %s"
    sql_val = (devices_count,)
    mycursor.execute(sql, sql_val)
    results = mycursor.fetchall()
    tokens_array = []
    for token in results:
        tokens_array.append(token[0])
    mydb.disconnect()

    for token in tokens_array:
        data_array = []
        logging.info("adding device Number:{0} and the token is: {1}".format(
            tokens_array.index(token), token))
        toggle = True
        for x in range(messages_count):
            toggle = not toggle
            value = random.randint(1, 100)
            telemetry = {"Msgs Count": x+1, "temperature": value,
                         "enabled": toggle, "currentFirmwareVersion": "v1.2.2"}
            data_array.append(telemetry)
            logging.info("adding msg number: {0}".format(x))
        thread_list.append(threading.Thread(
            target=tb_client_start, args=(data_array, token)))

        # logging.info("adding thread Number: ",tokens_array.index(token), " for token: ",token)

    for thread in thread_list:
        # thread.setDaemon(True)
        # logging.info("threads lists", thread_list)
        thread.setName(tokens_array[thread_list.index(thread)])
        # logging.info("token: ", tokens_array[thread_list.index(thread)])
        logging.debug("run thread name: {0} thread index: {1}".format(
            thread.getName(), thread_list.index(thread)))
        thread.start()
        # thread.join()
        # logging.info("new thread Starts: ", threading.enumerate())

    # delete_devices(start_index=1, count=3)


def tb_client_start(telemetries, token):
    logging.basicConfig(filename=token+'_app.log', filemode='w',
                        format='%(asctime)s : %(levelname)s : %(name)s : %(message)s', level=logging.INFO)
    client = TBDeviceMqttClient(mqtt_host, token)
    client.max_inflight_messages_set(50)
    client.connect()
    # logging.info("connect device: ", token)
    for telemetry in telemetries:
        logging.info("send telemetry: {0} for device with token: {1}".format(
            telemetries.index(telemetry), token))
        client.send_telemetry(telemetry)
        time.sleep(delay)
        # Sending telemetry and checking the delivery status (QoS = 1 by default)
        result = client.send_telemetry(telemetry)
        logging.debug(
            "results of client.send_telemetry(telemetry): {}".format(result))
        # get is a blocking call that awaits delivery status
        # success = result.get() == TBPublishInfo.TB_ERR_SUCCESS
        # if (success):
        #     # print("Success")
        #     logging.info("message sent successfully:{0} ".format(success))
        # else:
        #     logging.error("MQTT Failure: {0}".format(result))
    # Disconnect from ThingsBoard
    client.disconnect()
    # logging.info("all thread: ", threading.enumerate())
    global all_done
    all_done = True


if __name__ == "__main__":
    main(sys.argv[1:])
# publish_thread = threading.Thread(target=publish())
# publish_thread.setName("publishing")

# add_devices(start_index=start_index, Number_of_devices=3)
publish()
logging.info("Finished publishing")
# delete_devices(start_index,devices_count)

# creating_devices_thread = threading.Thread(target=add_devices,args=(start_index,devices_count),name="Creating Devices")
# publishing_data_thread = threading.Thread(target=publish,name="Publishing Data")
# deleting_devices_thread = threading.Thread(target=delete_devices,args=(start_index,devices_count),name="Deleting Devices")
#
# creating_devices_thread.start()
# publishing_data_thread.start()
# deleting_devices_thread.start()
#
# creating_devices_thread.join()
# publishing_data_thread.join()
# deleting_devices_thread.join()


# for x in range(messages_count):
#     publish()
#     time.sleep(delay)
# get_device_token("967077b0-2f6b-11e9-be13-4bcaaae79abc")
# add_devices(dev_name_prefix="Test_", start_index=1, Number_of_devices=3)
# time.sleep(20)
