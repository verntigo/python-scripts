#!/bin/python
#vcd-pwl maker
#A tool for parsing vcd file and make pwl file.
#By Steve M Song(stevemsong@yahoo.com)
#
# VCG
# Generalized the regexes. Works with Icarus Verilog.
# Vectored nets have not yet been tested.
import re,sys,os
from textwrap import wrap
import getopt

usage='''Usage: vcd-pwl.py [-h <voltage> | --high=<voltage>] [-l <voltage> | --low=<voltage>] 
    [-d <top_module> | --dut=<top_module>] <vcd_file>
        -h
        --high -- High output logic voltage level
        -l
        --low  -- Low output logic voltage level
        -d
        --dut  -- Device under test: this module's inputs will be rendered as PWL data
        vcd_file -- The VCD file to convert to PWL '''

try:
	opts, args = getopt.getopt(sys.argv[1:], "h:l:d:", ["high=", "low=", "dut="])
except getopt.GetoptError as err:
	print str(err)
	print usage
	sys.exit(2)
highVolts = 1.0
lowVolts  = 0.0
dut = "DUT"
for o, a in opts:
	if o in ("-h", "--help"):
		highVolts = a
	elif o in ("-l", "--low"):
		lowVolts = a
	elif o in ("-d", "--dut"):
		dut = a
	else:
		assert False, "unhandled option"

#if len(sys.argv) < 2:
#	print('usage: vcd-pwl.py <vcd-file>')
#	sys.exit(1)
if len(args) < 1:
	assert False, "Missing VCD file"
	
#inputFile = open('tb_mult8X8.vcd','r')
#inputFileName = sys.argv[1]
inputFileName = args[0]
inputFileExtension = os.path.splitext(inputFileName)[1]
baseName = os.path.splitext(os.path.basename(inputFileName))[0]
dirName = os.path.dirname(inputFileName)
#print "inputFileName = {0}".format(inputFileName)
#print "inputFileExtension = {0}".format(inputFileExtension)
#print "baseName = {0}".format(baseName)
#print "dirName = {0}".format(dirName)
#exit()
#inputFile = open(sys.argv[1],'r')
inputFile = open(inputFileName,'r')
contentList = inputFile.readlines()
#print "contentList = "
#print "".join(contentList)
inputFile.close()

signals={}
parseValue=[]
def collectSignals():    #collects signals in a dictionary format
	#print('Collecting data for these signals:')
	for i in range(len(contentList)):
		if contentList[i]==('$scope module {0} $end\n'.format(dut)):
			while re.search(r'^\$var\s+wire\s+\d+\s+\S+\s+([a-zA-Z]+\S*)(\s+\[\S+\])?',contentList[i+1]):
				mo=re.search(r'^\$var\s+wire\s+(\d+)\s+(\S+)\s+((\S+)(\s+\[\S+\])?)',contentList[i+1])
				signals[mo.group(2)]=mo.group(3).replace(" ","")    #group(1)=bits, group(2)=key, group(3)=value
				i=i+1
	return signals

def timescale():		#reads in timescale
	for i in range(len(contentList)):
		if contentList[i]==('$timescale\n'):
			while contentList[i] != ('$end\n'):
				if re.search(r'\s+\d+(\w)s',contentList[i]):
					timescale = re.search(r'\s+\d+(\w)s',contentList[i]).group(1)
				i=i+1
	return timescale

def printScreen():    #outputs signal transitions with timestamp
	for i in range(len(contentList)):
		if re.search(r'\#\d+',contentList[i]):
			print(re.search(r'\#\d+',contentList[i]).group() + timescale + 'sec')
		for k in signals.keys():
			if re.search(r'(^[01bx]{2,}\s|^[x01])'+re.escape(k)+'\n',contentList[i]):
				print(signals[k] + str('=>') + str(re.search(r'(^[01bx]{2,}\s|^[x01])'+re.escape(k)+'\n',contentList[i]).group(1).strip()))
				
def captureData():    #captures signal transition in a list format
	count=-1    #initialize count for dictionary length
	for k,j in signals.items():
		count=count+1    #counting the k,j loop iteration for parseValue.append purpose
		parseValue.append([j])
		for i in range(len(contentList)):
			if re.search(r'(^[01bx]{2,}\s|^[x01])'+re.escape(k)+'\n',contentList[i]):
				parseValue[count].append(re.search(r'(^[01bx]{2,}\s|^[x01])'+re.escape(k)+'\n',contentList[i]).group(1).strip()) #signal value append to list
				while re.search(r'^\#(\d+)\n',contentList[i]) == None:
					i=i-1
					if re.search(r'^\#(\d+)\n',contentList[i]):
						parseValue[count].append(re.search(r'^\#(\d+)\n',contentList[i]).group(1) + timescale)    #timestamp append to list
	return parseValue

