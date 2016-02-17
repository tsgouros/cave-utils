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

import shelve
import re

import subprocess
import datetime

import logging
import os
import socket
import sys

# This holds a bunch of projector objects, indexed by serial number.
projs = dict()

# This holds a bunch of ProjectorControl objects, indexed by position number.
projControls = dict()


class RepairRecord(object):
    """
    Holds an entry in the repair and maintenance record of a projector.
    """
    def __init__(self, date, repair, comment):
        self.date = date
        self.repair = repair
        self.comment = comment

    def pretty(self):
        """
        Prints a nice record of the record.
        """
        print "  {0} / {1} ({2})".format(self.date, self.repair, self.comment)


class ProjectorControl(object):
    """
    Holds the data for a projector, in use.
    """
    def __init__(self, number, projector, serialSwitch, switchPort, location):
        """
        A class to contain the extra data needed by a projector in
        use.  When we speak of 'projector 24' we are speaking of a
        projector control, occupied by some particular projector with
        a serial number.  Were we to swap the projector for another,
        with a different serial number, it would still be 'projector
        24'.

        A projector control must have a projector in place to create
        this structure, but it can be uninstalled, later.

        number -- the number of the projector.  This is just an index
          to identify a switch and port to which the projector in
          question is attached.

        projector -- a serial number for a projector object, see below.
       
        serialSwitch -- identifies the serial switch to which this
          projector is attached. How is this set on the device?

        switchPort -- The port on the serial switch connected to this
          projector.

        location -- What role does this projector play?  (wall, ceiling,
          floor, door)

        """
        self.number = number
        # set this to "none" if there is no projector in that control spot.
        self.projector = projector
        self.serialSwitch = serialSwitch
        self.switchPort = switchPort
        self.location = location

        if self.projector != "none":
            projs[self.projector].setPurpose("installed")

    def send(self, cmd):
        """
        Sends a command to the projector.

        Should just become a subprocess.call(pjexpect...).

        Note that we need to return whatever the output is from
        issuing this command.
        """
        if self.projector != "none":
            print "proj{0}".format(self.number), self.serialSwitch, self.switchPort, "cmd =", cmd
            out = subprocess.check_output(["ssh",
                                           "cave020",
                                           "/gpfs/runtime/opt/cave-utils/yurt/bin/pjexpect", 
                                           "proj{0:02d}".format(self.number),
                                           "do",
                                           self.serialSwitch,
                                           self.switchPort,
                                           "\"{0}\"".format(cmd)])
        
        return out

    def getInt(self, string):
        """
        Extracts a number from a string such as 'RED.OFFSET = -25'.
        """
        for s in string.split():
            try:
                out = int(s)
                return out
            except ValueError:
                pass
        return "none"


    def recordProjectorData(self, override):
        """
        Acquire projector data and store it in the projector's
        permanent record.
        """
        if self.projector == "none":
            return

        errRecord = self.send("op prerr")
        errs = errRecord.split("##")

        ## Check to see that this is the right projector.  It may have
        ## been swapped without recording the swap, in which case the
        ## error record of the projector in place (retrieved via
        ## direct query to projector) may not match the error record
        ## in the database.

        if (not override) & (len(projs[self.projector].errorRecord) > 0) & (self.projector != "TESTBENCH") :
            if len(errs) > 0:
                # This is a little bit of a cheat.  We are comparing the last
                # few characters of the error record to see if this is the same
                # projector as used to be here.  Really we should be doing a 
                # serial number comparison, but that's not an option with this
                # firmware.
                if errs[1][-64:] not in projs[self.projector].errorRecord:
                    abandon("Please excuse me, but something is wrong. The projector gives an error record of {0}\nwhile the record reads {1}.\nAre you sure this is projector {2} we're talking about?".format(errs[1], projs[self.projector].errorRecord, self.projector))
            else:
                abandon("I'm so sorry, but something is wrong. The projector gives an empty error record\nwhile the record reads {0}.\nAre you sure this is projector {1} we're talking about?".format(projs[self.projector].errorRecord, self.projector))

        ## This appears to be the correct projector.
        if len(errs) > 1:
            projs[self.projector].setErrorRecord("##" + errRecord.split("##")[1])

        ## Check to see if the projector is on. They only respond
        ## properly to the color queries when powered up.
        status = self.send("op status.check ?")
        if status.split()[-1] != '2':
            print "ERR: Please power on the projector to gather color data and hours."
        else: 
            self.recordHours()
            self.recordColorSettings()

    def recordHours(self):
        """
        Records the total number of hours usage, and the bulb timer, too.
        """
        projs[self.projector].setTotalHours(self.getInt(self.send("op total.hours ?")))
        projs[self.projector].setLampHours(self.getInt(self.send("op lamp.hours ?")))

    
    def recordColorSettings(self):
        """
        Records the color settings in use into the projector's
        permanent record.
        """
        if self.projector == "none":
            return

        settings = [100, 100, 100, 100, 100, 100, 4, 4]

        settings[0] = self.getInt(self.send("op red.offset ?"))
        settings[1] = self.getInt(self.send("op green.offset ?"))
        settings[2] = self.getInt(self.send("op blue.offset ?"))

        settings[3] = self.getInt(self.send("op red.gain ?"))
        settings[4] = self.getInt(self.send("op green.gain ?"))
        settings[5] = self.getInt(self.send("op blue.gain ?"))

        settings[6] = self.getInt(self.send("op color.temp ?"))
        settings[7] = self.getInt(self.send("op gamma ?"))

        projs[self.projector].setColorSettings(settings)

    def pretty(self):
        """
        A pretty-printer for this projector's data.  Could be prettier.
        """

        print "\n=============================="
        print "Projector: {0}".format(self.number)
        if self.projector == "none":
            print "S/N:       none"
        else:
            print "S/N:       {0}".format(projs[self.projector].serialNo)
        print "Switch:    {0}/{1}".format(self.serialSwitch, self.switchPort)
        print "Location:  {0}".format(self.location)
        print "==============================\n"

        return


