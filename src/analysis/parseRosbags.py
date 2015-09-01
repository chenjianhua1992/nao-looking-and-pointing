#!/usr/bin/env python

"""
Author: Henny Admoni 
Date Created: 8/31/2015

Analyze rosbags from NVB experiment. 
"""
import sys
import argparse
import glob
import re
import rosbag

#bagfile = '../rosbags/p0_2015-08-31-16-04-56.bag'

def printMessages(bag, topicslist):

	for topic, msg, t in bag.read_messages(
		topics=topicslist):
		print '---' + str(t) + '---'
		print topic
		print msg

	bag.close()

def system_validation(bag):
	""" 
	Do people touch the correct block? And how quickly do they do so?

	Measures accuracy of block touches for different NVB actions, as 
	well as response times for *correct* block touches.

	Returns a list of accuracies and a list of RTs by block.
	"""
	print("----- System validation analysis -----")

	# Possible actions of the robot
	action_list = ['none','look','point','lookandpoint']

	# Time window for correct response in seconds
	t_window = 4.0

	# trackers
	start_time = None
	target_obj = None
	nvb_action = None

	# totals
	total_actions = dict((act,0.0) for act in action_list)
	accuracy = dict((act,0.0) for act in action_list)
	responsetime = dict((act,0.0) for act in action_list)

	# For each object reference, find whether people touch the
	# target object within t_window seconds of that reference.
	for topic, msg, t in bag.read_messages(
		topics=['human_behavior','robot_behavior','script_status']):
		if topic == 'script_status':
			if msg.data == 'HRIConstruction':
				break
		if topic == 'robot_behavior':
			# A new robot behavior was produced, so reset all
			# trackers (start_time, target_obj, nvb_action)
			start_time = t
			target_obj = msg.object_id
			nvb_action = msg.action
			total_actions[nvb_action] += 1
		elif (topic == 'human_behavior' 
			and not target_obj == None
			and t - start_time < t_window):
			# This human behavior followed a robot behavior
			# within the specified time window
			objlist = msg.target
			effectorlist = msg.effector
			assert len(objlist) > 0
			assert len(objlist) == len(effectorlist)
			for i in range(len(objlist)):
				if effectorlist[i] == 'leftarm' or \
					effectorlist[i] == 'rightarm':
					touch_obj = objlist[i]
					# If this is a successful touch, record the accuracy
					# and RTs and then reset all trackers (so we only save
					# the first such correct touch)
					if touch_obj == target_obj:
						assert nvb_action in action_list
						accuracy[nvb_action] += 1
						touch_time = t - start_time
						responsetime[nvb_action] += touch_time
						start_time = None
						target_obj = None
						nvb_action = None
						break # leave the for loop

	print "Raw data:"
	print "  total actions: " + str(total_actions)
	print "  accuracy: " + str(accuracy)
	print "  response times: " + str(responsetime)

	# Construct a data string that can be plugged into SPSS
	# format: subjID, none, look, point, lookandpoint
	accuracy_datastring = str(userid)
	rt_datastring = str(userid)

	# Calculate average accuracy and response time per NVB action
	for action in action_list:
		aveAcc = accuracy[action] / total_actions[action]
		aveRt = responsetime[action] / total_actions[action]
		accuracy_datastring += ', ' + str(aveAcc)
		rt_datastring += ', ' + str(aveRt)

	print "Calculated data:"
	print "  average accuracy: " + accuracy_datastring
	print "  average RTs: " + rt_datastring

	return [accuracy_datastring, rt_datastring]

def completionTimeTask1(bag):
	""" 
	Report completion time for task 1

	Returns a CSV with "condition, time".
	"""
	

if __name__ == '__main__':
	global userid, bagfile, bag

	parser = argparse.ArgumentParser(description="Analyze data from NVB experiment.")
	parser.add_argument('--bag',
		help='the bag file to analyze')
	parser.add_argument('--user',
		help='participant number',
		type=int)

	args = parser.parse_args()
	arg_userid = args.user
	arg_bagfname = args.bag

	rosbagdir = '../rosbags/'
	userid = None
	bagfile = None

	# Get bag file and user id
	if arg_bagfname is not None:
		bagfile = arg_bagfname
		userid = int(re.findall(r'\d+', arg_bagfname)[0]) # first integer
	elif arg_userid is not None:
		userid = arg_userid
		potential_files = glob.glob(rosbagdir+'p'+str(arg_userid)+'_*.bag')
		if len(potential_files) == 0:
			print("No file found for participant %d." % arg_userid)
			sys.exit()
		elif len(potential_files) == 1:
			bagfile = potential_files[0]
		else:
			print("More than one bag file for this participant, "
				"try running with bag filename directly.")
			sys.exit()

	bag = rosbag.Bag(bagfile)
	#printMessages(bag, ['human_behavior', 'robot_behavior'])
	system_validation(bag)