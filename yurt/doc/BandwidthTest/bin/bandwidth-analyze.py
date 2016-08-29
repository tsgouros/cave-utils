import csv
import sys
import itertools
import glob
import numpy as np
import collections

input_file = '../performance/data/combined.txt'
input_open = open(input_file, 'rb')
output_file = '../performance/time-analysis.txt'
output_open = open(output_file, "w")

#initialize four dict for storing timestamp
head_tracker = {}
init = {}
cached_load_file = {}
noncached_load_file = {}

#initialize four lists for avg calculation
avg_init = []
avg_noncached = []
avg_cached = []
avg_tracking = []


def get_time (line):
	line = line.split(';')
	time = int(''.join((line[1], line[2])))
	return time


def add_zero (string):
	while len(string) < 6:
		string = "0" + string
	return string


#process each line
for line in input_open:
	line = line.strip().split(';')
	#add zeros to milliseconds to ensure it is 6 digits
	line[2] = add_zero(line[2])
	#concatenate time string
	curtime = int(''.join((line[1], line[2])))
	#getting node and Xdisplay number ex. cave001:0.0
	node = line[3]
	#getting event type, ex. event, cached-preload
	event_type = line[4]
	#getting event type, ex. Head_Tracker
	event_name = line[5]



	#if event name is preint but not in the dict
	#initiate the key and continue reading
	if event_name == 'preinit' and node not in init:
		init[node] = [curtime]
		continue

	if event_name == "preint" and node in init:
		init[node] += [curtime]
		continue

	#if event name is postint
	#calculate the difference and push the val back into the dict
	if event_name == 'postinit':
		prev_time = init[node].pop()
		diff = curtime - prev_time
		init[node] += [diff]
		continue


	if event_type == "noncached-preload" and node not in noncached_load_file:
		noncached_load_file[node] = [curtime]
		continue

	if event_type == "noncached-preload" and node in noncached_load_file:
		noncached_load_file[node] += [curtime]
		continue

	if event_type == "cached-preload" and node not in cached_load_file:
		cached_load_file[node] = [curtime]
		continue

	if event_type == "cached-preload" and node in cached_load_file:
		cached_load_file[node] += [curtime]
		continue

	if event_type == "noncached-postload":
		prev_time = noncached_load_file[node].pop()
		diff = (curtime - prev_time) * 0.000001
		fileSize = float(line[6][:-2])
		speed = float(fileSize / diff)
		noncached_load_file[node] += [speed]
		continue

	if event_type == "cached-postload":
		prev_time = cached_load_file[node].pop()
		diff = (curtime - prev_time) * 0.000001
		fileSize = float(line[6][:-2])
		speed = float(fileSize / diff) 
		cached_load_file[node] += [speed]
		continue

	if event_name != 'Head_Tracker':
		continue

	#if event is head trackers but not in the dict
	#initiate the key and continue reading
	if event_name == "Head_Tracker" and node not in head_tracker:
		head_tracker[node]  = [curtime]
		continue

	if event_name == "Head_Tracker" and node in head_tracker:		
		prev_time = head_tracker[node].pop()
		diff = curtime - prev_time
		head_tracker[node] += [diff, curtime]
		continue



# sort all dictionaries based on node names in ascending order
head_tracker = collections.OrderedDict(sorted(head_tracker.items()))
init = collections.OrderedDict(sorted(init.items()))
cached_load_file = collections.OrderedDict(sorted(cached_load_file.items()))
noncached_load_file = collections.OrderedDict(sorted(noncached_load_file.items()))


	
#calculate average, min, max and standard deviation of initiation time
output_open.write("Average program init time of each node: \n")
for key, val in init.iteritems():
	newline = str(key) + ", " + str(val[0]) + "\n" 
	avg_init.append(int(val[0]))
	output_open.write(newline)

avg = str(np.mean(avg_init))
min_val = str(np.amin(avg_init))
max_val = str(np.amax(avg_init))
std_val = str(np.std(avg_init))
newline = "Average init overall: " + avg + "\n" +  "Min init time: " + min_val + "\n" + "Max init time: " + max_val + "\n" + "Standard Deviation: " + std_val + "\n\n"
output_open.write(newline)


#calculate average, min, max and standard deviation of non-cached reading speed
output_open.write("Average non-cached load time of each node: \n")
for key, val in noncached_load_file.iteritems():
	avg = np.mean(val)
	noncached_load_file[key] = avg
	newline = str(key) + ", " + str(avg) + " MB/s" + "\n" 
	avg_noncached.append(avg)
	output_open.write(newline)

avg = str(np.mean(avg_noncached))
min_val = str(np.amin(avg_noncached))
max_val = str(np.amax(avg_noncached))
std_val = str(np.std(avg_noncached))
newline = "Average non-cached overall: " + avg + " MB/s\n" +  "Min non-cached reading speed: " + min_val + " MB/s\n" + "Max non-cached reading speed: " + max_val + " MB/s\n" + "Standard Deviation: " + std_val + " MB/s\n\n"
output_open.write(newline)


#calculate average, min, max and standard deviation of cached reading speed
output_open.write("Average cached load time of each node: \n")
for key, val in noncached_load_file.iteritems():
	avg = np.mean(val)
	cached_load_file[key] = avg
	newline = str(key) + ", " + str(avg) + " MB/s\n" 
	avg_cached.append(float(avg))
	output_open.write(newline)
avg = str(np.mean(avg_cached))
min_val = str(np.amin(avg_cached))
max_val = str(np.amax(avg_cached))
std_val = str(np.std(avg_cached))
newline = "Average cached overall: " + avg + " MB/s\n" +  "Min cached reading speed: " + min_val + " MB/s\n" + "Max cached reading speed: " + max_val + " MB/s\n" + "Standard Deviation: " + std_val + " MB/s\n\n"
output_open.write(newline)



#calculate average, min, max and standard deviation of head tracking time
output_open.write("\nAverage Head Tracking time of each node: \n")
for key, val in head_tracker.iteritems():
	if (val[len(val) - 1] > 1451606400):
		val.pop()
	avg = np.mean(val)
	head_tracker[key] = avg
	avg_tracking.append(avg)
	newline = str(key) + ", " + str(avg) + "\n" 
	output_open.write(newline)
avg = str(np.mean(avg_tracking))
min_val = str(np.amin(avg_tracking))
max_val = str(np.amax(avg_tracking))
std_val = str(np.std(avg_tracking))
newline = "Average Head Tracking overall: " + avg + " \n" +  "Min head tracking time: " + min_val + " \n" + "Max head tracking time: " + max_val + " \n" + "Standard Deviation: " + std_val + "\n"
output_open.write(newline)