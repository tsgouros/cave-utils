import sqlite3
import datetime

class InventoryDatabase:
    """
    This is the Inventory Database Object. (underlying object for
    InventoryDatabaseManager) It builds a database unique to its name,
    and executes all data manipulations (inserting into/updating
    tables).  We use sqlite3.
    """
    def __init__(self, pathname):
        """ 
        Initialized with the pathname of the database file.
        """
        # Should do some name checking and parsing here.
        self._name = pathname
        self._conn = sqlite3.connect(pathname)
        self._c = self._conn.cursor()

        # The methods inside here only function if the table they refer to
        # does not exist.  That is, for an existing table, this is a nop.
        self.createProjectorSettingsTable()
        self.createProjectorSettingsHistoryTable()
        self.createProjectorStatusTable()
        self.createProjectorStatusHistoryTable()
        self.createProjectorNumbersTable()
        self.createProjectorRepairsTable()
        self.createBulbStatusTable()
        self.createBulbStatusHistoryTable()


    def getName(self):
        """
        Input: None
        Output: name of the database file
        Purpose: Getter for the file name
        """
        return self._name

    def createProjectorNumbersTable(self):
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorNumbers(projNumber TEXT, onScreen TEXT, serialSwitch TEXT, serialPort TEXT, projServer TEXT, projDisplay TEXT)')
        
    def createProjectorSettingsTable(self):
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorSettings(projectorSerial TEXT, redOffset TEXT, greenOffset TEXT, blueOffset TEXT, redGain TEXT, greenGain TEXT, blueGain TEXT, colorTemp TEXT, gamma TEXT)')

    def createProjectorSettingsHistoryTable(self):
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorSettingsHistory(projectorSerial TEXT, redOffset TEXT, greenOffset TEXT, blueOffset TEXT, redGain TEXT, greenGain TEXT, blueGain TEXT, colorTemp TEXT, gamma TEXT, dateRecorded TEXT, note TEXT)')

    def createProjectorStatusTable(self):
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorStatus(projectorSerial TEXT, mfgDate TEXT, projNumber TEXT, totalHours TEXT, projStatus TEXT, onSite TEXT, lensType TEXT, repairID TEXT, errorRecord TEXT)')

    def createProjectorStatusHistoryTable(self):
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorStatusHistory(projectorSerial TEXT, mfgDate TEXT, projNumber TEXT, totalHours TEXT, projStatus TEXT, onSite TEXT, lensType TEXT, repairID TEXT, errorRecord TEXT, dateRecorded TEXT, note TEXT)')

    def createProjectorRepairsTable(self):
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorRepairs(repairID TEXT, projectorSerial TEXT, repairType TEXT, repairedBy TEXT, repairDate TEXT, repairNote TEXT)')

    def createBulbStatusTable(self):
        self._c.execute('CREATE TABLE IF NOT EXISTS BulbStatus(bulbID TEXT, bulbSerial TEXT, bulbLife TEXT, bulbStatus TEXT, projectorSerial TEXT, lampHours TEXT, dateIn TEXT, dateOut TEXT, repairID TEXT)')

    def createBulbStatusHistoryTable(self):
        self._c.execute('CREATE TABLE IF NOT EXISTS BulbStatusHistory(bulbID TEXT, bulbSerial TEXT, bulbLife TEXT, bulbStatus TEXT, projectorSerial TEXT, lampHours TEXT, dateIn TEXT, dateOut TEXT, repairID TEXT, dateRecorded TEXT, note TEXT)')


