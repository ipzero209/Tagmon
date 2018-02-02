#!/usr/bin/python

from threading import Thread
import os
import socket
import time
import shelve
import getpass
import datetime
import requests
import logging
import httplib
import xml.etree.ElementTree as ET




# =========================================================
# Thread functions

def listener():
    """Creates a socket to listen for HTTP messages from the firewall/Panorama"""
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('', 8089))
    serversocket.listen(5) # become a server socket, maximum 5 connections

    while True:
        connection, address = serversocket.accept()
        buf = connection.recv(512)
        if len(buf) > 0:
            fName =  buf[146:]
            os.system("touch ./sources/%s" % fName)
            connection.close()

# End thread functions
# =========================================================




# =========================================================
# Main functions

def getAPIKey(this_IP):
    """Generates an API key for use in subsequent calls"""
    # if os.path.isfile('data'):
    #     print "Keyfile found. Deleting old Key.\n\n\n"
    #     os.remove('data')
    pano_user = raw_input("Enter your username: ")
    pano_pass = getpass.getpass("Enter your password:")
    command = "/api/?type=keygen&user=" + pano_user + "&password=" + pano_pass
    req_conn = httplib.HTTPSConnection(this_IP)
    req_conn.request("GET", command)
    response = req_conn.getresponse()
    xml_resp = response.read()
    root = ET.fromstring(xml_resp)
    # print "Your new API Key is: " + root[0][0].text
    new_key = root[0][0].text
    d = shelve.open('data')
    d['api_key'] = new_key
    d.close
    return new_key



def remove_tag(pan_IP, tag_IP, tag, key):
    """Removes a previously tagged IP address"""
    logging.info('Removing tag for %s', tag_IP)
    command = "http://" + pan_IP + "/api/?type=user-id&vsys=vsys1&cmd=<uid-message><version>1.0</version><type>update</type><payload><unregister><entry ip=\"" + tag_IP + "\"><tag><member>" + tag + "</member></tag></entry></unregister></payload></uid-message>&key=" + key
    response = requests.request('GET', command)
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

api_key = getAPIKey(dev_IP)


listener_thread = Thread(target=listener)
listener_thread.start()
logging.info('Started listener thread.')



# Check to see if we have an API key already. If we do, load it.

# if os.path.isfile('data.db'):
#     print 'Data file found: checking for API key.'
#     d = shelve.open('data.db')
#     #keycheck = d.has_key('api_key')
#     try:
#         api_key = d['api_key']
#         print "Existing API key loaded."
#         sleep(2)
#         d.close
#     except Exception:
#         print "No API key found. We will generate one now."
#         sleep(3)
#         api_key = getAPIKey(dev_IP)
# else:
#     print "No data file found. Please generate and API key."
#     api_key = getAPIKey(dev_IP)

api_key = getAPIKey(dev_IP)

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
    time.sleep(150)
