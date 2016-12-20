#!/usr/bin/env python
#
# This is a set of routines meant to ease the pain of managing the
# collection of video projectors necessary to run the cave, um, I mean
# the YURT.  
#
# This is a program meant to be invoked from the command line.  There
# are two modes of operation.  One mode supports a legacy usage with
# command lines like this:
#
#   pjcontrol.py 42 install W217WOCY00053 switch 10013 wall
#
# and:
#
#   pjcontrol.py 42 repair bulb "Replaced bulb -- old one shattered."
#
# The other mode supports calls like this:
#
#   pjcontrol.py -a -s W217WOCY00053 -d 2012-05-21
#
# Which adds the given serial number to the database.


#
# Objects defined:
#
#  Projector control: This contains the data for a projector in
#    service in a particular spot.  This projector will have a number
#    and use defined, as well as a serial switch to which it is
#    attached, and so on.  This can only be created with a projector
#    serial number (for the projector installed there), but you can
#    uninstall it later, giving it a projector control of "none".
#
#  Projector: Data that defines a projector, regardless of whether or
#    how it is in use.  This data will include the serial number, date
#    of manufacture, repair and maintenance record, and suggested
#    color correction values.
#
#  Repair record: A date, operation, and some hopefully useful commentary.
#
#
# Tom Sgouros 05/2015
#

from projectorDbMethods import *

import re

import subprocess
import datetime

import logging
import os
import socket
import sys

#create a InventoryDatabaseManager object
dbManager = InventoryDatabaseManager("test.db") 

def abandon(errorString):
    print "ERROR: " + errorString
    exit()

def fullReport():
    """
    Produces a printable/readable version of all the information in
    the database.  This includes a dump of the projector data and of
    the projector control data.  The other stuff you'll see in this
    program is a part of one or the other of those collections.
    """
    dbManager.projectorReport()


def findRecord(serialFragment, projectors):
    """
    Find a serial number from a fragment of a serial number.  If the
    fragment does not define a unique serial number, a null value is
    returned.
    """

def send(number, serialSwitch, serialPort, cmd):
    print "proj{0}".format(number), serialSwitch, serialPort, "cmd =", cmd
    out = subprocess.check_output(["ssh",
				   "cave001",
				   "/gpfs/runtime/opt/cave-utils/yurt/bin/pjexpect",
				   "proj{0}".format(number),
				   "do",
				   serialSwitch,
				   serialPort,
				   "\"{0}\"".format(cmd)])
    return out



def getInt(string):
    print string
    for s in string.split():
	try:
	    out = int(s)
	    return out
        except ValueError:
	    pass
    return "none"    


def recordProjectorData(projNumber, override):
    ## modified from 
    cmdProperties = dbManager.getSendCmdProperties(projNumber)
    serialSwitch = cmdProperties[0]
    serialPort = cmdProperties[1]
    errRecord = send(projNumber, serialSwitch, serialPort, "op prerr")
    errs = errRecord.split("##")
    errs = errs[len(errs) - 1]
    ## some sanity check here but ignore it for now
    ## will come back to this later

    ## set error record
    if len(errs) > 1:
        #print "errors:"
	#print errs
	dbManager.recordErrorRecord(str(errs), projNumber)

    ##get status
    status = send(projNumber, serialSwitch, serialPort, "op status.check ?")
    if status.split()[-1] != '2':
	print "ERR: Please power on the projector to gather color data and hours."
    else:
	recordHours(projNumber, serialSwitch, serialPort)
	#print "record color settings " + projNumber 
	recordColorSettings(projNumber, serialSwitch, serialPort)

def recordHours(projNumber, serialSwitch, serialPort):
    totalHours = getInt(send(projNumber, serialSwitch, serialPort, "op total.hours ?"))
    lampHours = getInt(send(projNumber, serialSwitch, serialPort, "op lamp.hours ?"))
    #print "this is totalHours"
    #print totalHours
    totalHours = str(totalHours)
    lampHours = str(lampHours)
    dbManager.recordProjectorHours(totalHours, projNumber)
    dbManager.recordLampHours(lampHours, None, projNumber)