class DatabaseTable:
    """
    Contains information relevant to a particular table in a given
    database.  The class can include both a pointer to a table and a
    pointer to a corresponding history table.  If autohistory is True,
    an entry is made in the history table when the table changes.

    """
    def __init__(self, database, tableName, historyTableName):
        self._db = database
        self.tableName = tableName
        self.historyTableName = historyTableName

        # The first column in each of the tables is the primary key
        # for that table. 
        self.fieldNames = self.getColumnHeads()

        if self.historyTableName:
            self.historyTableFieldString = "(" + ",".join(self.getColumnHeads(self.historyTableName)) + ")"

        self.primaryKey = self.fieldNames[0]
        
    def getColumnHeads(self, table=None):
        """
        Returns the column heads for a specific table.
        """
        if table == None:
            table = self.tableName
        self._db._c.execute("PRAGMA table_info(" + table + ")")
        return [ col[1] for col in self._db._c.fetchall() ]

    def getNextIndex(self, indexName):
        """
        For an integer index, like a repair ID, this runs through the table
        and comes up with the next index to use.
        """
        self._db._c.execute("SELECT {} FROM {}".format(indexName,
                                                       self.tableName))
        IDs = self._db._c.fetchall()

        if len(IDs) == 0:
            return '1'

        # Generate a number one larger than the largest current ID.
        newID = 0
        for ID in IDs:
            newID = max(newID, int(ID[0]))
        newID += 1

        # Return that.
        return str(newID)
            
    def prettyTable(self, heads, rows):
        """
        Calculates column widths for printing a database table.
        """        
        # First calculate the maximum lengths for each column.
        lengths = map(len, heads)
        for row in rows:
            lengths = map(max, lengths, map(len, row))

        # Create a format string for the maximum lengths.
        formatString = ("|{{:^{}}}" * len(heads) + "|").format(*lengths)

        # Print the heads, then the contents.
        headLine = formatString.format(*heads)
        border = "-" * len(headLine)
        print(border)
        print(headLine)
        print(border)

        # Remake the format string right-justified.
        formatString = ("|{{:>{}}}" * len(heads) + "|").format(*lengths)
        for row in rows:
            print(formatString.format(*row))
            print(border)
        
    def tablePrint(self, tableName, field, val):
        """
        Generic table printer.
        """

        # Go get the column names here not later, so not to mess up
        # the database cursor after the SELECT.
        colNames = self.getColumnHeads(tableName)

        # Note that apparently table and field names cannot be parameterized
        # in SQLite execute() statements.
        if val == "*":

            selectString = "SELECT * FROM {}".format(tableName)
            self._db._c.execute(selectString)
        else:

            selectString = "SELECT * FROM {} WHERE {} = ?".format(tableName, field)
            self._db._c.execute(selectString, (val,))

        print(tableName)
        self.prettyTable(colNames, self._db._c.fetchall())

    def show(self, ID="*"):
        self.tablePrint(self.tableName, self.primaryKey, ID)

    def showHistory(self, ID="*"):
        if self.historyTableName != "none":
            self.tablePrint(self.historyTableName, self.primaryKey, ID)

    def insert(self, fieldValues, tableName=None):
        """
        A generic insert method for database tables.  Accepts a tuple of the
        field values as input, and executes an INSERT with them.

        If the primary key is included in the input fieldValues, then
        we check to make sure it is not repeated in the table and
        throw an error if it is.  If it is not included, we try to
        generate a new key value and add the other data to the table.

        Returns the value of the primary key inserted, so you can
        retrieve this record with that key.
        """
        if tableName == None:
            tableName = self.tableName
        
        fieldString = "(" + ",".join(self.fieldNames) + ")"
        questionMarks = "(" + ",".join(["?"] * len(self.fieldNames)) + ")"

        if len(fieldValues) == len(self.fieldNames) - 1:

            # the primary key is not specified -- generate a new one.
            vals = (self.getNextIndex(self.fieldNames[0]),) + fieldValues

        else:

            # The primary key is specified -- check to make sure it's
            # not already in the table. (If it is, use update instead.)
            self._db._c.execute("SELECT " + self.fieldNames[0] + " FROM " +
                                tableName + " WHERE " + self.fieldNames[0] +
                                " = ?", (fieldValues[0],))
            rows = self._db._c.fetchall()
            if rows:
                # Key already exists, don't overwrite
                return None
            
            vals = fieldValues

            
        self._db._c.execute("INSERT INTO " + tableName + fieldString +
                            " VALUES " + questionMarks, vals)
        self._db._conn.commit()

    def insertByHand(self):
        """
        Mostly for testing.  Queries the user for field values.
        """

        fieldValues = []
        for field in self.fieldNames:
            fieldValues.append(raw_input("Give " + field + ": "))

        print(self.tableName + ".insert(" + str(fieldValues) + ")")

        self.insert(fieldValues)

        
    def today(self):
        """
        Returns a properly formatted date for today.
        """
        return(datetime.date.today().isoformat())


    def insertHistoryRecord(self, record, date=None, note=" "):
        """
        Records a database record, with date and note, in the history
        table, if there is one.
        """
        if date == None:
            date = self.today()
        
        if self.historyTableName == None:
            return []

        else:
            
            fieldValues = list(record) + [date, note]
            fieldString = "(" + ",".join(self.getColumnHeads(self.historyTableName)) + ")"
            questionMarks = "(" + ",".join(["?"] * len(fieldValues)) + ")"

            self._db._c.execute("INSERT INTO " + self.historyTableName +
                                fieldString + " VALUES " + questionMarks,
                                fieldValues)
            self._db._conn.commit()

            return fieldValues[0]



    def update(self, inRecord, keyIndex=None):
        """
        Updates the table to the values in fieldValues.  The primary
        key is taken to be the first one in the list, unless another
        name is specified with the keyIndex argument.  Note that the
        primary key is more or less guaranteed to be unique in the
        table, but others aren't, so you are warned.

        """
        if keyIndex == None:
            keyIndex = 0

        conditions = ",".join([a + "='" + b + "'" for a,b in
                               zip(self.fieldNames,inRecord)]) 

        # Now figure out what changed, and change it in the table.
        self._db._c.execute("UPDATE " + self.tableName + " SET " +
                            conditions +
                            " WHERE " + self.fieldNames[keyIndex] + " = ?",
                            (inRecord[keyIndex],))
                
        self._db._conn.commit()

    def setValue(self, keyName, keyValue, valueName, valueValue):
        """
        Finds the record where keyName = keyValue, and changes
        valueName to be valueValue.

        """
        self._db._c.execute("UPDATE " + self.tableName + " SET " +
                            valueName + "=" + valueValue +
                            " WHERE " + keyName + "= ?", (keyValue,))
        
        self._db._conn.commit()

    def setValueDouble(self, firstKeyName, firstKeyValue,
                       secondKeyName, secondKeyValue,
                       valueName, valueValue):
        """
        Same as setValue(), but with two conditions.  This is mostly
        useful for bulbs, that have a serial number and a 'life' value
        to identify them. 
        """
        
        self._db._c.execute("UPDATE " + self.tableName + " SET " +
                            valueName + "=" + valueValue +
                            " WHERE " + firstKeyName + "= ? AND " +
                            secondKeyName + "= ?",
                            (firstKeyValue, secondKeyValue))
        
        self._db._conn.commit()
        
    def getValue(self, keyName, keyValue, valueName):
        """
        Recovers the value of the valueName where the given key has
        the given value.
        """
        self._db._c.execute("SELECT " + valueName + " FROM " +
                            self.tableName + " WHERE " + keyName +
                            " = ?", (keyValue,))

        return self._db._c.fetchone()

    def getAllValues(self, keyName):
        """
        Gets all the values of a given key in the table.
        """
        self._db._c.execute("SELECT " + keyName + " FROM " + self.tableName)

        return [ col[0] for col in self._db._c.fetchall() ]

        
    def getRecord(self, primaryKey):

        self._db._c.execute("SELECT * FROM " + self.tableName +
                            " WHERE " + self.fieldNames[0] +
                            " = ?", (primaryKey,))

        return self._db._c.fetchone()
        
    def recordHistory(self, primaryKey, date, note):

        record = self.getRecord(primaryKey)

        self.insertHistoryRecord(record, date, note)
        
        