class Projector(object):
    """
    Holds the data for a single projector, in use or not.
    """
    def __init__(self, serialNo, mfgDate, lens):
        """
        Required data:

        serialNo -- A string containing the projector serial number.
          These are on a sticker where the serial and video outlets
          are, on the back of the projector.

        mfgDate -- the date of manufacture, on the same sticker.

        Other parts:

        records -- A list of maintenance and repair record objects,
          see repairRecord.

        purpose -- in use / spare / broken

        colorSettings -- The color settings used for this projector
          when it was last in use. 
          [r.offset, g.offset, b.offset, r.gain, g.gain, b.gain, color.temp, gamma]
        """
        self.serialNo = serialNo
        self.mfgDate = mfgDate

        self.lens = lens

        self.records = []

        self.purpose = "spare"

        self.colorSettings = [100, 100, 100, 100, 100, 100, 100, 4, 4]

        self.totalHours = 0
        self.lampHours = 0

        self.errorRecord = ""

    def addRecord(self, repair, comment):

        datestr = datetime.date.isoformat(datetime.date.today())
        self.records.append(RepairRecord(datestr, repair, comment))

        return

    def setPurpose(self, newPurpose):
        self.purpose = newPurpose

    def setTotalHours(self, hours):
        self.totalHours = hours

    def setLampHours(self, hours):
        self.lampHours = hours

    def setErrorRecord(self, record):
        self.errorRecord = record

    def setColorSettings(self, settings):
        """
        Records the color settings for this projector.  It's unclear
        whether these depend on the bulb or the electronics or what,
        so it's potentially useful to keep them around.

        The color settings are six numbers for the RGB offset and
        gain, the color temperature setting, and the gamma.  The
        default value for the first six is 100 (they range from 0-200)
        and the default value for the last two is 4 (these are
        discrete settings, 0-4).
        """

        self.colorSettings = settings

    def pretty(self):
        """ Report writer, preliminary version """
        print "\n=============================="
        print "Projector:   {0}".format(self.serialNo) 
        print "Mfg date:    {0}".format(self.mfgDate)
        print "Purpose:     {0}".format(self.purpose)
        print "Lens:        {0}".format(self.lens)
        print "Total hours: {0}".format(self.totalHours)
        print "Lamp hours:  {0}\n".format(self.lampHours)

        print "Error record ({0}):".format(self.serialNo)
        print self.errorRecord

        if len(self.records) > 0:
            print "Repair record ({0}):".format(self.serialNo)

            for record in self.records:
                record.pretty()
            print " "
        
        print "Color report ({0}):".format(self.serialNo)
        print "  red.offset   = {0}".format(self.colorSettings[0])
        print "  green.offset = {0}".format(self.colorSettings[1])
        print "  blue.offset  = {0}".format(self.colorSettings[2])

        print "  red.gain     = {0}".format(self.colorSettings[3])
        print "  green.gain   = {0}".format(self.colorSettings[4])
        print "  blue.gain    = {0}".format(self.colorSettings[5])

        print "  color.temp   = {0}".format(self.colorSettings[6])
        print "  gamma        = {0}\n".format(self.colorSettings[7])
        print "==============================\n"

        return

