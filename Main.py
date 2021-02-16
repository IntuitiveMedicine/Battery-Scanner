import sys, sqlite3
from sqlite3 import Error
from datetime import date
import pynput
from pynput.keyboard import Key, Controller
from PyQt5 import QtCore, QtGui, QtWidgets, uic

keyboard = Controller()

database = "./batterydattabase.db"
# create a database connection
conn = None
try:
	conn = sqlite3.connect(database)
except Error as e:
	print(e)
# create table if not initialized
if conn is not None:
	try:
		c = conn.cursor()
		c.execute("CREATE TABLE IF NOT EXISTS batteries ( id integer PRIMARY KEY, SN text NOT NULL, date_of_test_charge text, date_of_confirmation_charge text, mAh integer, Voltage_delta integer);")
	except Error as e:
		print(e)
else:
	print("Error! cannot create the database connection.")

def initial_test_voltage(battSerial):
	# Get user data on new battery
	todaysDate = date.today()
	# This is the function to call when the cell is completly scanned
	cur = conn.cursor()
	cur.execute("SELECT rowid FROM batteries WHERE SN = ?", (battSerial,))
	data = cur.fetchall()
	if not data:
		cur.execute("INSERT INTO batteries (SN) "
					"VALUES(?)", (battSerial,))
		conn.commit()
	cur = conn.cursor()
	cur.execute("UPDATE batteries "
			 "SET date_of_test_charge = ? " 
			 "WHERE SN = ?", (todaysDate, battSerial))
	conn.commit()
def mah_measurment(battSerial, measuredVoltage, measuredmAH):
	# Get user data on new battery
	todaysDate = date.today()
	try:
		voltageDelta = 4.2 - measuredVoltage
	except:
		voltageDelta = "--"
	# This is the function to call when the cell is completly scanned
	cur = conn.cursor()
	cur.execute("SELECT rowid FROM batteries WHERE SN = ?", (battSerial,))
	data = cur.fetchall()
	if not data:
		cur.execute("INSERT INTO batteries (SN) "
					"VALUES(?)", (battSerial,))
		conn.commit()
		print("ERROR: This battery was never scanned during first scan")
	# Checks the first mAH was scanned
	cur.execute("SELECT rowid FROM batteries WHERE mAh_One IS NOT NULL AND SN = ?", (battSerial,))
	dataTwo = cur.fetchall()
	if not dataTwo:
		cur.execute("UPDATE batteries "
					"SET mAh_One = ? "
					"WHERE SN = ?", (measuredmAH, battSerial))
		conn.commit()
	else:
		cur.execute("UPDATE batteries "
					"SET mAh_Two = ?, "
					"date_of_confirmation_charge = ?, "
					"Voltage_delta = ? "
					"WHERE SN = ?", (measuredmAH, todaysDate, voltageDelta, battSerial))
		conn.commit()

class MainWindow(QtWidgets.QMainWindow):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		uic.loadUi("mainwindow.ui", self)
		cur = conn.cursor()
		self.Voltage_test_Button.clicked.connect(self.VoltageButtonClicked)
		self.ah_test_button.clicked.connect(self.mahButtonClicked)
		totalbatterycount = cur.execute('select * from batteries;')
		totalbatterycount = totalbatterycount.fetchall()
		totalbatterycount = len(totalbatterycount)
		self.Total_Cell_Label.setText(str(totalbatterycount))
		finihsedData = cur.execute('select * from batteries where mAh_Two is not null;')
		self.Total_Cell_Finished_Label.setText(str(len(finihsedData.fetchall())))
		firstmAHData = cur.execute('select mAh_One from batteries where mAh_One is not null;')
		secondmAHData = cur.execute('select mAh_Two from batteries where mAh_Two is not null;')
		firstmAHData = firstmAHData.fetchall()
		secondmAHData = secondmAHData.fetchall()
		allmAhData = firstmAHData + secondmAHData
		totalCount = len(allmAhData)
		iterattor = 0
		for i in allmAhData:
			iterattor = iterattor + i[0]
		averagemAh = iterattor/totalCount
		self.Total_Cell_mAh_Label.setText("{:.2f} mAh".format(averagemAh))
		packCount = 15
		batteriesPerPack = totalbatterycount/packCount
		EstiamtedTotalmAh = (averagemAh * batteriesPerPack)/1000
		self.Total_Cell_ETotal_mAh_Label.setText("{:.2f} Ah at 50V pack".format(EstiamtedTotalmAh))
	def VoltageButtonClicked (self):
		self.w = InitialVoltageWindow()
		self.w.showMaximized()
		self.hide()
	def mahButtonClicked (self):
		self.w = mahVoltageWindow()
		self.w.showMaximized()
		self.hide()

class InitialVoltageWindow(QtWidgets.QWidget):
	battSerial = ""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		uic.loadUi("scanvoltagewindow.ui", self)
		self.Done_button.pressed.connect(self.button_click)
		self.Battery_SN.installEventFilter(self)
	def eventFilter(self, obj, event):
		if event.type() == QtCore.QEvent.KeyPress and obj is self.Battery_SN:
			if event.key() == QtCore.Qt.Key_Return and self.Battery_SN.hasFocus():
				if self.Battery_SN.text() != "":
					self.battSerial = self.Battery_SN.text()
					initial_test_voltage(self.battSerial)
					self.Battery_SN.setText("")
		return super().eventFilter(obj, event)
	def button_click(self):
		self.w = MainWindow()
		self.w.showMaximized()
		self.hide()
