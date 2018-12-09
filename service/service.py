#!/usr/bin/python3
import os
import json
import uuid
import time
import logging
import argparse
import datetime
import tensorflow as tf
import numpy
from flask import Flask, jsonify, request, redirect
from werkzeug import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
#from gpu.tf1 import *
from gpu import tf1
from gpu import tf2


tfinfer = tf1.tf_inference(1, 2)
tfinfer2 = tf2.tf_inference()

# Global
app = Flask(__name__)
scheduler = BackgroundScheduler()


### Functions
# Call Registry for Updating Config
def update_reg():
	#print('update_reg hit')
	global app
	now = datetime.datetime.now()
	#print(now)
	pass
scheduler.add_job(update_reg, 'interval', minutes=1)
scheduler.start()


#with tf.Session() as sess:
@app.route('/v1', methods=['GET'])
def hello():
	return jsonify({'messages':'hello'})
	pass
@app.route('/v1/tasks/<modelName>', methods=['POST'])
def taskin(modelName):
	#request.files
	#print('taskin 1')
	#print(request.data)
	#print(request.form)
	#print(request.files)

	#print('taskin 2')#request.files
	re = tfinfer.infer(modelName, request.files)
	#print("rerererer")
	#print(type(re))
	#print(re)
	#return jsonify({'message':re})
	return json.dumps(re)


@app.route('/v1/healthcheck', methods=['GET'])
def healthcheck():
	return jsonify({'messages':'ssss'})





#----------------------------------------------------------
#|			Initialize			  |
#----------------------------------------------------------
if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Inference Service",
		epilog='Developed by Wei Cheng \'dyingapple\' Fang')
	parser.add_argument('--host',
		help="Host running IP, default=0.0.0.0",
		type=str,
		nargs=1,
		default='0.0.0.0')
	parser.add_argument('-p', '--port',
		help="Host running port, default=8500",
		type=int,
		nargs=1,
		default=8500)
	parser.add_argument('-f','--file',
		help="Config file saved location, default=config.txt",
		type=str,
		nargs=1,
		default='config.txt')
	parsed, unparsed = parser.parse_known_args()
	configFile = os.path.abspath(parsed.file[0])
	app.debug = True

	# Set Logs 
	formatter = logging.Formatter(
		"[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
	handler = logging.FileHandler('service.log', encoding='UTF-8')
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(formatter)
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.DEBUG)
	log.addHandler(handler)
	app.logger.addHandler(handler)

	app.secret_key = 'v3superkey'
	app.config['SESSION_TYPE'] = 'filesystem'
	print(parsed.port)
	print(type(parsed.port))
	if isinstance(parsed.port, list):
		parsed.port = int(parsed.port[0])
	app.run(host=parsed.host, port=parsed.port, debug=False)