def recordColorSettings(projNumber, serialSwitch, serialPort):
    rOffset = getInt(send(projNumber, serialSwitch, serialPort, "op red.offset ?"))
    gOffset = getInt(send(projNumber, serialSwitch, serialPort,"op green.offset ?"))
    bOffset = getInt(send(projNumber, serialSwitch, serialPort,"op blue.offset ?"))
    rGain = getInt(send(projNumber, serialSwitch, serialPort,"op red.gain ?"))
    gGain = getInt(send(projNumber, serialSwitch, serialPort,"op green.gain ?"))
    bGain = getInt(send(projNumber, serialSwitch, serialPort,"op blue.gain ?"))
    cTemp = getInt(send(projNumber, serialSwitch, serialPort,"op color.temp ?"))
    gamma = getInt(send(projNumber, serialSwitch, serialPort,"op gamma ?"))
    serialNum = dbManager.getSerialFromNumber(projNumber)
    dbManager.setSettings(serialNum, (str(rOffset), str(gOffset), str(bOffset), str(rGain), str(gGain), str(bGain), str(cTemp),str(gamma)))    

def parseIntegers(inputStr=""):
    """
    Returns a list of integers from an input string.  The string is a
    comma-separated list (no spaces allowed) that can contain both
    numbers and ranges (e.g. 24-36 or 2-4).

    Acceptable input:

      3,4,6-9 --> [3, 4, 6, 7, 8, 9]
      23-27 --> [23, 24, 25, 26, 27]
      5,6,7 --> [5, 6, 7]
    """

    # print ">>", inputStr, "<<<"

    if inputStr == "none":
        return []

    # Use sets to remove duplicate values by default.
    selection = set()
    invalid = set()

    # Start by separating the tokens. Each token is either an integer
    # or a range.
    tokens = [x.strip() for x in inputStr.split(',')]

    for i in tokens:
        try:
            # typically tokens are plain old integers
            selection.add(int(i))
        except:
            # if not, then it might be a range
            try:
                token = [int(k.strip()) for k in i.split('-')]
                if len(token) > 1:
                    token.sort()
                    # with separated by a dash, try to build a valid range
                    first = token[0]
                    last = token[len(token)-1]
                    for x in range(first, last+1):
                        selection.add(x)
            except:
                # No good (no integer, no range).
                invalid.add(i)

    # Report invalid tokens before returning valid selection
    if len(invalid) > 0:
        print "Error: invalid projector numbers: " + invalid

    return list(selection)

