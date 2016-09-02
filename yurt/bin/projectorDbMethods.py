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
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorSettings(projectorSerial TEXT, mfgDate TEXT, redOffset TEXT, greenOffset TEXT, blueOffset TEXT, redGain TEXT, greenGain TEXT, blueGain TEXT, colorTemp TEXT, gamma TEXT)')

    def createProjectorSettingsHistoryTable(self):
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorSettingsHistory(projectorSerial TEXT, mfgDate TEXT, redOffset TEXT, greenOffset TEXT, blueOffset TEXT, redGain TEXT, greenGain TEXT, blueGain TEXT, colorTemp TEXT, gamma TEXT, dateRecorded TEXT, note TEXT)')

    def createProjectorStatusTable(self):
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorStatus(projectorSerial TEXT, projNumber TEXT, totalHours TEXT, projStatus TEXT, onSite TEXT, lensType TEXT, dateIn TEXT, repairID TEXT, errorRecord TEXT)')

    def createProjectorStatusHistoryTable(self):
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorStatusHistory(projectorSerial TEXT, projNumber TEXT, totalHours TEXT, projStatus TEXT, onSite TEXT, lensType TEXT, dateIn TEXT, repairID TEXT, errorRecord TEXT, dateRecorded TEXT, note TEXT)')

    def createProjectorRepairsTable(self):
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorRepairs(repairID TEXT, projectorSerial TEXT, repairDate TEXT, repairType TEXT, repairedBy TEXT, repairNote TEXT)')

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
    def __init__(self, database, tableName, historyTableName, autoHistory):
        self._db = database
        self.tableName = tableName
        self.historyTableName = historyTableName
        self.autoHistory = autoHistory

        # The first column in each of the tables is the primary key
        # for that table. 
        self.fieldNames = self.getColumnHeads()
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


    def updatePrep(self, fieldValues, keyIndex=None, note="",
                   date=None, recordHistory=False):
        """
        This method looks for a record that matches the first value in the
        input fieldValues, and returns a tuple of the matching row.  If more
        than one row matches, or if no rows match, the return is empty.

        Use this method in writing an update() method in the subclass, 
        especially where the existing data will be recorded in a history
        table, e.g.:

          def update(vals):
            row = self.updatePrep(vals)
            if row:
              save history
              make insertions
        """
        if date == None:
            date = self.today()

        if keyIndex == None:
            keyIndex = 0
            
        key = self.fieldNames[keyIndex]

        old = self._db._c.execute("SELECT * FROM " + self.tableName +
                                  " WHERE " + key + " = ?",
                                  (fieldValues[keyIndex],))
        rows = self._db._c.fetchall()

        if len(rows) > 1:
            rows = []
            print("Err: Too many matches")

        # If there is a return here, we're probably going to change this
        # table entry.  Record the current state in the history table,
        # if there is one.
        if rows and (self.autoHistory or recordHistory):
            self.recordHistory(rows[0], date, note)

        # Return the original value of the row to be updated.
        return rows[0]

    def recordHistory(self, record, date=None, note=" "):
        """
        Records a database record, with date and note, in the history
        table, if there is one.
        """

        if self.historyTableName == "none":
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



            
    def update(self, inRecord, keyIndex=None, note="", date=None,
               recordHistory=False):
        """
        Updates the table to the values in fieldValues.  The primary
        key is taken to be the first one in the list, unless another
        name is specified with the indexName argument.  Note that the
        primary key is more or less guaranteed to be unique in the
        table, but others aren't, so you are warned.

        This method also records a note and date in the history table,
        if there is a history table and autohistory is turned on.
        """
        if keyIndex == None:
            keyIndex = 0
        
        if date == None:
            date = self.today()
        
        # Get the row of the table to be updated, and record it in the
        # history, if appropriate.
        oldRecord = self.updatePrep(inRecord, recordHistory=recordHistory)

        # Now figure out what changed, and change it in the table.
        for head,new,old in zip(self.fieldNames, inRecord, oldRecord):

            if new != old:
                
                self._db._c.execute("UPDATE " + self.tableName + " SET " +
                                    head + " = ? WHERE " +
                                    self.fieldNames[keyIndex] + " = ?",
                                    (new, oldRecord[0]))
                
                self._db._conn.commit()
    
        
