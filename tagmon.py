#!/usr/bin/python

from threading import Thread
import os
import socket
import time
import shelve
import getpass
import datetime
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import logging
import httplib
import xml.etree.ElementTree as ET

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# =========================================================
# Thread functions

def listener():
    """Creates a socket to listen for HTTP messages from the firewall/Panorama"""
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('', 8100))
    serversocket.listen(5) # become a server socket, maximum 5 connections

    while True:
        connection, address = serversocket.accept()
        buf = connection.recv(512)
        if len(buf) > 0:
            buf = buf.split('\n')
            for line in buf:
                if "ip_is" in line:
                    line = line.split(':')
                    os.system("touch sources/{}".format(line[1]))
            connection.close()

# End thread functions
# =========================================================




# =========================================================
# Main functions


def checkKey(dev_IP):
    """Checks to see if we already have an API key"""
    if os.path.isfile('data.db'):
        print 'Data file found: checking for API key.'
        d = shelve.open('data.db')
        keycheck = d.has_key('api_key')
        if keycheck:
            print "Existing key found. Loading key..."
            logging.info('Existing key found. Loading key.')
            key = d['api_key']
            d.close()
            return key
        else:
            print "Key file is missing API key. Need to regenerate key."
            logging.critical('API key not found in data file. Regenerating key.')
            key = getAPIKey(dev_IP)
            return key
    else:
        print "No data file found. Please generate and API key."
        key = getAPIKey(dev_IP)
        return key


def getAPIKey(this_IP):
    """Generates an API key for use in subsequent calls"""
    pano_user = raw_input("Enter your username: ")
    pano_pass = getpass.getpass("Enter your password:")
    command = "/api/?type=keygen&user=" + pano_user + "&password=" + pano_pass
    key_params = {"type" : "keygen",
                  "user" : pano_user,
                  "password" : pano_pass}
    key_req = requests.get("https://{}/api/?".format(this_IP), params=key_params, verify=False)
    key_xml = ET.fromstring(key_req.content)
    new_key = key_xml.find('./result/key').text
    d = shelve.open('data')
    d['api_key'] = new_key
    d.close
    return new_key


def remove_tag(pan_IP, tag_IP, tag, key):
    """Removes a previously tagged IP address"""
    logging.info('Removing tag for %s', tag_IP)
    cmd = "<uid-message><version>1.0</version><type>update</type><payload><unregister>" \
          "<entry ip=\"{}\"><tag><member>{}</member></tag></entry></unregister>" \
          "</payload></uid-message>".format(tag_IP, tag)
    tag_params = {"type" : "user-id",
                  "vsys" : "vsys1",
                  "cmd" : cmd,
                  "key" : key}
    response = requests.get("https://{}/api/?".format(pan_IP), params=tag_params, verify=False)
    return


# =========================================================
# Main body



logging.basicConfig(filename="tagmon.log", format=' %(asctime)s %(levelname)s:\t\t%(message)s', level=logging.DEBUG)


if not os.path.exists("sources"):
    os.makedirs("sources")



dev_IP = raw_input('What is the IP address of the firewall/Panorama? ')
tag_name = raw_input('What is the tag name:? ')
expiry = raw_input('Number of hours to keep tags active for an entry: ')
exp_int = int(expiry)

api_key = checkKey(dev_IP)


listener_thread = Thread(target=listener)
listener_thread.start()
logging.info('Started listener thread.')





while True:
    logging.info('Beginning cleanup of old entries.')
    files = os.listdir('./sources')
    for item in files:
        if "tag" not in item:
            now = datetime.datetime.today()
            last_mod = os.path.getmtime("./sources/%s" %item)
            last_seen = datetime.datetime.fromtimestamp(last_mod)
            expiry_delta = datetime.timedelta(hours=exp_int)
            if ( last_seen + expiry_delta ) < now:
                logging.info('%s has not been seen in %s hours.' % (item, expiry))
                remove_tag(dev_IP, item, tag_name, api_key)
                os.remove("./sources/%s" % item)
            else:
                logging.info('%s is still within quarantine period.' % item)
    time.sleep(3600)