class ProjectorSettingsTable(DatabaseTable):

    def __init__(self, db):
        DatabaseTable.__init__(self, db,
                               "ProjectorSettings",
                               "ProjectorSettingsHistory")

    def addProjector(self, projSerial):

        self.insert((projSerial,) + ("0",) * (len(self.fieldValues) - 1))
        

    def setSettings(self, projSerial, settings):

        self.update((projSerial,) + settings, 0)

        
class ProjectorStatus(DatabaseTable):
        
    def __init__(self, db):
        DatabaseTable.__init__(self, db,
                               "ProjectorStatus",
                               "ProjectorStatusHistory")

    def addProjector(self, projSerial, mfgDate, lensType):

        self.insert((projSerial, mfgDate) + ("0",) * 4 +
                    (lensType,) + ("0",) * 3)
        
    def setErrorRecord(self, projSerial, errors):

        self.setValue("projSerial", projSerial, "errorRecord", errors)

    def setNumber(self, projSerial, projNumber):

        self.setValue("projSerial", projSerial, "projNumber", projNumber)

    def getSerialFromNumber(self, projNumber):

        return self.getValue("projNumber", projNumber, "projSerial")
        
    def setHours(self, projSerial, hours):

        self.setValue("projSerial", projSerial, "totalHours", hours)
        
    def setLens(self, projSerial, newLens):

        self.setValue("projSerial", projSerial, "lensType", newLens)

    def setLocation(self, projSerial, newLocation):

        self.setValue("projSerial", projSerial, "onSite", newLocation)
        
    def setRepair(self, projSerial, repairID):

        self.setValue("projSerial", projSerial, "repairID", repairID)
        
    def setStatus(self, projSerial, newStatus):
        
        self.setValue("projSerial", projSerial, "projStatus", newStatus)
        
    def show(self, projectorSerial="*"):
        """
        From the generic table printer, modified because the error record is 
        usually long and complicated, messy.  For a collection of
        projectors we do not print it out, but for a single projector,
        we print it out after the table.
        """
        heads = self.fieldNames

        # Note that apparently table and field names cannot be parameterized
        # in SQLite execute() statements.
        if projectorSerial == "*":

            self._db._c.execute("SELECT * FROM ProjectorStatus")
        else:

            self._db._c.execute("SELECT * FROM ProjectorStatus WHERE projectorSerial = ?", (projectorSerial,))

        rows = self._db._c.fetchall()

        # Set up a container in which to hold the last error record.
        errorRecord = ""
        
        # First calculate the maximum lengths for each column.
        lengths = map(len, heads)
        for row in rows:
            errorRecord = row[-1]
            lengths = map(max, lengths, map(len, row))
            lengths[-1] = len(heads[-1])
            
        # Create a format string for the maximum lengths.
        formatString = ("|{{:^{}}}" * len(heads) + "|").format(*lengths)

        # Print the heads, then the contents.
        headLine = formatString.format(*heads)
        border = "-" * len(headLine)
        print("ProjectorStatus")
        print(border)
        print(headLine)
        print(border)

        # Remake the format string right-justified.
        formatString = ("|{{:>{}}}" * len(heads) + "|").format(*lengths)
        for row in rows:
            listRow = list(row)
            listRow[-1] = "*"
            print(formatString.format(*listRow))
            print(border)

        print("* The error record for the last projector in the table above is this:")
        print(errorRecord)