class ProjectorSettingsTable(DatabaseTable):

    def __init__(self, db):
        DatabaseTable.__init__(self, db,
                               "ProjectorSettings",
                               "ProjectorSettingsHistory",
                               False)

    def addProjector(self, projSerial, mfgDate):
        pass

    def setSettings(self, projNumber=None, projSerial=None):
        pass

    def recordSettings(self, projNumber=None, projSerial=None):
        pass

        
class ProjectorStatus(DatabaseTable):
        
    def __init__(self, db):
        DatabaseTable.__init__(self, db,
                               "ProjectorStatus",
                               "ProjectorStatusHistory",
                               True)
        
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
                               "none",
                               False)
        
class ProjectorRepairs(DatabaseTable):
        
    def __init__(self, db):
        DatabaseTable.__init__(self, db,
                               "ProjectorRepairs",
                               "none",
                               False)


class BulbStatus(DatabaseTable):
        
    def __init__(self, db):
        DatabaseTable.__init__(self, db,
                               "BulbStatus",
                               "BulbStatusHistory",
                               True)



#######################

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

        self.projSettings = self._db.ProjectorSettingsTable(p)
        self.projStatus = self._db.ProjectorStatus(p)
        self.projNumbers = self._db.ProjectorNumbers(p)
        self.projRepairs = self._db.ProjectorRepairs(p)
        self.bulbStatus = self._db.BulbStatus(p)

        
    def swapProjectors(self, projNumber, outSerial, inSerial, tech,
                       repairNote=" ", date=None):
        if date == None:
            date = self._db.today()

        self.projStatus.record(inSerial, date, repairNote)
        self.projStatus.record(outSerial, date, repairNote)

        # Change projector serial in position table.
        self.projNumbers.setNumber(projNumber, inSerial)
        
        # Change status of inSerial.
        self.projStatus.setStatus(inSerial, "broken")
        
        # Change status of outSerial.
        self.projStatus.setStatus(outSerial, "in use")

        # Record repair -- uninstall and install
        r = self.projRepairs.newRecord(outSerial, "uninstall from " +
                                       str(projNumber), tech,
                                       repairNote, date)
        projStatus.setRepair(outSerial, r)

        r = self.projRepairs.newRecord(inSerial, "install at " +
                                       str(projNumber),  
                                       tech, repairNote, date)
        projStatus.setRepair(inSerial, r)
            

    def repairProjector(self, projSerial, repairType, tech, newStatus=None, 
                        repairNote=" ", date=None):
        if date == None:
            date = self._db.today()

        # Record repair
        r = self.projRepairs.newRecord(projSerial, repairType, tech,
                                       repairNote, date)

        # Change projector status
        self.projStatus.setRepair(projSerial, r)
        if newStatus != None:
            self.projStatus.setStatus(projSerial, newStatus)
            

    def shipAwayProjector(self, projSerial, tech, repairNote=" ", date=None):
        if date == None:
            date = self._db.today()

        self.projStatus.record(projSerial, date, repairNote)
            
        # Record ship in repair table
        r = self.projRepairs.newRecord(projSerial, "ship", tech,
                                       repairNote, date) 
        
        # Change projector status
        self.projStatus.setLocation(projSerial, "off site")
        self.projStatus.setStatus(projSerial, "broken")
        self.projStatus.setRepair(projSerial, r)

    def receiveRepairedProjector(self, projSerial, repairNote=" ", date=None):
        if date == None:
            date = self._db.today()

        self.projStatus.record(projSerial, date, repairNote)

        # Record receipt in repair table
        r = self.projRepairs.newRecord(projSerial, "received", tech,
                                       repairNote, date)
        self.projStatus.setRepair(projSerial, r)
        
        # Change projector status
        self.projStatus.setLocation(projSerial, "on site")
        self.projStatus.setStatus(projSerial, "spare")


    def changeBulb(self, projSerial, outBulb, outLife, inBulb, inLife,
                   tech, repairNote=" ", date=None):
        if date == None:
            date = self._db.today()

        self.projStatus.record(projSerial, date, repairNote)            
            
        # Record repair in repair table
        r = self.projRepairs.newRecord(projSerial, "bulb", tech,
                                       repairNote, date)
        
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

        self.projStatus.record(projSerial, date, repairNote)
            
        # Record repair in repair table.
        r = self.projRepairs.newRecord(projSerial, "lens", tech,
                                       repairNote + " install " + newLens, date)

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
            

    def setSettings(self, projNumber=None, projSerial=None, date=None):
        if date == None:
            date = self._db.today()

        if projNumber == None and projSerial == None:
            print("No can do.  I need at least a position or a serial number.")

        # Change entries in projector settings table.
        self.projSettings.setSettings(projNumber=projNumber,
                                      projSerial=projSerial, settings)

    def recordSettingsHistory(self, projNumber=None,
                                   projSerial=None, date=None):
        if date == None:
            date = self._db.today()
        
        self.projSettings.recordSettings(projNumber=projNumber,
                                         projSerial=projSerial, date)
    
    def recordLampHours(self, hours, bulbID=None,
                        projNumber=None, projSerial=None):

        if bulbID == None:
        
            if projNumber == None and projSerial == None:
                print("No can do. Need at least a position or a serial number.")

            if projSerial == None:
                projSerial = self.projNumbers.getSerial(projNumber)
        
            # Record in bulb status table.
            self.bulbStatus.setLampHours(hours, projSerial=projSerial)

        else:

            self.bulbStatus.setLampHours(hours, bulbID=bulbID)
            
    def recordProjectorHours(self, hours, projNumber=None, projSerial=None):

        if projNumber == None and projSerial == None:
            print("No can do.  I need at least a position or a serial number.")

        if projSerial == None:
            projSerial = self.projNumbers.getSerial(projNumber)
        
        # Record in projector status table.
        self.projStatus.setHours(projSerial, hours)


    def recordErrorRecord(self, record, projNumber=None, projSerial=None):

        # Record in projector status table.
        self.projStatus.setErrorRecord(projSerial, errors)

    def projectorReport(self, projNumber=None, projSerial=None):

        self.projStatus.show(projSerial)


    def bulbReport(self, bulbID="*"):

        self.bulbStatus.show(bulbID)


