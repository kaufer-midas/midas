from datetime import datetime as dt
import time

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

class Durations:

	def __init__(self, durationCSV):
		self.durationsFile = open(durationCSV, 'r')
		self.durationsRaw = self.durationsFile.readlines()
		self.durationsParsed = self.parseDurations()

	def parseDurations(self):
		durationsParsed = []
		for durationRaw in self.durationsRaw:
			split = durationRaw.split('"')
			durationsParsed.append((split[1], float(split[3]), float(split[5]), float(split[7]))) 
		return durationsParsed

	def selectDurations(self, startTime, endTime):
		selectedDurations = []
		for durationParsed in self.durationsParsed:
			if durationParsed[1] >= startTime and durationParsed[1] <= endTime:
				selectedDurations.append(durationParsed)
		return selectedDurations

	def selectTime(self):
		date = raw_input("Start Date (day/month/year) (no leading 0s e.g. 8/1/2014, not 08/01/2014): ")
		dateSplit = date.split("/")
		month = int(dateSplit[0])
		day = int(dateSplit[1])
		year = int(dateSplit[2])

		time = raw_input("Start Time (24hr) (e.g. 7:31, 14:19): ")
		timeSplit = time.split(":")
		hour = int(timeSplit[0])
		minute = int(timeSplit[1])
		
		length = raw_input("Duration to search (hours:minutes:seconds) (e.g. 03:30:00): ")
		lengthSplit = length.split(":")
		lengthSeconds = (3600 * int(lengthSplit[0])) + (60 * int(lengthSplit[1])) + int(lengthSplit[2])
		
		startTime = (dt(year, month, day, hour, minute) - dt(1970, 1, 1)).total_seconds() + 25200
		endTime = startTime + lengthSeconds
		
		return startTime, endTime

	def printDuration(self, duration):
		startTimeStamp = findAscDate(duration[1]) + ' at ' + findAscTime(duration[1])
		endTimeStamp = findAscDate(duration[2]) + ' at ' + findAscTime(duration[1])
		durationLength = duration[2] - duration[1]
		print 'Group ' + duration[0] + ': Start: ' + startTimeStamp + ', End: ' + endTimeStamp + ', Duration: ' + str(durationLength) + ', Wheels: ' + str(duration[3])
		
	def search(self):
		try:
			startTime, endTime = self.selectTime()
			selectedDurations = self.selectDurations(startTime, endTime)
			for duration in selectedDurations:
				self.printDuration(duration)
		except:
			print "\nRestarting\n"
			pass
			
def main():
	d = Durations('durations.csv')
	while True:
		d.search()

main()