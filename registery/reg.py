#!/usr/bin/python3
import os
import sys
import json
#import uuid
import time
#import sched
import logging
import argparse
import datetime
import requests
from flask import Flask, jsonify, request, redirect, Response
from werkzeug import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler


save_location = '0'
app = Flask(__name__)
scheduler = BackgroundScheduler()

service_list = ['http://localhost:8500', 'http://cnh.ssh.abelite.ro:8500', 'http://ws.abelite.ro:8500']

def update_healthcheck():
	global service_list
	sort_list = []
	for host in service_list:
		url = host + '/v1/available'
		print(url)
		try:
			resp = requests.get(url)
			sort_list.append({resp.elapsed.total_seconds(): host})
		except:
			#print(resp.elapsed.total_seconds())
			sort_list.append({9999999: host})
	print(sort_list)

scheduler.add_job(update_healthcheck, 'interval', seconds=5 )
scheduler.start()

def list_sort():
	global service_list
	for hosts in service_list:
		url = hosts + '/v1/available'
		try:
			resp = requests.get(url)
			newList.insert({})
		except:
			continue
		


@app.route('/v1/config', methods=['GET'])
def config_response():
	print(save_location)
	with open(save_location) as f:
		data = json.load(f)
		print(data)
	return jsonify(data)

@app.route('/v1/check', methods=['GET'])
def health_response():
	global service_list
	now = datetime.datetime.now()
	for hosts in range(len(service_list)):
		url = service_list[hosts] + '/v1/available'
		try: 
			resp = requests.get(url)
			print(url)
		except:
			print(url, 'is down')
			continue
		#print(resp.elapsed.total_seconds())
		workable = json.loads(resp.text)['workable']
		if workable == 1:
			return jsonify({'sendto': service_list[hosts]})
	return jsonify({'sendto':"0"})




if __name__ == "__main__":
	# Default path of saving files
	dirsave = []
	dirsave.append(os.path.abspath(os.path.dirname(__file__)) + '/config.json')

	parser = argparse.ArgumentParser(
		description="Reg")
	parser.add_argument('--host',
		help="Host running IP, default=0.0.0.0",
		type=str,
		nargs=1,
		default='0.0.0.0')
	parser.add_argument('-p', '--port',
		help="Host running port, default=8502",
		type=str,
		nargs=1,
		default='8502')
	parser.add_argument('-s','--save',
		help="Config saved location, default=.",
		type=str,
		nargs=1,
		default=dirsave)
	parsed, unparsed = parser.parse_known_args()

	save_location = os.path.abspath(parsed.save[0])
	#if not os.path.exists(save_location):
	#	os.makedirs(save_location)


	# Set Logs 
	directory = 'log'
	if not os.path.exists(directory):
		os.makedirs(directory)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	
	handler = logging.FileHandler('log/reg.log', encoding='UTF-8')
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(formatter)
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.DEBUG)
	log.addHandler(handler)
	app.logger.addHandler(handler)


	app.secret_key = 'v3superkey'
	app.config['SESSION_TYPE'] = 'filesystem'
	app.run(host=parsed.host, port=parsed.port, debug=False, use_reloader=False)
