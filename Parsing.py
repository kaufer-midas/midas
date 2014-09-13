import time
from os import system
from datetime import datetime as dt
import sys

months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 
                        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}

def findAscDate(timeEpoch):
    ascRaw = time.ctime(float(timeEpoch))
    ascDate = ascRaw[-2:] + '/' +  months[ascRaw[4:7]] + '/' + ascRaw[8:10]
    return ascDate 

def findAscTime(timeEpoch):     
    ascRaw = time.ctime(float(timeEpoch))
    ascTime = ascRaw[11:19] + '.00'
    return ascTime

class Data:

	def __init__(self, dataLine):
		self.data = self.sliceData(dataLine)
		self.type = self.checkType()
		self.tag = 'N/A'
		self.gate = 'N/A'
		if self.type == 'tag':
			self.tag = self.data[0]
			self.gate = self.data[1]
		self.timeEpoch = float(self.data[2])
		self.ascStamp = self.data[3]

	def sliceData(self, dataLine):
		split = dataLine.split('"')
		return [split[1], split[3], split[5], split[7]]

	def checkType(self):
		if self.data[0] == 'wheel':
			return 'wheel'
		else:
			return 'tag'

class Mouse:

	def __init__(self, inputTag):
		self.tag = inputTag
		self.inWheel = False
		self.ranThisBlock = 0.0
		self.ranTotal = 0.0
		self.file = self.makeFile()
		self.inOutFile = self.makeInOutFile()

	def makeFile(self):
		filename = self.tag + '.txt'
		mouseFile = open(filename, 'w')
		mouseFile.write('GROUP ' + self.tag + '                                                                                 :\r\n\r\n---------\r\nUNIT TIME=\r\n')
		return mouseFile

	def makeInOutFile(self):
		filename = self.tag + '_inOut.txt'
		inOutFile = open(filename, 'w')
		inOutFile.write('RECORD OF MOUSE ENTERING AND EXITING WHEEL\n')
		return inOutFile

	def writeInOutLine(self, timeEpoch):
		dateAsc = findAscDate(timeEpoch)
		timeAsc = findAscTime(timeEpoch)
		if self.inWheel:
			self.inOutFile.write('ENTER AT: ' + timeAsc + '    ' + dateAsc + '\r\n')
		elif not self.inWheel:
			self.inOutFile.write('EXIT AT: ' + timeAsc + '    ' + dateAsc + '\r\n')

	def countTurn(self):
		if self.inWheel:
			self.ranThisBlock += 1
			self.ranTotal += 1

	def writeLine(self, dateAsc, timeAsc, scale):
		scaledRanThisBlock = self.ranThisBlock / scale
		self.file.write(dateAsc + ' ' + timeAsc + '     ' + str(scaledRanThisBlock) + '\r\n')

	def finishBlock(self):
		self.ranThisBlock = 0.0

class Group:

	def __init__(self, mice):
		self.tags = self.getTags(mice)
		self.name = self.genName()
		self.inWheel = False
		self.revolutions = 0.0
		self.durations = []
		self.startTime = None
		self.finishTime = None
		self.revolutionsInDuration = 0.0

	def durationFile(self):
		dCSV = open('durations.csv', 'a')
		for duration in self.durations:
			dCSV.write('"' + self.name + '","' + str(duration[0]) + '","' + str(duration[1]) + '","' + str(duration[2]) + '"\r\n')
		dCSV.close()	

	def addDuration(self):
		newDuration = (self.startTime, self.finishTime, self.revolutionsInDuration)
		self.durations.append(newDuration)
		self.startTime = None
		self.finishTime = None
		self.revolutionsInDuration = 0.0

	def getTags(self, mice):
		tags = []
		for mouse in mice:
			tags.append(mouse.tag)
		return tags

	def genName(self):
		tagString = ''
		for tag in self.tags:
			tagString += tag[-2:] + '_'
		return tagString

	def countWheel(self):
		if self.inWheel:
			self.revolutions += 1
			self.revolutionsInDuration += 1

	def checkMatch(self, matchTags):
		if len(matchTags) != len(self.tags):
			return False
		else:
			for tag in matchTags:
				if tag not in self.tags:
					return False
			return True

	def checkGroupInWheel(self, matchTags, currentData):
		if self.checkMatch(matchTags):
			self.inWheel = True
			if self.startTime == None:
				self.startTime = currentData.timeEpoch
		else:
			self.inWheel = False
			if self.finishTime == None and self.startTime != None:
				self.finishTime = currentData.timeEpoch
				self.addDuration()