if __name__ == "__main__":

    LOGFORMAT = '%(asctime)-15s %(machine)s %(username)s %(message)s'
    logging.basicConfig(filename='/gpfs/runtime/opt/cave-utils/yurt/log/pjcontrollog.txt', level=logging.DEBUG,format=LOGFORMAT)
    logdata = {'username': os.getlogin(),
               'machine':  socket.gethostname()}
    logging.info('pjcontrol %s', " ".join(sys.argv[1:]), extra=logdata)

    # Create a parser for the command line
    import argparse

    # This is all just argparse nonsense. For a documentation-rich
    # system, they didn't go out of their way to make the use of this
    # wonderful package terribly easy to read.
    parser = argparse.ArgumentParser(description='Projector control and tracking.  Use this script to turn projectors on and off, to adjust projector parameters for the projectors in use, and also to record repairs and other information about the projectors in the inventory.  See the script comments for more usage information.', epilog="Use 'pjcontrol 10-38 on' to turn on all the projectors from 10 to 38.  Try 'pjcontrol -s 00049 -r bulb -c 'shattered'' to record a bulb change.  You can also do 'pjcontrol 42 repair bulb 'shattered'")
    
    parser.add_argument('range', metavar='projs', nargs='?', default="none",
                        help="A comma-separated list of projector numbers or ranges.  Try '3,6,7' or '3-10' or '3,5,10-20'.")
    parser.add_argument('-s','--serial', dest='serialNo', nargs='?', 
                        default="none",
                        help='A projector serial number (or fraction thereof).  Use this to record actions on a projector that is not currently in use, or to add projectors to the system.')
    parser.add_argument('--clearErrs', dest='clearErrs', action='store_true',
                        help='Clear the error log for a projector.')
    parser.add_argument('-d','--date', dest='mfgDate', nargs="?", 
                        default="none",
                        help='The projector serial number stickers have a manufacturing date on them.  Record it here, in the format 2012-04-17.')
    parser.add_argument('-a','--add', dest='add', action='store_true', 
                        help='Signal that you are adding a projector to the database.  Requires that you specify a serial number and date and optional lens type, and  nothing else.')  
    parser.add_argument('-R','--report', dest='report', action='store_true', 
                        help='Produce a summary report about a projector.  Without a serial number specified, produce a summary report about all projectors and all projector controls.  Ignores all other arguments.')  
    parser.add_argument('-G','--gather', dest='gather', action='store_true', 
                        help='Run through all the projectors gathering all their data.  Ignores all other arguments.')  
    parser.add_argument('-r','--repairType', dest='repairType', nargs='?', 
                        default='none', 
                        choices=['none','bulb','ballast','lens','board','install','uninstall','ship'],
                        help='Indicates we are recording a repair. Use this to specify the type of repair (bulb, ballast, lens, board, install, uninstall), and do not forget to include a comment.')
    parser.add_argument('-l','--lens', dest='lens', nargs='?', 
                        default='long', 
                        choices=['none','long','short'],
                        help='Sets type of lens (long, short, none) for the given serial number.')
    parser.add_argument('-p','--purpose', dest='purpose', nargs='?', 
                        default='none', 
                        choices=['none','spare','broken','installed','returned'],
                        help='Record the current purpose of the projector (spare, broken, installed, returned).')
    parser.add_argument('-c','--comment', dest='comment', nargs='?', 
                        default='none', 
                        help='Commentary about the repair.')
    parser.add_argument('args', nargs=argparse.REMAINDER, 
                        help="The remaining arguments in the command line: on|off|power|version|mode|mono|stereo|lamp|eco|std|hour|error|raw|repair|install|uninstall|report|gather.  Unique abbreviations are allowed.  Some of these arguments require further args.  For example 'install' requires a serial number, switch name and port, and location. And 'repair' needs a serial number.")
    parser.add_argument('-t','--tech', dest='tech',
                        help='Name of the reponsible person who performed the repair')
    parser.add_argument('-n','--number', dest='projnum',
                        help='Projector Number')
    parser.add_argument('-loc','--location', dest='projLoc',
                        help='Projector Location')
    # Execute the parser.
    args = parser.parse_args()

    # This is just a hack because argparse seems to behave slightly
    # differently in 2.7.3 than in 2.7.5 where the development was
    # originally done.  Probably the -s option shouldn't be part of
    # the syntax, in favor of just making the code distinguish
    # between a range of projector numbers and a serial number.
    if args.serialNo != 'none':
        args.comment = args.comment + " " + args.range + " " + " ".join(args.args)
        args.range = "none"
        args.args = []

    #########################################################################
    # Run through the projectors gathering their data.
    if args.gather:

        if args.serialNo == "none":
	   #serial = dbManager.getProjSerialFromNum("67")
 	   numbers = dbManager.getAllProjNumber();
	   for num in numbers:
		#print num
		#serial = dbManager.getProjSerialFromNum(int(num))
		recordProjectorData(int(num), False)
	    #print serial
	    #recordProjectorData("67", False)

        else:
	   abandon("Please use the projector number (not the serial number) to\noperate the gather function.")
    #########################################################################
    # Issue a report. Decide if it's just for one projector or for the whole
    # shebang, and then print it.
    if args.report:

        if args.serialNo == "none":
            fullReport()
	    #recordColorSettings("1", "2", "3")
        else:
            findRecord(args.serialNo, projs)

    #########################################################################
    # Clear a projector's error record.
    if args.clearErrs:
        if args.serialNo == "none":
            abandon("I do regret it, but I cannot clear an error record without\nknowing which projector's record to clear.")
        else:
            sn = findRecord(args.serialNo, projs)

            if sn == "none":
                abandon("I wish I could say otherwise, but I have no record of a\nserial number like {0}".format(args.serialNo))

            projs[sn].errorRecord=""

        shelf.close()
        exit()


    #########################################################################
    # If we're here, we might have a range of projectors to control, or
    # maybe arguments passed via options.

    #
    # Do we have a range of projectors? 
    projectorsToControl = parseIntegers(args.range)

    # If test to see if there's a range.
    if projectorsToControl == []:

        # Without a range of projectors to control, the possible operations are:
        #  - add a projector
        #  - record a repair

        #if args.serialNo == "none":
            #abandon("I'm sorry, I need to have a projector to operate on.")

        # Decide whether we're adding a projector.

        if args.add:
            ############### Add
            # Apparently so. Check for presence of non-duplicate serial number.
	    # Check for a date.
            if args.mfgDate == "none":
                abandon("My only wish is to serve you, but I need to have a manufacturing\ndate to enter a projector into the database.")

            if args.lens == "none":
                abandon("My only wish is to serve you, but I need to have lens type first")
 
	    if args.serialNo == None or args.mfgDate == None or args.lens == None:
		abandon("We need serial number, date and lens type to store this projector")
	    dbManager.addProjector(args.serialNo, args.mfgDate, args.lens)
	    if args.projnum != None:
		print args.projnum
	        dbManager.addProjectorNumber(args.serialNo, args.projnum)
	    #TO DO#
	    if args.projLoc != None:
		dbManager.setLocation(args.serialNo, args.projLoc)

            ############### End Add
        elif args.repairType != "none":
	    ############## Repair
	    if args.serialNo == "none":
		abandon("Please provide a serial number")
	    else:
		dbManager.repairProjector(args.serialNo, args.repairType, args.tech, None , args.comment, args.mfgDate) 