class ProjectorNumbers(DatabaseTable):
        
    def __init__(self, db):
        DatabaseTable.__init__(self, db,
                               "ProjectorNumbers",
                               None)

    def getSwitch(self, projNumber):
        """
        Returns a tuple of projector number, switch name, and serial port 
        number.
        """
        


class ProjectorRepairs(DatabaseTable):
        
    def __init__(self, db):
        DatabaseTable.__init__(self, db,
                               "ProjectorRepairs",
                               None)

    def newRecord(self, projSerial, repairType, repairedBy, date, repairNote):
        """
        Generate a new unique repairID and then use that to add a new
        repair record.
        """
        # Generate new ID.
        newRepairID = self.getNextIndex("repairID")
        
        # Insert new record.
        self.insert((newRepairID,) +
                    (projSerial, repairType, repairedBy, date, repairNote))

        return newRepairID        
        

class BulbStatus(DatabaseTable):
        
    def __init__(self, db):
        DatabaseTable.__init__(self, db,
                               "BulbStatus",
                               "BulbStatusHistory")


    def addBulb(self, bulbSerial, bulbLife):

        # Generate new bulb ID
        newRepairID = self.getNextIndex("bulbID")

        # Add the data to the table.
        self.insert((bulbID, bulbSerial, bulbLife) + ("0",) * 6)

    def setLampHours(self, bulbID, hours):

        self.setValue("bulbID", bulbID, "lampHours", hours)
        
    def setProjSerial(self, inBulb, inLife, projSerial):

        self.setValueDouble("bulbSerial", inBulb, "bulbLife", inLife,
                            "projSerial", projSerial)

    def setRepair(self, inBulb, inLife, rID):

        self.setValueDouble("bulbSerial", inBulb, "bulbLife", inLife,
                            "repairID", rID)

    def setStatus(self, inBulb, inLife, status):

        self.setValueDouble("bulbSerial", inBulb, "bulbLife", inLife,
                            "bulbStatus", status)

        


