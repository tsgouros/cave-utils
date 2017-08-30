#!/usr/bin/env python

from projectorDbMethods import *

import subprocess
import datetime

import logging
import os
import socket
import sys

dbManager = InventoryDatabaseManager("test.db")

def send(number, serialSwitch, serialPort, cmd): 
	print "proj{0}".format(number), serialSwitch, serialPort, "cmd =", cmd 
	out = subprocess.check_output(["ssh",
				       "cave001", 
				       "/gpfs/runtime/opt/cave-utils/yurt/bin/pjexpect", 
				       "proj{0:02d}".format(number), 
				       "do", 
				       serialSwitch, 
				       serialPort,
				       "\"{0}\"".format(cmd)])
	return out


if __name__ == "__main__":

    LOGFORMAT = '%(asctime)-15s %(machine)s %(username)s %(message)s'
    logging.basicConfig(filename='/gpfs/runtime/opt/cave-utils/yurt/log/pjcontrollog.txt', level=logging.DEBUG,format=LOGFORMAT)
    logdata = {'username': os.getlogin(),
               'machine':  socket.gethostname()}
    logging.info('pjcontrol %s', " ".join(sys.argv[1:]), extra=logdata)


    ## TODO: This should not exit, but throw some kind of exception
    ## that if not handled, closes the shelf and exits.
    def abandon(errorString):
        print "ERR:", errorString
        shelf.close()
        exit()

    # Create a parser for the command line
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-a','--add', dest='add', action='store_true', 
                        help='Add a bulb by supplying the bulbSerial and bulbLife. Example cmd: -a bulbSerial bulbLife')  
    parser.add_argument('args', nargs=argparse.REMAINDER, 
                        help="Pass in parameters for bulbSerial, bulbLife, bulbStatus, projectorSerial, lampHours, dateIn, dateOut")
    args = parser.parse_args()
    if args.add:
    	if len(args.args) < 2:
		abandon("You need to supply the bulbSerial and bulbLife in order to add a bulb")
	else:
		bulbSerial = args.args[0]
		bulbLife = args.args[1]
		dbManager.addBulb(bulbSerial, bulbLife)	