##############################


        
    def updateLampHoursInTable(self, bulbID, lampHours):
        """
        Input: bulbID, lampHours
        Output: None
        Purpose: update the lampHours in the Bulb Current Status Table
        """
        self._c.execute("UPDATE BulbStatus SET lampHours = ? WHERE bulbID = ?",(lampHours,bulbID,))
        self._conn.commit()

    def insertIntoBulbStatusHistoryTable(self,bulbID, bulbSerial, bulbLife, bulbStatus, projSerial, dateIn, dateOut, lampHours, bulbHistNote):
        """
        Input: bulbID,
               bulbSerial (bulb serial number or unknown)
               bulbLife (0 if it is on its first life)
               bulbStatus (in use, broken, spare at the time)
               projSerial (projector bulb was installed in, 'na' if it was spare or broken)
               dateIn (date projector was put in this status)
               dateOut (date projector was removed from this status)
               lampHours (hours on the bulb at the time of its removal)
               bulbHistNote (miscellaneous notes)
        Output: None
        Purpose: Keep a log of everything that happens to the bulbs
               
        """
        self._c.execute("INSERT INTO BulbStatusHistory(bulbID, bulbSerial, bulbLife, bulbStatus, projectorSerial, dateIn, dateOut, lampHours, bulbHistNote) VALUES (?,?,?,?,?,?,?,?,?)",
                 (bulbID, bulbSerial, bulbLife, bulbStatus, projSerial, dateIn, dateOut, lampHours, bulbHistNote))
        self._conn.commit()

    def getBulbID(self, bulbSerial, projectorSerial):
        """
        Input: bulb Serial Number or 'unknown'
               projectorSerial Number or 'unknown'
        Output: bulbID or Error String
        Purpose: Ideally query the database to find out the bulbID, this 
               method is there to help if you know the bulb serial number 
               or the current projector serial number
        """
        if bulbSerial is not 'unknown':
            self._c.execute("SELECT bulbID FROM BulbStatus WHERE bulbSerial = ?",(bulbSerial,))
            rowRaw = self._c.fetchall()
            row = str(rowRaw.pop())
            bulbID = self.fixString(row)
            return bulbID
        
        if projectorSerial is not 'unknown':
            self._c.execute("SELECT bulbID FROM BulbStatus WHERE projectorSerial = ?",(projSerial,))
            rowRaw = self._c.fetchall()
            row = str(rowRaw[0])
            bulbID = self.fixString(row)
            return bulbID
        errorMessage = 'Please look through database to find bulbID'
        return errorMessage

    def getBulbLife(self,bulbID):
        """
        Input: bulbID
        Output: Current Life of the bulb (amount of times it has been relamped)
        Purpose: Queries the database for the reLamped method to find out how many times a certain bulb has
                 been reLamped
        """
        self._c.execute("SELECT bulbLife FROM BulbStatus WHERE bulbID = ?",(bulbID,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw.pop())
        bulbLife = self.fixString(row)
        return bulbLife

    def insertIntoProjectorSettingsTable(self,serial, mfgDate, date, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma):
        """
        Input: serial number of the projector
               mfgDate manufacturing date of the projector
               lens (short or long)
               Color Settings: red offset, green offset, blue offset
                               red gain, green gain, blue gain, colorTemp, gamma
        Output: None
        Purpose: This method is only used when a brand new projector is added to the sytem, all
                 of the values are static
        """
        self._c.execute("INSERT INTO ProjectorSettings(projectorSerial, mfgDate, lastUpdated, lensType, redOffset, greenOffset, blueOffset, redGain, greenGain, blueGain, colorTemp, gamma) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (serial, mfgDate, date, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma))
        self._conn.commit()

    def updateProjectorSettingsTable(self,serial, updatedOn, newLens, NewrOff, NewgOff, NewbOff, NewrGain, NewgGain, NewbGain, newTemp, newGamma, note):
        """
        Input: serial number of the projector
               updatedOn date today
               Color settings - changes if there are any, 'none' if there isn't one
               note - miscellaneous notes
        Output: None
        Purpose: Updates the projectors table if there is a change to its color settings, stores changes in a history table
        """

        #prevDateIn
        self._c.execute("SELECT lastUpdated FROM ProjectorSettings WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        prevDateIn = self.fixString(row)

        #oldLens
        self._c.execute("SELECT lensType FROM ProjectorSettings WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldLens = self.fixString(row)

        #oldRoff
        self._c.execute("SELECT redOffset FROM ProjectorSettings WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldRoff = self.fixString(row)

         #oldGoff
        self._c.execute("SELECT greenOffset FROM ProjectorSettings WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldGoff = self.fixString(row)
        
         #oldBoff
        self._c.execute("SELECT blueOffset FROM ProjectorSettings WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldBoff = self.fixString(row)
        
         #oldRgain
        self._c.execute("SELECT redGain FROM ProjectorSettings WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldRgain = self.fixString(row)
        
         #oldGgain
        self._c.execute("SELECT greenGain FROM ProjectorSettings WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldGgain = self.fixString(row)
        
         #oldBgain
        self._c.execute("SELECT blueGain FROM ProjectorSettings WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldBgain = self.fixString(row)
        
         #oldTemp
        self._c.execute("SELECT colorTemp FROM ProjectorSettings WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldTemp = self.fixString(row)
        
         #oldGamma
        self._c.execute("SELECT gamma FROM ProjectorSettings WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldGamma = self.fixString(row)
        self.insertIntoProjetorSettingsHistoryTable(serial, prevDateIn, updatedOn, oldLens, oldRoff, oldGoff, oldBoff, oldRgain, oldGgain, oldBgain, oldTemp, oldGamma, note)

        if updatedOn is not 'none':
            self._c.execute("UPDATE ProjectorSettings SET lastUpdated = ? WHERE projector_serial = ?",(updatedOn,serial,))
            self._conn.commit()
        if newLens is not 'none':
            self._c.execute("UPDATE ProjectorSettings SET lensType = ? WHERE projector_serial = ?",(newLens, serial,))
            self._conn.commit()
        if NewrOff is not 'none':
            self._c.execute("UPDATE ProjectorSettings SET redOffset = ? WHERE projector_serial = ?",(NewrOff,serial,))
            self._conn.commit()
        if NewgOff is not 'none':
            self._c.execute("UPDATE ProjectorSettings SET greenOffset = ? WHERE projector_serial = ?",(NewgOff,serial,))
            self._conn.commit()
        if NewbOff is not 'none':
            self._c.execute("UPDATE ProjectorSettings SET blueOffset = ? WHERE projector_serial = ?",(NewbOff,serial,))
            self._conn.commit()
        if NewrGain is not 'none':
            self._c.execute("UPDATE ProjectorSettings SET redGain = ? WHERE projector_serial = ?",(NewrGain,serial,))
            self._conn.commit()
        if NewgGain is not 'none':
            self._c.execute("UPDATE ProjectorSettings SET greenGain = ? WHERE projector_serial = ?",(NewgGain,serial,))
            self._conn.commit()
        if NewbGain is not 'none':
            self._c.execute("UPDATE ProjectorSettings SET blueGain = ? WHERE projector_serial = ?",(NewbGain,serial,))
            self._conn.commit()
        if newTemp is not 'none':
            self._c.execute("UPDATE ProjectorSettings SET colorTemp = ? WHERE projector_serial = ?",(newTemp,serial,))
            self._conn.commit()
        if newGamma is not 'none':
            self._c.execute("UPDATE ProjectorSettings SET gamma = ? WHERE projector_serial = ?",(newGamma,serial,))
            self._conn.commit()
        
    def insertIntoProjectorSettingsHistoryTable(self,serial, dateIn, dateOut, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma, note):
        """
        Input: serial number of the projector
               date into the old settings, date out of the old settings
               color settings
               note (miscellaneous notes)
        Output: None
        Purpose: Keep log of changes to the projector's color settings
        """
        self._c.execute("INSERT INTO ProjectorSettingsHistory(projectorSerial, dateIn, dateOut, lensType, redOffset, greenOffset, blueOffset, redGain, greenGain, blueGain, colorTemp, gamma, settingsNote) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (serial, dateIn, dateOut, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma, note))
        self._conn.commit()

    def insertIntoProjectorStatusTable(self,serial, status, onSite, projNumber, dateIn, totalHours, errorRec):
        """
        Input: serial number of the projector
               status (in use, broken, spare)
               location (on site or off site)
               position (which position the projector is located in the YURT or 'na' if broken or spare)
               dateIn (date projector was placed in the current status)
               totalHours (number of hours the projector has been in use)
        Output: None
        Purpose: Insert rows into the projector current status table
        
        """
        self._c.execute("INSERT INTO ProjectorStatus(projectorSerial, projNumber, dateIn, totalHours, projStatus, onSite, errorRecord) VALUES (?,?,?,?,?,?,?)",
                  (serial, status, onSite, projNumber, dateIn, totalHours, errorRec))
        self._conn.commit()

    def updateProjectorStatusTable(self,serial, status, location, position, dateIn, notes):
        """
        Input: serial number of the projector
               new status (in use, broken, spare)
               new location (on site or off site)
               new position (location in the YURT or 'na' if broken or spare)
               dateIn (date the projector was placed in this new status)
               notes (miscellaneous notes
        Output: None
        Purpose: update a row in the projector current status table as well as take the previous
                 status and update the projector history table
        
        """
        #Oldlocation
        self._c.execute("SELECT onScreen FROM ProjectorStatus WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldLocation = self.fixString(row)
        
        #Oldstatus
        self._c.execute("SELECT projStatus FROM ProjectorStatus WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldStatus = self.fixString(row)
        
        #dateIn Previous Status
        self._c.execute("SELECT dateIn FROM ProjectorStatus WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        dateInPrevStatus = self.fixString(row)
        
        #oldPosition
        self._c.execute("SELECT projNumber FROM ProjectorStatus WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldPosition = self.fixString(row)
        
        #totalHours
        self._c.execute("SELECT totalHours FROM ProjectorStatus WHERE projector_serial = ?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        totalHours = self.fixString(row)    

        self.insertIntoProjectorStatusHistoryTable(serial, oldPosition, dateInPrevStatus, dateIn, totalHours, oldStatus, oldLocation, notes) 

        if status is not 'none':
            self._c.execute("UPDATE ProjectorStatus SET projStatus = ? WHERE projector_serial = ?",(status,serial,))
            self._conn.commit()
        if location is not 'none':
            self._c.execute("UPDATE ProjectorStatus SET onScreen = ? WHERE projector_serial = ?",(location,serial,))
            self._conn.commit()
        if position is not 'none':
            self._c.execute("UPDATE ProjectorStatus SET projNumber = ? WHERE projector_serial = ?",(position,serial,))
            self._conn.commit()
        if dateIn is not 'none':
            self._c.execute("UPDATE ProjectorStatus SET dateIn = ? WHERE projector_serial = ?",(dateIn,serial,))
            self._conn.commit()
            
    def updateTotalHoursInTable(self,serial, totalHours):
        """
        Input: serial number of the projector
               totalHours of the projector
        Output: None
        Purpose: update the total hours on a projector in the current status table
        """
        self._c.execute("UPDATE ProjectorStatus SET totalHours = ? WHERE projectorSerial = ?",(totalHours,serial,))
        self._conn.commit()
        
    def insertIntoProjectorStatusHistoryTable(self,serial, position, dateIn, dateOut, totalHours, status, location, notes):
        """
        Input: serial number of the projector
               old status (in use, broken, spare)
               old location (on site or off site)
               old position (index of position in the YURT or na if it was broken/spare)
               dateIn (date placed in this status)
               dateOut (date removed from this status)
               totalHours (hours projector had been used up until this point in time)
               notes (miscellaneous notes)
        Output: None
        Purpose: Keep a log of all of the things that happen to the projector
        """
        self._c.execute("INSERT INTO ProjectorStatusHistory(projectorSerial, projNumber, dateIn, dateOut, totalHours, projStatus, onSite, projHistNote) VALUES (?,?,?,?,?,?,?,?)",
                  (serial, position, dateIn, dateOut, totalHours, status, location, notes))
        self._conn.commit()

    def insertIntoProjectorRepairTable(self,projSerial, date, repair, repairedBy, note):
        """
        Input: serial number of the projector,
               date of repair (year-month-date) Ex/ 2016-01-05 is January 5, 2016
               repair type (install, uninstall, bulb, board, ship)
               repaired By (who repaired projector),
               note (miscellaneous notes)
        Output: None
        Purpose: Logging a new repair 
        """
        repairIndex = self.getRepairIndex()
        self._c.execute("INSERT INTO ProjectorRepairs(repairID, projector_serial, repairDate, repairType, repairedBy, repairNote) VALUES (?,?,?,?,?,?)",
                 (repairIndex, projSerial, date, repair, repairedBy, note))
        self._conn.commit()           

    def insertIntoProjectorPositions(self,position,location,serialSwitch,serialPort,server,display):
        """
        Input: position (number index that represents a position in the YURT)
               location (wall, door, ceiling) location of the position
               Attributes unique to a position:
               serialSwitch
               serialPort
               projServer
               projDisplay
        Output: None
        Purpose: Solely for the initial buildup of the ProjectorPositions Table. The ProjectorPositions Table is not modified
                 once all of the rows have been inserted into the table.
        
        """
        self._c.execute("INSERT INTO ProjectorPositions(projNumber, onScreen, serialSwitch, serialPort, projServer, projDisplay) VALUES (?,?,?,?,?,?)",
                 (position, location, serialSwitch, serialPort, server, display))
        self._conn.commit()           

    def getProjectorPositionData(self, projNumber):

        self._c.execute("SELECT projectorSerial,serialSwitch,serialPort FROM ProjectorPositions WHERE projNumber = ?", (projNumber,))

    def recordErrorRecord(self, projSerial, errorRecord):

        # We don't need to record the error record history, since it
        # is a history.
        self._c.execute("UPDATE ProjectorStatus SET errorRecord = ? WHERE projectorSerial = ?", (errorRecord, projSerial))
        

class aInventoryDatabaseManager:
    """
    The Inventory Database Manager object is the one used by the user.
    Ex/ to work with YurtInventory.db
    dbm = InventoryDatabaseManager('YurtInventory')
    """

    def __init__(self,dbFilename):
        self._db = InventoryDatabase(dbFilename)


    def getProjectorPositionData(self, projNumber):
        return self._db.getProjectorPositionData(projNumber)

    def recordErrorRecord(self, projSerial, errorRecord):
        return self._db.recordErrorRecord(projSerial, errorRecord)

    def getErrorRecord(self, projSerial):
        return self._db.getErrorRecord(projSerial)
        
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

    def newProjector(self, serial, status, location, position, date, mfgDate, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma):
        """
        Input: serial number
               status (in Use, Spare, Broken),
               onSite (on site or off site),
               manufacturing date, 
               Color settings: Red Offset, Green Offset, Blue Offset, Red Gain, Green Gain, Blue Gain, Temp, Gamma
        Output: None
        Purpose: Adding a new projector to the system, if the projector is in use right away,
                 this method will prompt two more inputs: repairedBy and repairNotes to add to the
                 Projector Repairs Log
        """
        if self.checkInputtedStatus(status) == False or self.checkInputtedLocation(location) == False or self.checkInputtedLens(lens) == False or self.checkInputtedDate(date) == False:
            return
        
        self._db.insertIntoProjectorSettingsTable(serial, mfgDate, date, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma)
        totalHours = 0
        self._db.insertIntoProjectorStatusTable(serial, position, date, status, location, totalHours)

        if status == 'in use':
            repairedBy = input("Who installed the projector?")
            notes = input("Any Notes?")
            self._db.insertIntoProjectorRepairTable(serial,  date, 'install', repairedBy, notes)

    def uninstallProjector(self, serial, newStatus, newLocation, date, uninstalledBy, note):
        """
        Input: serial number of the projector
               newStatus of the projector (spare or broken, most likeley broken)
               newLocation of the projector (on site or off site)
               date (date of uninstallation year-month-day Ex/ 2016-01-05 is January 5, 2016
               uninstalledBy (who uninstalled the projector)
               note (Miscellaneous note)
        Output: None
        Purpose: Uninstalling a projector updates the projector's current status and creates a
                 repair record. Updating the current status will automatically change the projector
                 history table.
        """
        if self.checkInputtedStatus(newStatus) == False or self.checkInputtedLocation(newLocation) == False or self.checkInputtedDate(date) == False:
            return
        self._db.updateProjectorStatusTable(serial, 'na', date, newStatus, newLocation)
        self._db.insertIntoProjectorRepairTable(serial,date,'uninstall',uninstalledBy, note)
            
    def installProjector(self, serial, position, date, installedBy, note):
        """
        Input: serial number of the projector
               position the projector is installed to (index)
               date of the installation
               installedBy (who installed it)
               note (miscellaneous notes)
        Output: None
        Purpose: This method, unlike newProjector() assumes the projector is already in the system
                 and is now being installed. This method updates the status of the projector and
                 logs the installation in the Projector Repair Table.
        """
        if self.checkInputtedDate(date) == False:
            return
        self._db.updateProjectorStatusTable(serial,position,date,'in use','on site',note)
        self._db.insertIntoProjectorRepairTable(serial, date, 'install', installedBy, note)

    def shipProjector(self, serial, status, date, whereTo, note):
        """
        Input: serial number of the projector
               status (in use, spare, broken) - most likely broken
               date today (year-month-day Ex/ 2016-01-05 is January 5, 2016)
               whereTo - where the projector is being shipped to
               note (miscellaneous notes) 
        Output: None
        Purpose: Updates the current status of the projector if it is shipped off-site,
                 most likeley for repairs. Adds this to the projector repair table.
        """
        if self.checkInputtedStatus(status) == False or self.checkInputtedDate(date) == False:
            return
        self._db.updateProjectorStatusTable(serial, 'na',date,status,'off site',note)
        self._db.insertIntoProjectorRepairTable(serial, date, 'ship',whereTo, note)

    def recievedProjector(self, serial,status,date,enteredBy, note):
        """
        Input: serial number of the projector
               status (in use, spare, broken) - most likely broken
               date today (year-month-day Ex/ 2016-01-05 is January 5, 2016)
               enteredBy (whoever is responsible for recieving the Projector)
               note (miscellaneous notes) Ex/ Recieved from Taiwan
        Output: None
        Purpose: Updates the current status and repair record of the projector when it is recieved. 
        """
        if self.checkInputtedStatus(status) == False or self.checkInputtedDate(date) == False:
            return
        self._db.updateProjectorStatusTable(serial, 'na',date,status, 'on site',note)
        self._db.insertIntoProjectorRepairTable(serial,date,'recieved',enteredBy,note)

    def fixedProjector(self, serial, date, fixedBy, note):
        """
        Input: serial number of projector
               date today (year-month-day Ex/ 2016-01-05 is January 5, 2016)
               fixedBy (whoever fixed the projector)
               note (miscellaneous notes)
        Output: None
        Purpose: Udates current status of projector when it is fixed. Logs it into the
                 Projector Repairs Table.
        
        """
        if self.checkInputtedDate(date) == False:
            return
        self._db.updateProjectorStatusTable(serial,'na',date,'spare','on site',note)
        self._db.insertIntoProjectorRepairTable(serial, date, 'fixed', fixedBy, note)

    def projectorBreaks(self, serial, date, note):
        """
        Input: serial number of the projector
               date the projector breaks (year-month-day Ex/ 2016-01-05 is January 5, 2016)
               note (miscellaneous notes)
        Output: None
        Purpose: Updates the current status of projector when it breaks. 
        """
        if self.checkInputtedDate(date) == False:
            return
        self._db.updateProjectorStatusTable(serial, 'na', date, 'broken', 'on site', note)

    def updateProjectorSettings(self, serial, date, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma, note):
        """
        Input: serial number of the projector
               date today (year-month-day Ex/ 2016-01-05 is January 5, 2016)
               lens (new lensType)
               new Color Settings
               note
        Output: None
        Purpose: on user's call it will update the projector's color settings, and log the old settings in a history table
       
        """
        if self.checkInputtedLens(lens) == False or self.checkInputtedDate(date) == False:
            return
        self._db.updateProjectorSettingsTable(serial, date, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma, note)


    def newRepair(self, serial, date, repair, repairedBy, note):
        """
        Input: serial number of the projector
               date of repair (year-month-day Ex/ 2016-01-05 is January 5, 2016)
               repairedBy, note
        Output: None
        Purpose: This method is for generic repairs such as board repairs. This method is not
                 for bulb repairs. 
        """
        if self.checkInputtedRepair(repair) == False or self.checkInputtedDate(date) == False:
            return
        self._db.insertIntoProjectorRepairTable(serial, date, repair, repairedBy, note)

    def newBulb(self, bulbSerial, bulbLife, status, projSerial, date):
        """
        Input: serial number of the bulb (unknown if not known)
               status (in use, spare, broken),
               projSerial (serial number of the projector, na if bulb is spare or broken)
               dateIn (today's date year-month-day Ex/ 2016-01-05 is January 5, 2016),
               your name
        Output: None
        Purpose: Adding a new bulb to the system, if the bulb is being installed, update projector repairs
        """
        if self.checkInputtedStatus(status) == False or self.checkInputtedDate(date) == False:
            return

        lampHours = 0
        
        self._db.insertIntoBulbStatusTable(bulbSerial, bulbLife, status, projSerial, date, lampHours)

        if status == 'in use':
            repairedBy = input("Who installed the bulb into the Projector?")
            note = input("Any Notes?")
            self._db.insertIntoProjectorRepairTable(projSerial,date,'bulb',repairedBy,note)

    def uninstallBulb(self, bulbID, projSerial, newStatus, date, uninstalledBy, note):
        """
        Input: bulbID (try to query database to find it, if not type idk - should work)
               projSerial (serial number of the projector)
               newStatus (broken or spare) of the bulb - most likely broken
               date (today's date year-month-day Ex/ 2016-01-05 is January 5, 2016)
               uninstalledBy (whoever uninstalled the bulb)
               note (Miscellaneous notes)
        Output: None
        Purpose: Updating status of the bulb that is being uninstalled and adding a repair record
        """
        if self.checkInputtedStatus(newStatus) == False or self.checkInputtedDate(date) == False:
            return
        if bulbID == 'idk':
            bulbID = self._db.getBulbID('unknown',projSerial)
        self._db.updateBulbStatusTable(bulbID, 'none', newStatus, 'na', date)
        self._db.insertIntoProjectorRepairTable(projSerial, date, 'bulb', uninstalledBy, 'uninstalled bulb')

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
        
    def installBulb(self, bulbID, projSerial, date, installedBy, note):
        """
        Input: bulbID of the bulb now being installed
               projSerial (serial number of projector bulb is to be 
                 installed into)
               date (today's date year-month-day Ex/ 2016-01-05 is 
                 January 5, 2016)
               installedBy (whoever installed the bulb)
               note (miscellaneous notes)
        Output: None
        Purpose: This method is for bulbs that are already in the system 
                and are being installed, most likely because they have 
                recently been repaired. 
        """
        if self.checkInputtedDate(date) == False:
            return
        self._db.updateBulbStatusTable(bulbID, 'none', 'in use', projSerial, date, note)
        self._db.insertIntoProjectorRepairTable(projSerial, date, 'bulb', installedBy, 'installed bulb')

    def updateLampHours(self, bulbID, lampHours):
        """
        Input: bulbID, lampHours
        Output: None
        Purpose: Integrate this method with pjcontrol to update the lamp hours of the bulbs
        """
        self._db.updateLampHoursInTable(bulbID, lampHours)

    def updateTotalHours(self, serial, totalHours):
        """
        Input: bulbID, totalHours
        Output: None
        Purpose: Integrate this method with pj-control to update the total hours of the projector
        """
        self._db.updateTotalHoursInTable(serial, totalHours)

    def addProjectorPosition(self,index,location,serialSwitch,serialPort,server,display):
        """
        Input: index corresponding to position number
               location (ceiling, wall, or floor)
               serialSwitch
               serialPort
               server
               display
        Output: None
        Purpose: These methods used initially to set up the positions table
        """
        self._db.insertIntoProjectorPositions(index,location,serialSwitch,serialPort,server,display)

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
    