class InventoryDatabaseManager:
    """
    The Inventory Database Manager object is the one used by the user.
    Ex/ to work with YurtInventory.db
    dbm = InventoryDatabaseManager('YurtInventory')

    Operations supported:

    Swap projector
    Repair projector
    Ship away for repair
    Return repaired projector to inventory
    Change bulb on projector

    Add projector
    Add bulb or Fix bulb (relamping)

    Record color settings
    Record lamp hours
    Record projector hours
    Record error record

    Projector report
    Bulb report

    """
    def __init__(self,dbFilename):
        self._db = InventoryDatabase(dbFilename)

        self.projSettings = ProjectorSettingsTable(self._db)
        self.projStatus = ProjectorStatus(self._db)
        self.projNumbers = ProjectorNumbers(self._db)
        self.projRepairs = ProjectorRepairs(self._db)
        self.bulbStatus = BulbStatus(self._db)

        
    def swapProjectors(self, projNumber, outSerial, inSerial, tech,
                       repairNote=" ", date=None):
        if date == None:
            date = self._db.today()

        self.projStatus.recordHistory(inSerial, date, repairNote)
        self.projStatus.recordHistory(outSerial, date, repairNote)

        # Change projector serial in position table.
        self.projStatus.setNumber(inSerial, projNumber)
        
        # Change status of inSerial.
        self.projStatus.setStatus(inSerial, "broken")
        
        # Change status of outSerial.
        self.projStatus.setStatus(outSerial, "in use")

        # Record repair -- uninstall and install
        r = self.projRepairs.newRecord(outSerial, "uninstall from " +
                                       str(projNumber), tech,
                                       date, repairNote)
        projStatus.setRepair(outSerial, r)

        r = self.projRepairs.newRecord(inSerial, "install at " +
                                       str(projNumber),  
                                       tech, date, repairNote)
        projStatus.setRepair(inSerial, r)
            

    def repairProjector(self, projSerial, repairType, tech, newStatus=None, 
                        repairNote=" ", date=None):
        if date == None:
            date = self._db.today()

        # Record repair
        r = self.projRepairs.newRecord(projSerial, repairType, tech,
                                       date, repairNote)

        # Change projector status
        self.projStatus.setRepair(projSerial, r)
        if newStatus != None:
            self.projStatus.setStatus(projSerial, newStatus)
            

    def shipAwayProjector(self, projSerial, tech, repairNote=" ", date=None):
        if date == None:
            date = self._db.today()

        self.projStatus.recordHistory(projSerial, date, repairNote)
            
        # Record ship in repair table
        r = self.projRepairs.newRecord(projSerial, "ship", tech,
                                       date, repairNote) 
        
        # Change projector status
        self.projStatus.setLocation(projSerial, "off site")
        self.projStatus.setStatus(projSerial, "broken")
        self.projStatus.setRepair(projSerial, r)

    def receiveRepairedProjector(self, projSerial, repairNote=" ", date=None):
        if date == None:
            date = self._db.today()

        self.projStatus.recordHistory(projSerial, date, repairNote)

        # Record receipt in repair table
        r = self.projRepairs.newRecord(projSerial, "received", tech,
                                       date, repairNote)
        self.projStatus.setRepair(projSerial, r)
        
        # Change projector status
        self.projStatus.setLocation(projSerial, "on site")
        self.projStatus.setStatus(projSerial, "spare")


    def changeBulb(self, projSerial, outBulb, outLife, inBulb, inLife,
                   tech, repairNote=" ", date=None):
        if date == None:
            date = self._db.today()

        self.projStatus.recordHistory(projSerial, date, repairNote)            
            
        # Record repair in repair table
        r = self.projRepairs.newRecord(projSerial, "bulb", tech,
                                       date, repairNote)
        
        # Record repair in projector status table.
        self.projStatus.setRepair(projSerial, r, date, note)

        # Record outgoing bulb status in bulb table -- was the number
        # recorded properly?
        self.bulbStatus.setRepair(outBulb, outLife, r)
        self.bulbStatus.setStatus(outBulb, "broken")
        self.bulbStatus.setProjSerial(outBulb, outLife, "na")

        # Is new bulb in bulb table? Add it if not.
        self.bulbStatus.addBulb(inBulb, inLife, "spare")
        
        # Record ingoing bulb status in bulb table.
        self.bulbStatus.setRepair(inBulb, inLife, r)
        self.bulbStatus.setStatus(inBulb, inLife, "in use")
        self.bulbStatus.setProjSerial(inBulb, inLife, projSerial)


    def swapLens(self, projSerial, newLens, repairNote=" ", date=None):
        if date == None:
            date = self._db.today()

        self.projStatus.recordHistory(projSerial, date, repairNote)
            
        # Record repair in repair table.
        r = self.projRepairs.newRecord(projSerial, "lens", tech,
                                       date, repairNote + " install " + newLens)

        # Record repair in projector status table.
        self.projStatus.setRepair(projSerial, r, date, repairNote)
        self.projStatus.setLens(projSerial, newLens)

    def addProjector(self, projSerial, mfgDate, lens):

        # Add projector to projector status table.
        self.projSettings.addProjector(projSerial, mfgDate)
        self.projStatus.addProjector(projSerial, lensType)
        

    def addBulb(self, bulbSerial, bulbLife, date=None):
        if date == None:
            date = self._db.today()

        # Add bulb to bulb status table.
        self.bulbStatus.addBulb(bulbSerial, bulbLife)
            

    def setSettings(self, projSerial, settings):
        if date == None:
            date = self._db.today()

        if projNumber == None and projSerial == None:
            print("No can do.  I need at least a position or a serial number.")
            return
            
        if projSerial == None:
            projSerial = self.projStatus.getSerialFromNumber(projNumber)
            
        # Change entries in projector settings table.
        self.projSettings.setSettings(projSerial, settings)

    def recordSettingsHistory(self, projNumber=None,
                              projSerial=None, date=None, note=" "):
        if date == None:
            date = self._db.today()
        
        if projNumber == None and projSerial == None:
            print("No can do.  I need at least a position or a serial number.")
            return

        if projSerial == None:
            projSerial = self.projStatus.getSerialFromNumber(projNumber)
            
        self.projSettings.recordHistory(projSerial, date, note)
    
    def recordLampHours(self, hours, bulbID=None,
                        projNumber=None, projSerial=None):

        if bulbID == None:
        
            if projNumber == None and projSerial == None:
                print("No can do. Need at least a position or a serial number.")
                return
                
            if projSerial == None:
                projSerial = self.projStatus.getSerialFromNumber(projNumber)
        
            # Record in bulb status table.
            self.bulbStatus.setLampHours(hours, projSerial=projSerial)

        else:

            self.bulbStatus.setLampHours(hours, bulbID=bulbID)
            
    def recordProjectorHours(self, hours, projNumber=None, projSerial=None):

        if projNumber == None and projSerial == None:
            print("No can do.  I need at least a position or a serial number.")

        if projSerial == None:
            projSerial = self.projStatus.getSerialFromNumber(projNumber)
        
        # Record in projector status table.
        self.projStatus.setHours(projSerial, hours)


    def recordErrorRecord(self, record, projNumber=None, projSerial=None):

        # Record in projector status table.
        self.projStatus.setErrorRecord(projSerial, errors)

    def projectorReport(self, projNumber=None, projSerial=None):

        self.projStatus.show(projSerial)


    def bulbReport(self, bulbID="*"):

        self.bulbStatus.show(bulbID)

