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


tf_inference = tf1.tf_inference(0.3)

# Global
app = Flask(__name__)
scheduler = BackgroundScheduler()

### Functions
# Call Registry for Updating Config
def update_reg():
	global app
	now = datetime.datetime.now()
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
	tf_inference.off()
	re = tf_inference.infer(modelName, request.files)
	tf_inference.on()
	return json.dumps(re)




@app.route('/v1/available', methods=['GET'])
def	healthcheck(): 
#	print("tf1 Workable = ", tf_inference.Workable)
	return jsonify({'workable':tf_inference.workable()})


@app.route('/v1/on')
def on():
	return jsonify({'workable': tf_inference.on()})

@app.route('/v1/off')
def off():
	return jsonify({'workable': tf_inference.off()})

#----------------------------------------------------------
#|			Initialize			  |
#----------------------------------------------------------
if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Inference Service",
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
	#app.debug = True

	# Set Logs 
	directory = 'log'
	if not os.path.exists(directory):
		os.makedirs(directory)
	formatter = logging.Formatter(
		"[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
	handler = logging.FileHandler('log/service.log', encoding='UTF-8')
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(formatter)
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.DEBUG)
	log.addHandler(handler)
	app.logger.addHandler(handler)

	app.secret_key = 'v3superkey'
	app.config['SESSION_TYPE'] = 'filesystem'
	#print(parsed.port)
	#print(type(parsed.port))
	if isinstance(parsed.port, list):
		parsed.port = int(parsed.port[0])
	app.run(host=parsed.host, port=parsed.port, debug=False)
