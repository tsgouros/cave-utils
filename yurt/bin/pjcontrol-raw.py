#!/usr/bin/env python
#
# This is a set of routines meant to ease the pain of managing the
# collection of video projectors necessary to run the cave, um, I mean
# the YURT.  
#
# This is a stripped-down version of pjcontrol.py that is meant to be used
# in conjunction with projd.py.
#
# Tom Sgouros 11/2015
#

import shelve
import re

import subprocess
import datetime
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
            out = subprocess.check_output(["ssh",
                                           "cave001",
                                           "/gpfs/runtime/opt/cave-utils/yurt/bin/pjexpect-raw", 
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


    def recordProjectorData(self):
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

        if len(projs[self.projector].errorRecord) > 0:
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

        projs[self.projector].setTotalHours(self.getInt(self.send("op total.hours ?")))
        projs[self.projector].setLampHours(self.getInt(self.send("op lamp.hours ?")))

        if len(errs) > 1:
            projs[self.projector].setErrorRecord("##" + errRecord.split("##")[1])
        ## Check to see if the projector is on. They only respond
        ## properly to the color queries when powered up.
        status = self.send("op status.check ?")
        if status.split()[-1] != '2':
            abandon("Please power on the projector to gather color data.")

        self.recordColorSettings()

    
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
        projectorControls[k].recordProjectorData()


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
    parser.add_argument('args', nargs=argparse.REMAINDER, 
                        help="The remaining arguments in the command line: on|off|power|version|mode|mono|stereo|lamp|eco|std|hour|error|raw|repair|install|uninstall|report|gather.  Unique abbreviations are allowed.  Some of these arguments require further args.  For example 'install' requires a serial number, switch name and port, and location. And 'repair' needs a serial number.")

    # Execute the parser.
    args = parser.parse_args()

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
    # If we're here, we might have a range of projectors to control, or
    # maybe arguments passed via options.

    #
    # Do we have a range of projectors? 
    projectorsToControl = parseIntegers(args.range)

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
            command = " ".join(args.args[1:])
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
                        sys.stdout.write(projControls[p].send(command))
                else:
                    abandon("So sorry. I never heard of projector {0}.".format(p))


    shelf.close()