def bus2bitConversion():	#converts bus in list to individual bit transition
	for i in range(len(mylist)):
		mo=re.search(r'([^\[]+)\[(\d+):0\]',mylist[i][0])
		if mo:
			for j in range(int(mo.group(2))+int(1)):
				mylist.append([mo.group(1)+str([j])])
	for i in range(len(mylist)):
		mbus=re.search(r'([^\[]+)\[(\d+):0\]',mylist[i][0])    #group(1)=A_1 group(2)=7
		if mbus:
			for h in mylist[i]:  #going horizonal(list within list)
				mbusValue=re.search(r'^b([x01]+)',h)
				if mbusValue:
					if len(mbusValue.group(1))==1:
						for k in range(len(mylist)):
							mbusName=re.search(re.escape(mbus.group(1))+ r'\[(\d+)\]',mylist[k][0])
							if mbusName:
								mylist[k].append(mbusValue.group(1))
					else:
						partialList=list(mbusValue.group(1))
						addZeros=int(mbus.group(2))+1-len(partialList)
						for a in range(addZeros):
							partialList.insert(0,'0')  #adding 0's to complete the full bus data
						partialList.reverse()
						for m in range(len(mylist)): #going vertically entire list
							for j in range(len(partialList)): #bit index
								mbusNameBit=re.search(re.escape(mbus.group(1))+ r'\['+str(j)+r'\]',mylist[m][0])
								if mbusNameBit:
									mylist[m].append(partialList[j])
				mtime=re.search(r'\d+[a-z]',h)
				if mtime:
					for k in range(len(mylist)):
						mbusName=re.search(re.escape(mbus.group(1))+ r'\[(\d+)\]',mylist[k][0])
						if mbusName:
							mylist[k].append(mtime.group())
	result=[]						 
	for i in range(len(mylist)):	#removing bus data from the list
		mbus=re.search(r'([^\[]+)\[(\d+):0\]',mylist[i][0])
		if mbus:
			result.append(mylist[i])
	for i in result:
		mylist.remove(i)
				   
def makePwl(input):    #takes in captured signal list and outputs pwl format in a file
	finalContent=''
	# Regex that finds time points with SPICE suffixes
	# Since Verilog represents time steps as integer values of the simulation resolution, this is
	# relatively simple
	re_timepoint = re.compile(r"(\d+)(\w)?")
	for i in range(len(input)):
		#content='vv{0} {1} 0'.format(i+1, input[i][0])
		content='V_{0} {1} 0'.format(input[i][0], input[i][0])
		#input[i].insert(1,'0 dc 0 pwl (0')
		#input[i].insert(1,'0 dc 0 pwl (')
		content = content + ' dc 0 pwl ('
		#content = content + str(' ') + input[i][0]
		content = content + str(' ') + input[i][2] + str(' ') + outputLevel(input[i][1])
		#print content
		old_amp = input[i][1]
		if len(input[i]) > 3:
			#for j in range(len(input[i])):
			for j in range(3, len(input[i]), 2):
				tmpt = re.search(re_timepoint, input[i][j+1])
				timept = tmpt.group(1)
				timesfx = tmpt.group(2)
				#print "timept = {0}, timesfx = {1}".format(timept, timesfx)
				#content = content + str(' ') + input[i][j]
				content = content + str(' ') + str(int(timept)-1) + timesfx + str(' ') + outputLevel(old_amp)
				content = content + str(' ') + str(int(timept)+1) + timesfx + str(' ') + outputLevel(input[i][j])
				old_amp = input[i][j]
		#content = content + ')'
		content = content + ' )'
		finalContent = finalContent + content + '\n'
	finalContent = filterLineLength(finalContent)
	print(finalContent)
	#outputFile = open('vcd2pwl.out','w')
	#outputFile = open(sys.argv[2],'w')
	outputFile = open("{0}/{1}.pwl".format(dirName, baseName) if dirName != "" else "{0}.pwl".format(baseName), 'w')
	outputFile.write(finalContent)
	outputFile.close()

def filterLineLength(linestream, lengthOpt=80):
	lines = linestream.split("\n")
	continuationStr = "+ "
	newlines = []
	for ln in lines:
		lnset = []
		if len(ln) > lengthOpt:
			lnset = wrap(ln, lengthOpt, subsequent_indent = continuationStr)
			for item in lnset:
				newlines.append(item)
		else:
			newlines.append(ln)
	return "\n".join(newlines)

def outputLevel(digval):
	output = ''
	if int(digval) == 1:
		output = highVolts
	elif int(digval) == 0:
		output = lowVolts
	else:
		output = digval
	# Return a string to make the printing easier
	return str(output)

signalsDict=collectSignals()
#print(signalsDict)
timescale=timescale()
#printScreen()
mylist=captureData()
bus2bitConversion()
#print(mylist)
makePwl(mylist)