class mahVoltageWindow(QtWidgets.QWidget):
	battSerial = ""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		uic.loadUi("mAHUpdater.ui", self)
		self.FrameTwo.setHidden(not self.FrameTwo.isHidden())
		self.Battery_SN.installEventFilter(self)
		self.mAHRecordingLine.installEventFilter(self)
		self.Back_To_SN_Button.pressed.connect(self.BackToSNbutton_click)
		self.Saved_Results_Button.pressed.connect(self.SaveResultsbutton_click)
		self.Cancel_Button.pressed.connect(self.Cancelbutton_click)
		self.Button_Number_1.clicked.connect(self.NumberPadButtons)
		self.Button_Number_2.clicked.connect(self.NumberPadButtons)
		self.Button_Number_3.clicked.connect(self.NumberPadButtons)
		self.Button_Number_4.clicked.connect(self.NumberPadButtons)
		self.Button_Number_5.clicked.connect(self.NumberPadButtons)
		self.Button_Number_6.clicked.connect(self.NumberPadButtons)
		self.Button_Number_7.clicked.connect(self.NumberPadButtons)
		self.Button_Number_8.clicked.connect(self.NumberPadButtons)
		self.Button_Number_9.clicked.connect(self.NumberPadButtons)
		self.Button_Number_0.clicked.connect(self.NumberPadButtons)
		self.Button_Number_Period.clicked.connect(self.NumberPadButtons)
		self.Delete_Button.clicked.connect(self.NumberPadButtons)

	def Cancelbutton_click(self):
		self.w = MainWindow()
		self.w.showMaximized()
		self.hide()
	def BackToSNbutton_click(self):
		self.Frame1.setHidden(not self.Frame1.isHidden())
		self.FrameTwo.setHidden(not self.FrameTwo.isHidden())
		self.mAHRecordingLine.setText("")
	def SaveResultsbutton_click(self):
		if self.mAHRecordingLine.text() != "":
			mah_measurment(self.battSerial, None, self.mAHRecordingLine.text())
			self.mAHRecordingLine.setText("")
			self.Frame1.setHidden(not self.Frame1.isHidden())
			self.FrameTwo.setHidden(not self.FrameTwo.isHidden())
	def NumberPadButtons(self):
		if self.sender() is self.Button_Number_1:
			self.mAHRecordingLine.setFocus()
			keyboard.press('1')
		if self.sender() is self.Button_Number_2:
			self.mAHRecordingLine.setFocus()
			keyboard.press('2')
		if self.sender() is self.Button_Number_3:
			self.mAHRecordingLine.setFocus()
			keyboard.press('3')
		if self.sender() is self.Button_Number_4:
			self.mAHRecordingLine.setFocus()
			keyboard.press('4')
		if self.sender() is self.Button_Number_5:
			self.mAHRecordingLine.setFocus()
			keyboard.press('5')
		if self.sender() is self.Button_Number_6:
			self.mAHRecordingLine.setFocus()
			keyboard.press('6')
		if self.sender() is self.Button_Number_7:
			self.mAHRecordingLine.setFocus()
			keyboard.press('7')
		if self.sender() is self.Button_Number_8:
			self.mAHRecordingLine.setFocus()
			keyboard.press('8')
		if self.sender() is self.Button_Number_9:
			self.mAHRecordingLine.setFocus()
			keyboard.press('9')
		if self.sender() is self.Button_Number_0:
			self.mAHRecordingLine.setFocus()
			keyboard.press('0')
		if self.sender() is self.Button_Number_Period:
			self.mAHRecordingLine.setFocus()
			keyboard.press('.')
		if self.sender() is self.Delete_Button:
			self.mAHRecordingLine.setFocus()
			keyboard.press(Key.backspace)
	def eventFilter(self, obj, event):
		cur = conn.cursor()
		if event.type() == QtCore.QEvent.KeyPress and obj is self.Battery_SN:
			if event.key() == QtCore.Qt.Key_Return and self.Battery_SN.hasFocus():
				if self.Battery_SN.text() != "":
					self.battSerial = self.Battery_SN.text()
					firstmAHDataTrue = cur.execute('select mAh_One from batteries where mAh_One is not null AND SN = ?', (self.battSerial,))
					secondmAHDataTrue = cur.execute('select mAh_Two from batteries where mAh_Two is not null AND SN = ?', (self.battSerial,))
					countOfScans = '0'
					if firstmAHDataTrue is not None:
						if secondmAHDataTrue is not None:
							countOfScans = '2'
						else:
							countOfScans = '1'

					self.Battery_Scan_Count_Label.setText(countOfScans)
					self.Battery_SN_Label.setText(self.battSerial)
					self.Frame1.setHidden(not self.Frame1.isHidden())
					self.FrameTwo.setHidden(not self.FrameTwo.isHidden())
					self.mAHRecordingLine.setFocus()
					self.Battery_SN.setText("")
		return super().eventFilter(obj, event)
app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
w.showMaximized()
app.exec_()