def gatherReportData(projectorControls):
    """
    Runs through all the installed projectors and gathers settings and
    the error log from each one, and stores them in the corresponding
    Projector object where it is accessible for reporting.
    """
    for k in projectorControls.keys():
        projectorControls[k].recordProjectorData(False)


def fullReport(projectors, projectorControls):
    """
    Produces a printable/readable version of all the information in
    the database.  This includes a dump of the projector data and of
    the projector control data.  The other stuff you'll see in this
    program is a part of one or the other of those collections.
    """

    print "\n\nPROJECTOR CONDITION REPORT"
    projKeys = projectors.keys()
    projKeys.sort()
    for k in projKeys:
        projectors[k].pretty()

    print "\n\nPROJECTOR CONTROL REPORT"
    projKeys = projectorControls.keys()
    projKeys.sort()    
    for k in projKeys:
        projectorControls[k].pretty()


def findRecord(serialFragment, projectors):
    """
    Find a serial number from a fragment of a serial number.  If the
    fragment does not define a unique serial number, a null value is
    returned.
    """

    output = list()

    for k in projectors.keys():
        if re.search(serialFragment, k):
            output.append(k)

    if len(output) == 1:
        return output[0]
    else:
        return "none"


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


    ## TODO: This should not exit, but throw some kind of exception
    ## that if not handled, closes the shelf and exits.
    def abandon(errorString):
        print "ERR:", errorString
        shelf.close()
        exit()

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

    # print(args.range)
    # print(args.serialNo)
    # print(args.repairType)
    # print(args.comment)
    # print(args.args)

    #########################################################################
    # Open the shelf file.  It might be empty, so check first.
    shelf = shelve.open("/gpfs/runtime/opt/cave-utils/yurt/etc/projector.db", writeback=True)

    # Prepare the items on the shelf.
    if "projs" in shelf.keys():
        projs = shelf["projs"]
    else:
        shelf["projs"] = projs

    if "projControls" in shelf.keys():
        projControls = shelf["projControls"]
    else:
        shelf["projControls"] = projControls 


    #########################################################################
    # Run through the projectors gathering their data.
    if args.gather:

        if args.serialNo == "none":

            gatherReportData(projControls)
        else:

            abandon("Please use the projector number (not the serial number) to\noperate the gather function.")

        shelf.close()
        exit()

    #########################################################################
    # Issue a report. Decide if it's just for one projector or for the whole
    # shebang, and then print it.
    if args.report:

        if args.serialNo == "none":
            fullReport(projs, projControls)
        else:

            sn = findRecord(args.serialNo, projs)

            if sn == "none":
                abandon("I wish I could say otherwise, but I have no record of a\nserial number like {0}".format(args.serialNo))

            projs[sn].pretty()

        shelf.close()
        exit()

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

        if args.serialNo == "none":
            abandon("I'm sorry, I need to have a projector to operate on.")

        # Decide whether we're adding a projector.

        if args.add:
            ############### Add
            # Apparently so. Check for presence of non-duplicate serial number.

            if args.serialNo in projs.keys():
                abandon("My deepest apologies, but there seems to be a projector by\nthe name of {0} already in the database.".format(args.serialNo))

            # Check for a date.
            if args.mfgDate == "none":
                abandon("My only wish is to serve you, but I need to have a manufacturing\ndate to enter a projector into the database.")

            # We are not doing data sanity checking. It's up to you to
            # enter good data.
            projs[args.serialNo] = Projector(args.serialNo, args.mfgDate, args.lens)

            # If there was a purpose specified on the command line,
            # add it.
            if args.purpose != "none":
                projs[args.serialNo].setPurpose(args.purpose)

            print "added:"
            projs[args.serialNo].pretty()

            ############### End Add
        else:
            ############### Repair
            # It appears that we are to make a repair entry.  Do some
            # data checking.
            sn = findRecord(args.serialNo, projs)

            if sn == "none":
                abandon("Please don't be alarmed, but I have no record of a\nserial number {0}".format(args.serialNo))

            else:
                if (args.purpose == "none") & (args.repairType == "none"):
                    abandon("I wish I could help, but without a repairType or a purpose, I'm\nhonestly not sure what you want me to do.")

                if args.purpose != "none":
                    projs[sn].setPurpose(args.purpose)

                else:
                    if (args.repairType == "none") | (args.comment == "none"):
                        abandon("I'm sorry, I can't file a repair report without a repair type\nand a comment.  I have {0} and {1}".format(args.repairType, args.comment))

                    else:

                        projs[sn].addRecord(args.repairType, args.comment)

                        print "repairing", sn, args.repairType, args.comment

                print "result:"
                projs[sn].pretty()
            ############### End Repair

        #print shelf
        shelf.close()
        exit()


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
            
            for p in projectorsToControl:
                if p not in projControls.keys():
                    abandon("It's probably my fault but I never heard of projector {0}".format(p))

                print "repairing", p, " ".join(args.args[1:])
                if len(args.args) < 3:
                    abandon("So sorry.  I need a repair type (bulb, ballast, lens, board) and a comment about it to process the record.")

                if projControls[p].projector == "none":
                    abandon("I'm sorry, there seems not to be a projector installed at {0}".format(p))

                projs[projControls[p].projector].addRecord(args.args[1], args.args[2])
                print "result:"
                projs[projControls[p].projector].pretty()

            command = "none"
        elif re.match("inst", args.args[0]):
            if len(projectorsToControl) > 1:
                abandon("I regret extremely that I can only install one projector at a time.")

            command = "none"
            # This is to handle lines like this:
            #  pjcontrol 42 install W217WACY00045 switch03 1014 wall
            #
            # As above, we're not doing a lot of sanity checking here, so 
            # be careful.
            sn = findRecord(args.args[1], projs)

            if sn == "none":
                abandon("I regret that I can only install projectors I can identify.\n'{0}' is missing or ambiguous.".format(args.args[1]))
            else:

                p = projectorsToControl[0]

                if p in projControls.keys():
                    # We already have a slot for this, so only need to
                    # update the serial number.
                    print "Installing {0} at position {1}, switch {2}, port {3}, to be part of the {4}.".format(sn, p, projControls[p].serialSwitch, projControls[p].switchPort, projControls[p].location)

                    # Record the projector, but only if there isn't already one there.
                    if projControls[p].projector == "none":
                        projControls[p].projector = sn
                    else:
                        abandon("Sorry to bother you, but there seems already to be a projector ({0}) at {1}.".format(projControls[p].projector, p))

                else:
                    if len(args.args) < 4:
                        abandon("I'm afraid I need the switch and port data for that projector.")

                    print "Installing {0} at position {1}, switch {2}, port {3}, to be part of the {4}.".format(sn, p, args.args[2], args.args[3], args.args[4])
                    projControls[p] = ProjectorControl(p, 
                                                       sn,
                                                       args.args[2],
                                                       args.args[3],
                                                       args.args[4])

                # Record the installation.
                projs[projControls[p].projector].addRecord("install", "installed at {0}".format(p))


        elif re.match("unin", args.args[0]): # uninstall
            for p in projectorsToControl:

                if projControls[p].projector == "none":
                    print "I'm sorry, there seems not to be a projector installed at {0}".format(p)
                else:
                # Record the uninstallation.

                    projs[projControls[p].projector].addRecord("uninstall", "removed from {0}".format(p))
                    projs[projControls[p].projector].setPurpose("broken")
                    projs[projControls[p].projector].pretty()

                    projControls[p].projector = "none"

            command = "none"
                                                        
        elif re.match("repo", args.args[0]):
            for p in projectorsToControl:
                if p not in projControls.keys():
                    abandon("It's probably my fault but I never heard of projector {0}.".format(p))

                projControls[p].pretty()

                if projControls[p].projector != "none":
                    projs[projControls[p].projector].pretty()

            command = "none"

        elif re.match("gat", args.args[0]):
            for p in projectorsToControl:
                if p not in projControls.keys():
                    abandon("I wish I knew a projector {0}, but I don't.".format(p))
                projControls[p].recordProjectorData(False)

            command = "none"

        else:
            abandon("What command is that?")
            command = "none"

        # END of long if statement.

        if command != "none":
            for p in projectorsToControl:
                if p in projControls.keys():
                    if projControls[p].projector == "none":
                        print "ERR: I regret that there is no projector installed at {0} at the present.".format(p)
                    else:
                        if command == "op powoff":
                            projControls[p].recordHours()
                        print projControls[p].send(command)
                else:
                    abandon("So sorry. I never heard of projector {0}.".format(p))


    shelf.close()

