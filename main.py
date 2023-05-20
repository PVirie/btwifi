from bless import (
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions
)
from typing import Any
import asyncio
import time
import os
import sys
import subprocess
import signal
from loguru import logger

dir_path = os.path.dirname(os.path.realpath(__file__))

logger.add(os.path.join(dir_path, "log.log"))


def read_config():
    import json
    with open(os.path.join(dir_path, "config.json")) as f:
        return json.load(f)


def get_ssid():
    cmd = "nmcli -t -f active,ssid dev wifi | egrep '^yes' | cut -d\: -f2"
    ssid = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
    return ssid


def connect_to_wifi(ssid, password):
    # disconnect from all networks
    subprocess.run(["nmcli", "radio", "wifi", "off"])
    subprocess.run(["nmcli", "radio", "wifi", "on"])
    time.sleep(5)
    # connect to the specified network
    subprocess.run(["nmcli", "device", "wifi", "rescan"])
    subprocess.run(["nmcli", "device", "wifi", "connect", ssid, "password", password])



def read_request(
        characteristic: BlessGATTCharacteristic,
        **kwargs
) -> bytearray:

    str_characteristic = str(characteristic.uuid)

    if str_characteristic == config_data["nssid_characteristic_uuid"]:
        return get_ssid().encode("utf-8")

    return "".encode("utf-8")


temp_ssid = None
def write_request(
        characteristic: BlessGATTCharacteristic,
        value: Any,
        **kwargs
):
    global temp_ssid
    str_characteristic = str(characteristic.uuid)
    # only accept utf-8 string
    str_value = value.decode("utf-8")

    if str_characteristic == config_data["nssid_characteristic_uuid"]:
        logger.info("Received ssid: {}".format(str_value))
        temp_ssid = str_value
    elif str_characteristic == config_data["ncred_characteristic_uuid"]:
        logger.info("Received password for ssid: {}".format(temp_ssid))
        if temp_ssid is not None:
            logger.info("Connecting to wifi...")
            connect_to_wifi(temp_ssid, str_value)


server = None
order_reset = False


def signal_handler(sig, frame):
    global order_reset
    order_reset = True
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def init_bluetooth():
    global server

    my_service_name = config_data["service_name"]
    server = BlessServer(name=my_service_name)
    server.read_request_func = read_request
    server.write_request_func = write_request

    # Add Service
    my_service_uuid = config_data["service_uuid"]
    await server.add_new_service(my_service_uuid)

    await server.add_new_characteristic(
        my_service_uuid,
        config_data["nssid_characteristic_uuid"],
        GATTCharacteristicProperties.read | GATTCharacteristicProperties.write,
        None,
        GATTAttributePermissions.readable | GATTAttributePermissions.writeable)

    await server.add_new_characteristic(
        my_service_uuid,
        config_data["ncred_characteristic_uuid"],
        GATTCharacteristicProperties.write,
        None,
        GATTAttributePermissions.writeable)

    if not await server.start():
        logger.error("Bluetooth failed to start.")
        raise Exception("Bluetooth failed to start.")


async def sub_worker():
    order_reset = False

    await init_bluetooth()
    while True:
        if order_reset:
            logger.info("Stopping bluetooth...")
            await server.stop()
            await asyncio.sleep(10)
            break
        await asyncio.sleep(1)



if __name__ == '__main__':

    if os.path.exists(os.path.join(dir_path, "config.json")):
        config_data = read_config()
    else:
        print("config.json not found!")
        print("Please create config.json and place in the root directory with the following key-value pairs.")
        print("service_name: <name of the service (no hyphen, only _ allowed)>")
        print("service_uuid: <uuid of the service>")
        print("nssid_characteristic_uuid: <uuid of the network SSID>")
        print("ncred_characteristic_uuid: <uuid of the network PASSWORD>")
        sys.exit(1)

    asyncio.run(sub_worker())
