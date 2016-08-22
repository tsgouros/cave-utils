import sqlite3



class InventoryDatabase:
    '''
    This is the Inventory Database Object. (underlying object for InventoryDatabaseManager)
    It Builds a database unique to its name, and executes all
    data manipulations (inserting into/updating tables). 
    '''
    def __init__(self,name):
        ''' 
        Name should be entered as: Yurt, not Yurt.db
        '''
        self._name = name
        self._conn = sqlite3.connect(str(name)+'.db')
        self._c = self._conn.cursor()
        self.buildDatabase()

    def get_name(self):
        '''
        Input: None
        Output: name of the file
        Purpose: Getter for the file name
        '''
        return self._name
    
    def buildDatabase(self):
        #builds all of the tables
        self.createProjectorsTable()
        self.createProjectorSettingsHistoryTable()
        self.createProjectorCurrentStatusTable()
        self.createPositionsTable()
        self.createProjectorHistoryTable()
        self.createProjectorRepairsTable()
        self.createBulbCurrentStatusTable()
        self.createBulbHistoryTable()

    def createProjectorsTable(self):
        # creates the ProjectorsTable
        self._c.execute('CREATE TABLE IF NOT EXISTS Projectors(Projector_Serial TEXT, mfgDate TEXT, Last_Updated TEXT, Lens TEXT, redOffset TEXT, greenOffset TEXT, blueOffset TEXT, redGain TEXT, greenGain TEXT, blueGain TEXT, colorTemp TEXT, gamma TEXT)')

    def createProjectorSettingsHistoryTable(self):
        # creates the ProjectorsTable
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorSettingsHistory(Projector_Serial TEXT, Date_In TEXT, Date_Out TEXT, Lens TEXT, redOffset TEXT, greenOffset TEXT, blueOffset TEXT, redGain TEXT, greenGain TEXT, blueGain TEXT, colorTemp TEXT, gamma TEXT, Note TEXT)')

    def createProjectorCurrentStatusTable(self):
        # creates the Projector current status table
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorCurrentStatus(Projector_Serial TEXT, Status TEXT, Location TEXT, Position TEXT, Date_In TEXT, Total_Hours TEXT)')

    def createPositionsTable(self):
        # creates the Positions Table
        self._c.execute('CREATE TABLE IF NOT EXISTS Positions(Position TEXT, Location TEXT, Serial_Switch TEXT, Serial_Port TEXT, Server TEXT, Display TEXT)')
            
    def createProjectorHistoryTable(self):
        # creates the Projector History Table
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorHistory(Projector_Serial TEXT, Status TEXT, Location TEXT, Position TEXT, Date_In TEXT, Date_Out TEXT, Total_Hours TEXT, Note TEXT)')
            
    def createProjectorRepairsTable(self):
        # creates the Projector Repair Table
        self._c.execute('CREATE TABLE IF NOT EXISTS ProjectorRepairs(Repair_Index TEXT, Projector_Serial TEXT, Date TEXT, Repair TEXT, Repaired_By TEXT, Note TEXT)')
            
    def createBulbCurrentStatusTable(self):
        # creates the Bulb Current Status Table
        self._c.execute('CREATE TABLE IF NOT EXISTS BulbCurrentStatus(Bulb_ID TEXT, Bulb_Serial TEXT, Current_Life TEXT, Status TEXT, Projector_Serial TEXT, Date_In TEXT, Lamp_Hours TEXT)')
        
    def createBulbHistoryTable(self):
        # creates the Bulb History Table
        self._c.execute('CREATE TABLE IF NOT EXISTS BulbHistory(Bulb_ID TEXT, Bulb_Serial TEXT, Life TEXT, Status TEXT, Projector_Serial TEXT, Date_In TEXT, Date_Out TEXT, Lamp_Hours TEXT, Note TEXT)')

    '''
    FOLLOWING ARE DATA MANIPULATION METHODS
    '''
    def newBulbID(self):
        '''
        Input: None
        Output: The ID of the next bulb
        Purpose: Helper Method for inserting into Bulb Current Status Table
        '''
        self._c.execute("SELECT Bulb_ID FROM BulbCurrentStatus")
        IDs = self._c.fetchall()
        if len(IDs) == 0:
            return '1'
        lastBulbID = list(str(IDs[len(IDs)-1]))
        bulbID = ''
        for letter in lastBulbID:
            if letter == "'" or letter == '(' or letter == ')' or letter == ',':
                bulbID = bulbID
            else:
                bulbID = bulbID + letter
        bulbID = str(int(bulbID) + 1)
        return bulbID

    def getRepairIndex(self):
        '''
        Input: None
        Output: The repairIndex of the next repair
        Purpose: Helper Method for inserting into Projector Repair Table
        '''
        self._c.execute("SELECT Repair_Index FROM ProjectorRepairs")
        repairIndices = self._c.fetchall()
        if (len(repairIndices) == 0):
            return '1'
        lastRepairIndex = list(str(repairIndices[len(repairIndices)-1]))
        repairIndex = ''
        for letter in lastRepairIndex:
            if letter == "'" or letter == '(' or letter == ')' or letter == ',':
                repairIndex = repairIndex
            else:
                repairIndex = repairIndex + letter
        repairIndex = str(int(repairIndex) + 1)
        return repairIndex

    def fixString(self,string):
        '''
        Input: a string that looks like ('3',)
        Output: a string that looks like '3'
        Purpose: SQL is annoying and gives data like ('data',) which looks ugly when inserted into tables
        '''
        word = list(string)
        returnString = ''
        for letter in word:
            if letter == "'" or letter == '(' or letter == ')' or letter == ',':
                returnString = returnString
            else:
                returnString = returnString + letter
        return returnString


    def insertIntoBulbCurrentStatusTable(self,bulbSerial, currentLife, status, projSerial, dateIn, lampHours):
        '''
        Input: serial number of the bulb or 'unknown'
               current Life (Number of times the bulb has been reLamped, 0 if new)
               status (in use, spare, broken)
               projSerial (serial number of the projector, na if bulb is spare or broken)
               dateIn (date of change: year-month-day) Ex/ 2016-01-05 is January 5, 2016
               lampHours (number of hours on the bulb, 0 if new)
        Output: None
        Purpose: insert a row into the bulb current status table
        '''
        bulbID = self.newBulbID()
        self._c.execute("INSERT INTO BulbCurrentStatus(Bulb_ID, Bulb_Serial, Current_Life, Status, Projector_Serial, Date_In, Lamp_Hours) VALUES (?,?,?,?,?,?,?)",
                 (bulbID, bulbSerial, currentLife, status, projSerial, dateIn, lampHours))
        self._conn.commit()
        

    def updateBulbCurrentStatusTable(self,bulbID, currentLife, status, projSerial, dateIn, note):
        '''
        Input: bulbID,
               current Life (Number of times the bulb has been reLamped, 0 if new)
               new status (in use, broken, spare)
               projSerial (serial number of the projector, na if bulb status is now spare or broken)
               dateIn (date of change: year-month-day) Ex/ 2016-01-05 is January 5, 2016
               note (Miscellaneous note)
        Output: None
        Purpose: updating the current status table, also stores the previous status of the bulb in the
                 bulb history table
               
        '''
        #Bulb Serial
        self._c.execute("SELECT Bulb_Serial FROM BulbCurrentStatus WHERE Bulb_ID ="+"=?",(bulbID,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        bulbSerial = self.fixString(row)

        #Bulb Life
        self._c.execute("SELECT Current_Life FROM BulbCurrentStatus WHERE Bulb_ID ="+"=?",(bulbID,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        bulbLife = self.fixString(row)

        #oldStatus
        self._c.execute("SELECT Status FROM BulbCurrentStatus WHERE Bulb_ID ="+"=?",(bulbID,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldStatus = self.fixString(row)

        #oldProjector
        self._c.execute("SELECT Projector_Serial FROM BulbCurrentStatus WHERE Bulb_ID ="+"=?",(bulbID,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldProjector = self.fixString(row)

        #Lamp Hours
        self._c.execute("SELECT Lamp_Hours FROM BulbCurrentStatus WHERE Bulb_ID ="+"=?",(bulbID,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        lampHours = self.fixString(row)

        #prevDateIn
        self._c.execute("SELECT Date_In FROM BulbCurrentStatus WHERE Bulb_ID ="+"=?",(bulbID,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        prevDateIn = self.fixString(row)
        
        self.insertIntoBulbHistoryTable(bulbID, bulbSerial, bulbLife, oldStatus, oldProjector, prevDateIn, dateIn, lampHours, note)
        if currentLife is not 'none':
            self._c.execute("UPDATE BulbCurrentStatus SET Current_Life ="+"=?"+"WHERE Bulb_ID ="+"=?",(currentLife,bulbID,))
            self._conn.commit()
        if status is not 'none':
            self._c.execute("UPDATE BulbCurrentStatus SET Status ="+"=?"+"WHERE Bulb_ID ="+"=?",(status,bulbID,))
            self._conn.commit()
        if projSerial is not 'none':
            self._c.execute("UPDATE BulbCurrentStatus SET Projector_Serial ="+"=?"+"WHERE Bulb_ID ="+"=?",(projSerial, bulbID,))
            self._conn.commit()
        if dateIn is not 'none':
            self._c.execute("UPDATE BulbCurrentStatus SET Date_In ="+"=?"+"WHERE Bulb_ID ="+"=?",(dateIn,bulbID,))
            self._conn.commit()

    def updateLampHoursInTable(self,bulbID, lampHours):
        '''
        Input: bulbID, lampHours
        Output: None
        Purpose: update the lampHours in the Bulb Current Status Table
        '''
        self._c.execute("UPDATE BulbCurrentStatus SET Lamp_Hours ="+"=?"+"WHERE Bulb_ID ="+"=?",(lampHours,bulbID,))
        self._conn.commit()

    def insertIntoBulbHistoryTable(self,bulbID, bulbSerial, bulbLife, bulbStatus, projSerial, dateIn, dateOut, lampHours, Note):
        '''
        Input: bulbID,
               bulbSerial (bulb serial number or unknown)
               bulbLife (0 if it is on its first life)
               bulbStatus (in use, broken, spare at the time)
               projSerial (projector bulb was installed in, 'na' if it was spare or broken)
               dateIn (date projector was put in this status)
               dateOut (date projector was removed from this status)
               lampHours (hours on the bulb at the time of its removal)
               Note (miscellaneous notes)
        Output: None
        Purpose: Keep a log of everything that happens to the bulbs
               
        '''
        self._c.execute("INSERT INTO BulbHistory(Bulb_ID, Bulb_Serial, Life, Status, Projector_Serial, Date_In, Date_Out, Lamp_Hours, Note) VALUES (?,?,?,?,?,?,?,?,?)",
                 (bulbID, bulbSerial, bulbLife, bulbStatus, projSerial, dateIn, dateOut, lampHours, Note))
        self._conn.commit()

    def getBulbID(self,bulbSerial, projectorSerial):
        '''
        Input: bulb Serial Number or 'unknown'
               projectorSerial Number or 'unknown'
        Output: bulbID or Error String
        Purpose: Ideally query the database to find out the bulbID, this method is there to help
                 if you know the bulb serial number or the current projector serial number
        '''
        if bulbSerial is not 'unknown':
            self._c.execute("SELECT Bulb_ID FROM BulbCurrentStatus WHERE Bulb_Serial ="+"=?",(bulbSerial,))
            rowRaw = self._c.fetchall()
            row = str(rowRaw.pop())
            bulbID = self.fixString(row)
            return bulbID
        
        if projectorSerial is not 'unknown':
            self._c.execute("SELECT Bulb_ID FROM BulbCurrentStatus WHERE Projector_Serial ="+"=?",(projSerial,))
            rowRaw = self._c.fetchall()
            row = str(rowRaw[0])
            bulbID = self.fixString(row)
            return bulbID
        errorMessage = 'Please look through database to find bulbID'
        return errorMessage

    def getBulbLife(self,bulbID):
        '''
        Input: bulbID
        Output: Current Life of the bulb (amount of times it has been relamped)
        Purpose: Queries the database for the reLamped method to find out how many times a certain bulb has
                 been reLamped
        '''
        self._c.execute("SELECT Current_Life FROM BulbCurrentStatus WHERE Bulb_ID ="+"=?",(bulbID,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw.pop())
        bulbLife = self.fixString(row)
        return bulbLife

    def insertIntoProjectorsTable(self,serial, mfgDate, date, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma):
        '''
        Input: serial number of the projector
               mfgDate manufacturing date of the projector
               lens (short or long)
               Color Settings: red offset, green offset, blue offset
                               red gain, green gain, blue gain, colorTemp, gamma
        Output: None
        Purpose: This method is only used when a brand new projector is added to the sytem, all
                 of the values are static
        '''
        self._c.execute("INSERT INTO Projectors(Projector_Serial, mfgDate, Last_Updated, Lens, redOffset, greenOffset, blueOffset, redGain, greenGain, blueGain, colorTemp, gamma) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (serial, mfgDate, date, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma))
        self._conn.commit()

    def updateProjectorsTable(self,serial, updatedOn, newLens, NewrOff, NewgOff, NewbOff, NewrGain, NewgGain, NewbGain, newTemp, newGamma, note):
        '''
        Input: serial number of the projector
               updatedOn date today
               Color settings - changes if there are any, 'none' if there isn't one
               note - miscellaneous notes
        Output: None
        Purpose: Updates the projectors table if there is a change to its color settings, stores changes in a history table
        '''

        #prevDateIn
        self._c.execute("SELECT Last_Updated FROM Projectors WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        prevDateIn = self.fixString(row)

        #oldLens
        self._c.execute("SELECT Lens FROM Projectors WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldLens = self.fixString(row)

        #oldRoff
        self._c.execute("SELECT redOffset FROM Projectors WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldRoff = self.fixString(row)

         #oldGoff
        self._c.execute("SELECT greenOffset FROM Projectors WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldGoff = self.fixString(row)
        
         #oldBoff
        self._c.execute("SELECT blueOffset FROM Projectors WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldBoff = self.fixString(row)
        
         #oldRgain
        self._c.execute("SELECT redGain FROM Projectors WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldRgain = self.fixString(row)
        
         #oldGgain
        self._c.execute("SELECT greenGain FROM Projectors WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldGgain = self.fixString(row)
        
         #oldBgain
        self._c.execute("SELECT blueGain FROM Projectors WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldBgain = self.fixString(row)
        
         #oldTemp
        self._c.execute("SELECT colorTemp FROM Projectors WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldTemp = self.fixString(row)
        
         #oldGamma
        self._c.execute("SELECT gamma FROM Projectors WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldGamma = self.fixString(row)
        self.insertIntoProjetorSettingsHistoryTable(serial, prevDateIn, updatedOn, oldLens, oldRoff, oldGoff, oldBoff, oldRgain, oldGgain, oldBgain, oldTemp, oldGamma, note)

        if updatedOn is not 'none':
            self._c.execute("UPDATE Projectors SET Last_Updated ="+"=?"+"WHERE projector_serial ="+"=?",(updatedOn,serial,))
            self._conn.commit()
        if newLens is not 'none':
            self._c.execute("UPDATE Projectors SET Lens ="+"=?"+"WHERE projector_serial ="+"=?",(newLens, serial,))
            self._conn.commit()
        if NewrOff is not 'none':
            self._c.execute("UPDATE Projectors SET redOffset ="+"=?"+"WHERE projector_serial ="+"=?",(NewrOff,serial,))
            self._conn.commit()
        if NewgOff is not 'none':
            self._c.execute("UPDATE Projectors SET greenOffset ="+"=?"+"WHERE projector_serial ="+"=?",(NewgOff,serial,))
            self._conn.commit()
        if NewbOff is not 'none':
            self._c.execute("UPDATE Projectors SET blueOffset ="+"=?"+"WHERE projector_serial ="+"=?",(NewbOff,serial,))
            self._conn.commit()
        if NewrGain is not 'none':
            self._c.execute("UPDATE Projectors SET redGain ="+"=?"+"WHERE projector_serial ="+"=?",(NewrGain,serial,))
            self._conn.commit()
        if NewgGain is not 'none':
            self._c.execute("UPDATE Projectors SET greenGain ="+"=?"+"WHERE projector_serial ="+"=?",(NewgGain,serial,))
            self._conn.commit()
        if NewbGain is not 'none':
            self._c.execute("UPDATE Projectors SET blueGain ="+"=?"+"WHERE projector_serial ="+"=?",(NewbGain,serial,))
            self._conn.commit()
        if newTemp is not 'none':
            self._c.execute("UPDATE Projectors SET colorTemp ="+"=?"+"WHERE projector_serial ="+"=?",(newTemp,serial,))
            self._conn.commit()
        if newGamma is not 'none':
            self._c.execute("UPDATE Projectors SET gamma ="+"=?"+"WHERE projector_serial ="+"=?",(newGamma,serial,))
            self._conn.commit()
        
    def insertIntoProjetorSettingsHistoryTable(self,serial, dateIn, dateOut, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma, note):
        '''
        Input: serial number of the projector
               date into the old settings, date out of the old settings
               color settings
               note (miscellaneous notes)
        Output: None
        Purpose: Keep log of changes to the projector's color settings
        '''
        self._c.execute("INSERT INTO ProjectorSettingsHistory(Projector_Serial, Date_In, Date_Out, Lens, redOffset, greenOffset, blueOffset, redGain, greenGain, blueGain, colorTemp, gamma, Note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (serial, dateIn, dateOut, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma, note))
        self._conn.commit()

    def insertIntoProjectorCurrentStatusTable(self,serial, status, location, position, dateIn, totalHours):
        '''
        Input: serial number of the projector
               status (in use, broken, spare)
               location (on sire or off site)
               position (which position the projector is located in the YURT or 'na' if broken or spare)
               dateIn (date projector was placed in the current status)
               totalHours (number of hours the projector has been in use)
        Output: None
        Purpose: Insert rows into the projector current status table
        
        '''
        self._c.execute("INSERT INTO ProjectorCurrentStatus(Projector_Serial, Status, Location, Position, Date_In, Total_Hours) VALUES (?,?,?,?,?,?)",
                  (serial, status, location, position, dateIn, totalHours))
        self._conn.commit()

    def updateProjectorCurrentStatusTable(self,serial, status, location, position, dateIn, notes):
        '''
        Input: serial number of the projector
               new status (in use, broken, spare)
               new location (on site or off site)
               new position (location in the YURT or 'na' if broken or spare)
               dateIn (date the projector was placed in this new status)
               notes (miscellaneous notes
        Output: None
        Purpose: update a row in the projector current status table as well as take the previous
                 status and update the projector history table
        
        '''
        #Oldlocation
        self._c.execute("SELECT Location FROM ProjectorCurrentStatus WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldLocation = self.fixString(row)
        
        #Oldstatus
        self._c.execute("SELECT Status FROM ProjectorCurrentStatus WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldStatus = self.fixString(row)
        
        #dateIn Previous Status
        self._c.execute("SELECT Date_In FROM ProjectorCurrentStatus WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        dateInPrevStatus = self.fixString(row)
        
        #oldPosition
        self._c.execute("SELECT Position FROM ProjectorCurrentStatus WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        oldPosition = self.fixString(row)
        
        #totalHours
        self._c.execute("SELECT Total_Hours FROM ProjectorCurrentStatus WHERE projector_serial ="+"=?",(serial,))
        rowRaw = self._c.fetchall()
        row = str(rowRaw[0])
        totalHours = self.fixString(row)    

        self.insertIntoProjectorHistoryTable(serial, oldStatus, oldLocation, oldPosition, dateInPrevStatus, dateIn, totalHours, notes) 

        if status is not 'none':
            self._c.execute("UPDATE ProjectorCurrentStatus SET Status ="+"=?"+"WHERE projector_serial ="+"=?",(status,serial,))
            self._conn.commit()
        if location is not 'none':
            self._c.execute("UPDATE ProjectorCurrentStatus SET Location ="+"=?"+"WHERE projector_serial ="+"=?",(location,serial,))
            self._conn.commit()
        if position is not 'none':
            self._c.execute("UPDATE ProjectorCurrentStatus SET Position ="+"=?"+"WHERE projector_serial ="+"=?",(position,serial,))
            self._conn.commit()
        if dateIn is not 'none':
            self._c.execute("UPDATE ProjectorCurrentStatus SET Date_In ="+"=?"+"WHERE projector_serial ="+"=?",(dateIn,serial,))
            self._conn.commit()
            
    def updateTotalHoursInTable(self,serial, totalHours):
        '''
        Input: serial number of the projector
               totalHours of the projector
        Output: None
        Purpose: update the total hours on a projector in the current status table
        '''
        self._c.execute("UPDATE ProjectorCurrentStatus SET Total_Hours ="+"=?"+"WHERE Projector_Serial ="+"=?",(totalHours,serial,))
        self._conn.commit()
        
    def insertIntoProjectorHistoryTable(self,serial, status, location, position, dateIn, dateOut, totalHours, notes):
        '''
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
        '''
        self._c.execute("INSERT INTO ProjectorHistory(Projector_Serial, Status, Location, Position, Date_In, Date_Out, Total_Hours, Note) VALUES (?,?,?,?,?,?,?,?)",
                  (serial, status, location, position, dateIn, dateOut, totalHours, notes))             
        self._conn.commit()

    def insertIntoProjectorRepairTable(self,projSerial, date, repair, repairedBy, note):
        '''
        Input: serial number of the projector,
               date of repair (year-month-date) Ex/ 2016-01-05 is January 5, 2016
               repair type (install, uninstall, bulb, board, ship)
               repaired By (who repaired projector),
               note (miscellaneous notes)
        Output: None
        Purpose: Logging a new repair 
        '''
        repairIndex = self.getRepairIndex()
        self._c.execute("INSERT INTO ProjectorRepairs(Repair_Index, projector_serial, Date, Repair, Repaired_By, Note) VALUES (?,?,?,?,?,?)",
                 (repairIndex, projSerial, date, repair, repairedBy, note))
        self._conn.commit()           

    def insertIntoPositions(self,position,location,serialSwitch,serialPort,server,display):
        '''
        Input: position (number index that represents a position in the YURT)
               location (wall, door, ceiling) location of the position
               Attributes unique to a position:
               serialSwitch
               serialPort
               Server
               Display
        Output: None
        Purpose: Solely for the initial buildup of the Positions Table. The Positions Table is not modified
                 once all of the rows have been inserted into the table.
        
        '''
        self._c.execute("INSERT INTO Positions(Position, Location, Serial_Switch, Serial_Port, Server, Display) VALUES (?,?,?,?,?,?)",
                 (position, location, serialSwitch, serialPort, server, display))
        self._conn.commit()           



class InventoryDatabaseManager:
    '''
    The Inventory Database Manager object is the one used by the user.
    Ex/ to work with YurtInventory.db
    dbm = InventoryDatabaseManager('YurtInventory')
    '''

    def __init__(self,dbFilename):
        self._db = InventoryDatabase(dbFilename)

    def checkInputtedStatus(self, status):
        '''
        Input: status
        Output: True if the status is in use, spare or broken, otherwise False
        Purpose: 'Sanitizes' status - if more options become available add to the array
        '''
        possibleStatus = ['in use','spare','broken']
        checkStatus = status in possibleStatus 
        if checkStatus == False:
            print("status must be: 'in use','spare', or 'broken'")
            return False
        return True

    def checkInputtedLocation(self, location):
        '''
        Input: location
        Output: True if the location is formatted correctly, otherwise false
        Purpose: 'Sanitizes' location
        '''
        possibleLocations = ['on site','off site']
        checkLocation = location in possibleLocations
        if checkLocation == False:
            print("location must be: 'on site' or 'off site'")
            return False
        return True

    def checkInputtedLens(self, lens):
        '''
        Input: lens
        Output: True if the lens is one of the two choices, othewise False
        Putpose: 'Sanitizes' lens
        '''
        lenseTypes = ['short','long']
        checkLens = lens in lenseTypes
        if checkLens == False:
            print("lens must be: 'short' or 'long'")
            return False
        return True

    def checkInputtedDate(self, date):
        '''
        Input: date
        Output: True if the data is formmatted correctly, False if the date is formatted incorrectly
        Purpose: 'Sanitizes' date
        '''
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
        '''
        Input: repair
        Output: True if the repair is one of the choices, False if not
        Putpose: 'Sanitizes' repair
        '''
        possibleRepairs = ['bulb','install','uninstall','ship','fixed','recieved']
        checkRepair = repair in possibleRepairs
        if checkRepair == False:
            print("Repair can be: bulb, install, uninstall, or ship")
            return False
        return True       

    def newProjector(self, serial, status, location, position, date, mfgDate, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma):
        '''
        Input: serial number
               status (in Use, Spare, Broken),
               Location (on site or off site),
               manufacturing date, 
               Color settings: Red Offset, Green Offset, Blue Offset, Red Gain, Green Gain, Blue Gain, Temp, Gamma
        Output: None
        Purpose: Adding a new projector to the system, if the projector is in use right away,
                 this method will prompt two more inputs: repairedBy and Notes to add to the
                 Projector Repairs Log
        '''
        if self.checkInputtedStatus(status) == False or self.checkInputtedLocation(location) == False or self.checkInputtedLens(lens) == False or self.checkInputtedDate(date) == False:
            return
        
        self._db.insertIntoProjectorsTable(serial, mfgDate, date, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma)
        totalHours = 0
        self._db.insertIntoProjectorCurrentStatusTable(serial, status, location, position, date, totalHours)

        if status == 'in use':
            repairedBy = input("Who installed the projector?")
            notes = input("Any Notes?")
            self._db.insertIntoProjectorRepairTable(serial,  date, 'install', repairedBy, notes)

    def uninstallProjector(self, serial, newStatus, newLocation, date, uninstalledBy, note):
        '''
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
        '''
        if self.checkInputtedStatus(newStatus) == False or self.checkInputtedLocation(newLocation) == False or self.checkInputtedDate(date) == False:
            return
        self._db.updateProjectorCurrentStatusTable(serial, newStatus, newLocation, 'na', date, note)
        self._db.insertIntoProjectorRepairTable(serial,date,'uninstall',uninstalledBy, note)
            
    def installProjector(self, serial, position, date, installedBy, note):
        '''
        Input: serial number of the projector
               position the projector is installed to (index)
               date of the installation
               installedBy (who installed it)
               note (miscellaneous notes)
        Output: None
        Purpose: This method, unlike newProjector() assumes the projector is already in the system
                 and is now being installed. This method updates the status of the projector and
                 logs the installation in the Projector Repair Table.
        '''
        if self.checkInputtedDate(date) == False:
            return
        self._db.updateProjectorCurrentStatusTable(serial,'in use','on site',position,date,note)
        self._db.insertIntoProjectorRepairTable(serial, date, 'install', installedBy, note)

    def shipProjector(self, serial, status, date, whereTo, note):
        '''
        Input: serial number of the projector
               status (in use, spare, broken) - most likely broken
               date today (year-month-day Ex/ 2016-01-05 is January 5, 2016)
               whereTo - where the projector is being shipped to
               note (miscellaneous notes) 
        Output: None
        Purpose: Updates the current status of the projector if it is shipped off-site,
                 most likeley for repairs. Adds this to the projector repair table.
        '''
        if self.checkInputtedStatus(status) == False or self.checkInputtedDate(date) == False:
            return
        self._db.updateProjectorCurrentStatusTable(serial, status,'off site','na',date,note)
        self._db.insertIntoProjectorRepairTable(serial, date, 'ship',whereTo, note)

    def recievedProjector(self, serial,status,date,enteredBy, note):
        '''
        Input: serial number of the projector
               status (in use, spare, broken) - most likely broken
               date today (year-month-day Ex/ 2016-01-05 is January 5, 2016)
               enteredBy (whoever is responsible for recieving the Projector)
               note (miscellaneous notes) Ex/ Recieved from Taiwan
        Output: None
        Purpose: Updates the current status and repair record of the projector when it is recieved. 
        '''
        if self.checkInputtedStatus(status) == False or self.checkInputtedDate(date) == False:
            return
        self._db.updateProjectorCurrentStatusTable(serial, status, 'on site','na',date,note)
        self._db.insertIntoProjectorRepairTable(serial,date,'recieved',enteredBy,note)

    def fixedProjector(self, serial, date, fixedBy, note):
        '''
        Input: serial number of projector
               date today (year-month-day Ex/ 2016-01-05 is January 5, 2016)
               fixedBy (whoever fixed the projector)
               note (miscellaneous notes)
        Output: None
        Purpose: Udates current status of projector when it is fixed. Logs it into the
                 Projector Repairs Table.
        
        '''
        if self.checkInputtedDate(date) == False:
            return
        self._db.updateProjectorCurrentStatusTable(serial,'spare','on site','na',date,note)
        self._db.insertIntoProjectorRepairTable(serial, date, 'fixed', fixedBy, note)

    def projectorBreaks(self, serial, date, note):
        '''
        Input: serial number of the projector
               date the projector breaks (year-month-day Ex/ 2016-01-05 is January 5, 2016)
               note (miscellaneous notes)
        Output: None
        Purpose: Updates the current status of projector when it breaks. 
        '''
        if self.checkInputtedDate(date) == False:
            return
        self._db.updateProjectorCurrentStatusTable(serial, 'broken', 'on site', 'na', date, note)

    def updateProjectorSettings(self, serial, date, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma, note):
        '''
        Input: serial number of the projector
               date today (year-month-day Ex/ 2016-01-05 is January 5, 2016)
               lens (new Lens)
               new Color Settings
               note
        Output: None
        Purpose: on user's call it will update the projector's color settings, and log the old settings in a history table
       
        '''
        if self.checkInputtedLens(lens) == False or self.checkInputtedDate(date) == False:
            return
        self._db.updateProjectorsTable(serial, date, lens, rOff, gOff, bOff, rGain, gGain, bGain, temp, gamma, note)


    def newRepair(self, serial, date, repair, repairedBy, note):
        '''
        Input: serial number of the projector
               date of repair (year-month-day Ex/ 2016-01-05 is January 5, 2016)
               repairedBy, note
        Output: None
        Purpose: This method is for generic repairs such as board repairs. This method is not
                 for bulb repairs. 
        '''
        if self.checkInputtedRepair(repair) == False or self.checkInputtedDate(date) == False:
            return
        self._db.insertIntoProjectorRepairTable(serial, date, repair, repairedBy, note)

    def newBulb(self, bulbSerial, currentLife, status, projSerial, date):
        '''
        Input: serial number of the bulb (unknown if not known)
               status (in use, spare, broken),
               projSerial (serial number of the projector, na if bulb is spare or broken)
               dateIn (today's date year-month-day Ex/ 2016-01-05 is January 5, 2016),
               your name
        Output: None
        Purpose: Adding a new bulb to the system, if the bulb is being installed, update projector repairs
        '''
        if self.checkInputtedStatus(status) == False or self.checkInputtedDate(date) == False:
            return

        lampHours = 0
        
        self._db.insertIntoBulbCurrentStatusTable(bulbSerial, currentLife, status, projSerial, date, lampHours)

        if status == 'in use':
            repairedBy = input("Who installed the bulb into the Projector?")
            note = input("Any Notes?")
            self._db.insertIntoProjectorRepairTable(projSerial,date,'bulb',repairedBy,note)

    def uninstallBulb(self, bulbID, projSerial, newStatus, date, uninstalledBy, note):
        '''
        Input: bulbID (try to query database to find it, if not type idk - should work)
               projSerial (serial number of the projector)
               newStatus (broken or spare) of the bulb - most likely broken
               date (today's date year-month-day Ex/ 2016-01-05 is January 5, 2016)
               uninstalledBy (whoever uninstalled the bulb)
               note (Miscellaneous notes)
        Output: None
        Purpose: Updating status of the bulb that is being uninstalled and adding a repair record
        '''
        if self.checkInputtedStatus(newStatus) == False or self.checkInputtedDate(date) == False:
            return
        if bulbID == 'idk':
            bulbID = self._db.getBulbID('unknown',projSerial)
        self._db.updateBulbCurrentStatusTable(bulbID, 'none', newStatus, 'na', date, note)
        self._db.insertIntoProjectorRepairTable(projSerial, date, 'bulb', uninstalledBy, 'uninstalled bulb')

    def reLampBulb(self, oldBulbID, bulbSerial, newStatus, newProjSerial, date):
        '''
        Input: oldBulbID (try to query database to find it)
               bulbSerial (serial number of bulb or unknown)
               newStatus (in use, spare) most likely spare
               newProjSerial (if it is in use, specidy which projector it is now in, otherwise na)
               date (today's date year-month-day Ex/ 2016-01-05 is January 5, 2016)
        Output: None
        Purpose: Creates a new row in the bulb current status table. The bulb serial number
                 remians the same, but its life attribute increases by 1
        '''
        if self.checkInputtedStatus(newStatus) == False or self.checkInputtedDate(date) == False:
            return
        oldLife = self._db.getBulbLife(oldBulbID)
        currentLife = str(int(oldLife) + 1)
        self.newBulb(bulbSerial, currentLife, newStatus, newProjSerial, date)
        
    def installBulb(self, bulbID, projSerial, date, installedBy, note):
        '''
        Input: bulbID of the bulb now being installed
               projSerial (serial number of projector bulb is to be installed into)
               date (today's date year-month-day Ex/ 2016-01-05 is January 5, 2016)
               installedBy (whoever installed the bulb)
               note (miscellaneous notes)
        Output: None
        Purpose: This methos is for bulbs that are already in the system and are being installed, most
                 likely because they have recently been repaired. 
        '''
        if self.checkInputtedDate(date) == False:
            return
        self._db.updateBulbCurrentStatusTable(bulbID, 'none', 'in use', projSerial, date, note)
        self._db.insertIntoProjectorRepairTable(projSerial, date, 'bulb', installedBy, 'installed bulb')

    def updateLampHours(self, bulbID, lampHours):
        '''
        Input: bulbID, lampHours
        Output: None
        Purpose: Integrate this method with pj-control to update the lamp hours of the bulbs
        '''
        self._db.updateLampHoursInTable(bulbID, lampHours)

    def updateTotalHours(self, serial, totalHours):
        '''
        Input: bulbID, totalHours
        Output: None
        Purpose: Integrate this method with pj-control to update the total hours of the projector
        '''
        self._db.updateTotalHoursInTable(serial, totalHours)

    def runDemo(self):
        '''
        Generic Demo, can only be called on a db named demo.db (also a good way to test changes in methods)
        '''
        if self._db.get_name() is not 'demo':
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
    
