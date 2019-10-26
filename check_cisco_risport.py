#!/usr/bin/python3

from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from requests import Session
from requests.auth import HTTPBasicAuth
from lxml import etree
import urllib3
import sys
import getopt
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#nagios return codes
UNKNOWN = -1
OK = 0
WARNING = 1
CRITICAL = 2
usage = 'usage: ./check_cisco_risport -H <string> -u <string> -p <string> -d <string> -w <integer> -c <integer>'

levels = [ 
	{ 
		"name":"Registered",
		"value": 1
	},
	{ 
		"name":"UnRegistered",
		"value": 2
	},
	{ 
		"name":"Rejected",
		"value": 3
	},
	{ 
		"name":"PartiallyRegistered",
		"value": 4
	},
	{ 
		"name":"Unknown",
		"value": 5
	},
	{ 
		"name":"NotFound",
		"value": 6
	}
]

def get_risport(username,password,hostname,devicename):
	username = username
	password = password
	cmserver = hostname
	cmport = '8443'
	wsdl = 'https://' + cmserver + ':' + cmport + '/realtimeservice2/services/RISService70?wsdl'  
	session = Session()
	session.verify = False
	session.auth = HTTPBasicAuth(username, password)
	transport = Transport(cache=SqliteCache(), session=session)
	history = HistoryPlugin()
	client = Client(wsdl=wsdl, transport=transport, plugins=[history])
	factory = client.type_factory('ns0')
	deviceArr = [devicename] #'*' for all
	item=[]

	for names in deviceArr:
		item.append(factory.SelectItem(Item=names))

	Item = factory.ArrayOfSelectItem(item)
	stateInfo = ''

	criteria = factory.CmSelectionCriteria(
		MaxReturnedDevices = 1000,
		DeviceClass='Any', #The device class to query for real-time status. Device classes include: Any, Phone, Gateway, H323, Cti, VoiceMail, MediaResources, HuntList, SIPTrunk, Unknown
		Model=255,    #255 for all
		Status='Any', #Allows device searches by status (or state): Any,Registered,UnRegistered, Rejected,PartiallyRegistered,Unknown
		NodeName='',
		SelectBy='Name',
		SelectItems=Item,
		Protocol='Any',
		DownloadStatus='Any'
	)

	timeStampCheck = 0
	status = ''

	try:
		result = client.service.selectCmDevice(stateInfo, criteria)
		
		if result['SelectCmDeviceResult']['TotalDevicesFound'] == 0:
			print ('***devicename not found***')
			sys.exit(UNKNOWN)
		else:
			for node in result['SelectCmDeviceResult']['CmNodes']['item']:
				if node['CmDevices'] != None:
					for device in node['CmDevices']['item']:
						data = {
							'name':device['Name'],
							'directory':device['DirNumber'],
							'status':device['Status'],
							'description':device['Description'],
							'ipaddress':device['IPAddress']['item'][0]['IP'],
							'timestamp':device['TimeStamp'],
							'deviceclass':device['DeviceClass']
						}
						if (device['TimeStamp'] >= timeStampCheck):
							timeStampCheck = device['TimeStamp']
							status = device['Status']

		return status
	except Exception as e:
		# If error exit with UNKNOWN
		print(e)
		sys.exit(UNKNOWN)
	
# define command line options and validate data.  Show usage or provide info on required options
def command_line_validate(argv):
	try:
		opts, args = getopt.getopt(argv, 'H:u:p:d:w:c:o:', ['hostname=','username=','password=','devicename=','warn=','crit='])
	except getopt.GetoptError:
		print (usage)
	try:
		for opt, arg in opts:
			if opt in ('-w', '--warn'):
				try:
					warn = int(arg)
				except:
					print ('***warn value must be an integer***')
					sys.exit(CRITICAL)
			elif opt in ('-c', '--crit'):
				try:
					crit = int(arg)
				except:
					print ('***crit value must be an integer***')
					sys.exit(CRITICAL)
			elif opt in ('-u', '--username'):
				try:
					username = str(arg)
				except:
					print ('***username value must be an string***')
					sys.exit(CRITICAL)
			elif opt in ('-p', '--password'):
				try:
					password = str(arg)
				except:
					print ('***password value must be an string***')
			elif opt in ('-H', '--hostname'):
				try:
					hostname = str(arg)
				except:
					print ('***hostname value must be an string***')
					sys.exit(CRITICAL)
			elif opt in ('-d', '--devicename'):
				try:
					devicename = str(arg)
				except:
					print ('***devicename value must be an string***')
					sys.exit(CRITICAL)
			else:
				print (usage)
		try:
			isinstance(username, str)
			#print ('user:', username)
		except:
			print ('***username is required***')
			print (usage)
			sys.exit(CRITICAL)
		try:
			isinstance(password, str)
			#print ('pass:', password)
		except:
			print ('***password is required***')
			print (usage)
			sys.exit(CRITICAL)
		try:
			isinstance(hostname, str)
			#print ('hostname:', hostname)
		except:
			print ('***hostname (IP Address or DNS) is required***')
			print (usage)
			sys.exit(CRITICAL)
		try:
			isinstance(devicename, str)
			#print ('devicename:', devicename)
		except:
			print ('***devicename is required***')
			print (usage)
			sys.exit(CRITICAL)
		try:
			isinstance(warn, int)
			#print ('warn level:', warn)
		except:
			print ('***warn level is required***')
			print (usage)
			sys.exit(CRITICAL)
		try:
			isinstance(crit, int)
			#print ('crit level:', crit)
		except:
			print ('***crit level is required***')
			print (usage)
			sys.exit(CRITICAL)
	except:
		sys.exit(CRITICAL)
	# confirm that warning level is less than critical level, alert and exit if check fails
	if warn > crit:
		print ('***warning level must be less than critical level***')
		sys.exit(CRITICAL)
	return hostname,username,password,devicename,warn,crit
	
#check total CPU 
def status_check(devicename,status,warn,crit):
	result = None

	matchStatusName = next(d for d in levels if d['name'] == status)
	matchCriticalLevel = next(d for d in levels if d['value'] == crit)
	matchWarningLevel = next(d for d in levels if d['value'] == warn)
	
	
	if matchStatusName['value'] >= crit:
		print ('CRITICAL - Registration Status for ',devicename,': ', status, '; Critical Value:', matchCriticalLevel['name'])
		result = 1
		sys.exit(CRITICAL)
	elif matchStatusName['value'] >= warn:
		print ('Warning - Registration Status for ',devicename,': ', status, '; Warning Value:', matchWarningLevel['name'])
		result = 1
		sys.exit(WARNING)

	return result

# main function
def main():
	argv = sys.argv[1:]
#	print(argv)
	hostname,username,password,devicename,warn,crit = command_line_validate(argv)
	status = get_risport(username,password,hostname,devicename)
#   print perf_data
	result = status_check(devicename, status, warn, crit)
	if result == None:
		matchCriticalLevel = next(d for d in levels if d['value'] == crit)
		matchWarningLevel = next(d for d in levels if d['value'] == warn)
		print ('OK - Registration Status for ',devicename, ': ', status, '; Warning Value:',matchWarningLevel['name'],"; Critical Value:",matchCriticalLevel['name'])
if __name__ == '__main__':
	main()