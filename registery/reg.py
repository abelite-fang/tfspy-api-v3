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
#from apscheduler.schedulers.background import BackgroundScheduler


save_location = '0'
app = Flask(__name__)

@app.route('/v1/config', methods=['GET'])
def config_response():
	print(save_location)
	with open(save_location) as f:
		data = json.load(f)
		print(data)
	return jsonify(data)






if __name__ == "__main__":
	# Default path of saving files
	dirsave = []
	dirsave.append(os.path.abspath(os.path.dirname(__file__)) + '/config.json')

	parser = argparse.ArgumentParser(
		description="Reg",
		epilog='Developed by Wei Cheng \'dyingapple\' Fang')
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
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	
	handler = logging.FileHandler('reg.log', encoding='UTF-8')
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(formatter)
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.DEBUG)
	log.addHandler(handler)
	app.logger.addHandler(handler)


	app.secret_key = 'v3superkey'
	app.config['SESSION_TYPE'] = 'filesystem'
	app.run(host=parsed.host, port=parsed.port, debug=True, use_reloader=True)