#### TODO: Need rear.mode

    if len(args.args) > 0:
        if re.match("on", args.args[0]):
            command = "op powon"
        elif re.match("off", args.args[0]):
            command = "op powoff"
        elif re.match("pow", args.args[0]):
            command = "op status.check ?"
        elif re.match("ver", args.args[0]):
            command = "op soft.version ?"
        elif re.match("mode", args.args[0]):
            command = "op s3d.mode ?"
        elif re.match("mono", args.args[0]):
            command = "op s3d.mode = 0"
        elif re.match("stereo", args.args[0]):
            command = "op s3d.mode = 2"
        elif re.match("lamp", args.args[0]):
            command = "op lamp.pow ?"
        elif re.match("eco", args.args[0]):
            command = "op lamp.pow = 0"
        elif re.match("std", args.args[0]):
            command = "op lamp.pow = 1"
        elif re.match("hour", args.args[0]):
            command = "op lamp.hours ?"
        elif re.match("err", args.args[0]):
            command = "op prerr"
        elif re.match("debug", args.args[0]):
            command = "op demsg = 1"
        elif re.match("raw", args.args[0]):
            command = "op " + " ".join(args.args[1:])
        elif re.match("repa", args.args[0]):
            
	    if len(args.args) < 6:
                abandon("Need more information to proceed")
	    command = "none"
	elif re.match("inst", args.args[0]):
	    if len(projectorsToControl) > 1:
		abandon("I regret extremely that I can only install one projector at a time.") 
	    for p in projectorsToControl:
	    	dbManager.instProjector(p, args.args[1], args.args[2], args.args[3], args.args[4], args.args[5]) 
	    command = "none"
	elif re.match("gat", args.args[0]):
	    for p in projectorsToControl:
		recordProjectorData(int(p), False)	
        else:
            abandon("What command is that?")
            command = "none"
    	if command != "none":
	    for p in projectorsToControl:
		cmdProperties = dbManager.getSendCmdProperties(p)
		serialSwitch = cmdProperties[0]
		serialPort = cmdProperties[1]
		if command == "op powoff":
		    totalHours = getInt(send(p, serialSwitch, serialPort, "op total.hours ?"))
		    lampHours = getInt(send(p, serialSwitch, serialPort, "op lamp.hours ?"))	             
		    dbManager.recordProjectorHours(totalHours, p)
		    dbManager.recordLampHours(lampHours, p)
		else:
		    print "a bit lost here, what should I do?"
		    #print send(p, cmdProperties[0], cmdProperties[1], command)		