######################
        
    def checkInputtedStatus(self, status):
        """
        Input: status
        Output: True if the status is in use, spare or broken, otherwise False
        Purpose: 'Sanitizes' status - if more options become available add to the array
        """
        possibleStatus = ['in use','spare','broken']
        checkStatus = status in possibleStatus 
        if checkStatus == False:
            print("status must be: 'in use','spare', or 'broken'")
            return False
        return True

    def checkInputtedLocation(self, location):
        """
        Input: location
        Output: True if the location is formatted correctly, otherwise false
        Purpose: 'Sanitizes' location
        """
        possibleLocations = ['on site','off site']
        checkLocation = location in possibleLocations
        if checkLocation == False:
            print("location must be: 'on site' or 'off site'")
            return False
        return True

    def checkInputtedLens(self, lens):
        """
        Input: lens
        Output: True if the lens is one of the two choices, othewise False
        Putpose: 'Sanitizes' lens
        """
        lenseTypes = ['short','long']
        checkLens = lens in lenseTypes
        if checkLens == False:
            print("lens must be: 'short' or 'long'")
            return False
        return True

    def checkInputtedDate(self, date):
        """
        Input: date
        Output: True if the data is formmatted correctly, False if the date is formatted incorrectly
        Purpose: 'Sanitizes' date
        """
        splitDate = date.split('-')
        if len(splitDate) is not 3:
            print('Error in Inputted Date')
            return False
        year = splitDate[0]
        month = splitDate[1]
        day = splitDate[2]
        if len(year) == 4 and int(year) > 2000 and len(month) == 2 and int(month) > 0 and int(month) < 12 and len(day) == 2 and int(day) > 0 and int(day) < 32:
            return True
        print('Error in Inputted Date')
        return False

    def checkInputtedRepair(self, repair):
        """
        Input: repair
        Output: True if the repair is one of the choices, False if not
        Putpose: 'Sanitizes' repair
        """
        possibleRepairs = ['bulb','install','uninstall','ship','fixed','recieved']
        checkRepair = repair in possibleRepairs
        if checkRepair == False:
            print("repairType can be: bulb, install, uninstall, or ship")
            return False
        return True       


    def reLampBulb(self, oldBulbID, bulbSerial, newStatus, newProjSerial, date):
        """
        Input: oldBulbID (try to query database to find it)
               bulbSerial (serial number of bulb or unknown)
               newStatus (in use, spare) most likely spare
               newProjSerial (if it is in use, specidy which projector it is now in, otherwise na)
               date (today's date year-month-day Ex/ 2016-01-05 is January 5, 2016)
        Output: None
        Purpose: Creates a new row in the bulb current status table. The bulb serial number
                 remians the same, but its life attribute increases by 1
        """
        if self.checkInputtedStatus(newStatus) == False or self.checkInputtedDate(date) == False:
            return
        oldLife = self._db.getBulbLife(oldBulbID)
        bulbLife = str(int(oldLife) + 1)
        self.newBulb(bulbSerial, bulbLife, newStatus, newProjSerial, date)
        

    def runDemo(self):
        """
        Generic Demo, can only be called on a db named demo.db (also a good way to test changes in methods)
        """
        if self._db.getName() is not 'demo':
            print('only works for a demo database file')
            return
        keepGoing = input("Continue?")

        print('Lets add a new Projector ABC, that is a spare')
        self.newProjector('ABC','spare','on site','na','2016-01-01','mfgDate','long','cs','cs','cs','cs','cs','cs','cs','cs')    
        keepGoing = input("Continue?")
        
        print('Lets add a new Projector ABD, that is in use in position 1')
        self.newProjector('ABD','in use','on site','1','2016-01-01','mfgDate','long','cs','cs','cs','cs','cs','cs','cs','cs')
        keepGoing = input("Continue?")
        
        print('Since Projector ABD is installed, we need to add a new bulb')
        self.newBulb('unknown','0','in use','ABD','2016-01-01')
        keepGoing = input("Continue?")

        print('Lets also create a new bulb as a spare')
        self.newBulb('b123','0','spare','na','2016-01-01')
        keepGoing = input("Continue?")

        print('Now lets install projector ABC')
        self.installProjector('ABC','2','2016-01-02','palak','installed projector')
        keepGoing = input("Continue?")

        print("Remember to put bulb inside the projector")
        self.installBulb('2','ABC','2016-01-02','palak','installed b123 into ABC')
        keepGoing = input("Continue?")

        print('Unfortunately Projector ABD breaks')
        self.uninstallProjector('ABD','broken','on site','2016-01-02','palak','aww man :(')
        keepGoing = input("Continue?")
        
        print('Now we need to ship ABD do Taiwan to get it fixed')
        self.shipProjector('ABD','broken','2016-01-03','Taiwan','shipped')
        keepGoing = input("Continue?")

        print('Projector ABD returns from Taiwan fixed!')
        self.recievedProjector('ABD','spare','2016-01-05','palak','it works!')
        keepGoing = input("Continue?")

        print('okay, thats enough about ABD, lets say the bulb breaks in ABC')
        self.uninstallBulb('2','ABC','broken','2016-01-06','palak','shattered')
        keepGoing = input("Continue?")

        print('The bulb that was in ABC, not gets reLamped')
        self.reLampBulb('2','b123','spare','na','2016-01-08')
        keepGoing = input("Continue?")

        print('Time to install the bulb back into ABC')
        self.installBulb('3','ABC','2016-01-10','palak','it works now!')
        keepGoing = input("Continue?")
    