class Parser:

	def __init__(self):
		print "Setting up..."
		self.csvfile = self.openCSV()
		self.data, self.startTime = self.makeData()
		self.dataIndex = 0
		self.miceTags, self.mice = self.makeMice()
		self.groups = self.makeGroups()
		self.interval, self.scale, self.odometerMode = self.setup()
		self.endOfBlock = self.startTime + self.interval
		self.done = False
		self.currentData = None
		self.ranTotalBlock = 0.0
		self.ranTotal = 0.0
		self.cageFile = self.makeCageFile()
		self.miceTagsInWheel = []

	def setup(self):
		if raw_input("Use defaults? (Interval: 600s, Scale: 1, Odometer Mode: 1) (y/n): ").lower() == 'y':
			return 600.0, 1.0, True
		else:
			interval = float(input("Interval (seconds): "))
			scale = float(input("Scale: "))
			odometerMode = bool(input("Odometer Mode (1 = True, 0 = False): "))
			return interval, scale, odometerMode

	def openCSV(self):
		try:
			csvfile = open('data.csv', 'r')
		except:
			csvfile = open(raw_input("CSV filename (with .csv extension): "), 'r')
		return csvfile

	def makeData(self):
		print 'Making data...'
		startTime = float(self.csvfile.readline()[12:25])
		data = []
		done = False
		while not done:
			dataLine = self.csvfile.readline()
			if dataLine == '':
				done = True
			else:
				data.append(Data(dataLine))
		data.append('done')
		print 'Finished data...'
		return data, startTime

	def makeMice(self):
		print 'Making mice...'
		miceTags, mice = [], []
		done = False
		while not done:
			for d in self.data:
				if d == 'done':
					done = True
				else:
					if d.type == 'tag':
						if d.tag not in miceTags:
							miceTags.append(d.tag)
							mice.append(Mouse(d.tag))
		print 'Finished mice...'
		return miceTags, mice

	def makeGroups(self):
		print 'Making groups...'
		sets = [[i] for i in range(len(self.miceTags))]
		groups = []
		S = [[i] for i in range(len(self.miceTags))]
		N = S
		for k in range(len(self.miceTags)):
			if N:
				S = N
				N = []
				for e in S:
					for i in range(e[-1]+1, len(self.miceTags)):
						f = e[:]
						f.append(i)
						N.append(f)
						sets.append(f)
		for subset in sets:
			groups.append(Group([self.mice[e] for e in subset]))
		print 'Finished groups...'
		return groups

	def makeCageFile(self):
		cageFile = open('cage.txt', 'w')
		cageFile.write('GROUP cage                                                                                                       :\r\n\r\n---------\r\nUNIT TIME=\r\n')
		return cageFile
	
	def writeData(self):
		scaledRanTotalBlock = self.ranTotalBlock / self.scale
		dateAsc = findAscDate(self.endOfBlock)
		timeAsc = findAscTime(self.endOfBlock)
		for mouse in self.mice:
			mouse.writeLine(dateAsc, timeAsc, self.scale)
			mouse.finishBlock()
		self.cageFile.write(dateAsc + ' ' + timeAsc + '     ' + str(scaledRanTotalBlock) + '\r\n')
		self.ranTotalBlock = 0.0

	def updateMiceFlags(self):
		for mouse in self.mice:
			if mouse.tag == self.currentData.tag:
				if self.currentData.gate == '1':
					mouse.inWheel = False
					if mouse.tag in self.miceTagsInWheel:
						self.miceTagsInWheel.remove(mouse.tag)
				elif self.currentData.gate == '2':
					mouse.inWheel = True
					if not mouse.tag in self.miceTagsInWheel:
						self.miceTagsInWheel.append(mouse.tag)
				mouse.writeInOutLine(self.currentData.timeEpoch)

	def countTurns(self):
		doesAdd = False
		numMice = 0
		for mouse in self.mice:
			if mouse.inWheel:
				doesAdd = True
				numMice += 1
				mouse.countTurn()
		if doesAdd:
			if self.odometerMode:
				self.ranTotal += 1
				self.ranTotalBlock += 1
			else:
				ranTotal += numMice
				ranTotalBlock += numMice
		for group in self.groups:
			if group.inWheel:
				group.countWheel()

	def parseLine(self):
		self.currentData = self.data[self.dataIndex]
		if self.currentData == 'done':
			self.done = True
		else:
			if self.currentData.type == 'wheel':
				if (self.currentData.timeEpoch < self.endOfBlock):
					self.countTurns()
				else:
					self.writeData()
					self.endOfBlock += self.interval
					while (self.currentData.timeEpoch > self.endOfBlock):
						self.writeData()
						self.endOfBlock += self.interval
					self.countTurns()
			elif self.currentData.type == 'tag':
				if (self.currentData.timeEpoch < self.endOfBlock):
					self.updateMiceFlags()
				else:
					self.writeData()
					self.endOfBlock += self.interval
					while (self.currentData.timeEpoch > self.endOfBlock):
						self.writeData()
						self.endOfBlock += self.interval
					self.updateMiceFlags()
				for group in self.groups:
					group.checkGroupInWheel(self.miceTagsInWheel, self.currentData)
		self.dataIndex += 1

	def parse(self):
		print 'Parsing...'
		while not self.done:
			self.parseLine()
		print 'Finished Parsing...'
		print 'Finishing file creation...'
		for mouse in self.mice:
			mouse.file.close()
			mouse.inOutFile.write('Total Revolutions: ' + str(mouse.ranTotal))
			mouse.inOutFile.close()
		self.cageFile.close()
		for group in self.groups:
			group.durationFile()
		print 'Done.'

def main():
	p = Parser()
	p.parse()

main()