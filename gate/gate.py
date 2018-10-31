#!/usr/bin/python3
import os
import json
import uuid
import time
import sched
import logging
import argparse
import datetime
from flask import Flask, jsonify, request, redirect
from werkzeug import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler

# Global
save_location = '0'
app = Flask(__name__)
scheduler = BackgroundScheduler()



# Call Registry for Updating Config

def update_reg():
	print('update_reg hit')
	
	now = datetime.datetime.now()
	logger.debug('Update Reg inFunction   time:', now)
	print(now)
	pass
scheduler.add_job(update_reg, 'interval', minutes=3)
scheduler.start()






def upload_record(uid, files, create_time):
	record = {'uuid':'0000', 'time':str(datetime.datetime.now()), 'file':'' }
	record['uuid'] = uid
	record['create_time'] = create_time
	record['file'] = files


	return 1

def save_file(files):
	global save_location
	tmp = files.getlist("file")
	spid = uuid.uuid4()
	directory = save_location + '/' + str(spid)
	if os.path.exists(directory):
		return 0
	os.makedirs(directory)

	for l in tmp:
		filename = secure_filename(l.filename)
		l.save(os.path.join(directory, l.filename))
	return spid







#----------------------------------------------------------
#|		    Client <---> API Gate		  |
#----------------------------------------------------------
# Client <--> API Gate
@app.route('/v1/models/<modelName>:<action>', methods=['POST'])
def v1_predict(modelName, action):
	debug = False
	d = debug


	if action == 'predict' and request.method == 'POST':
		if d == True : print(request.files)
		if 'file' not in request.files:
			return jsonify({'error':'no file'})
		spid = save_file(request.files)
		if spid == 0:
			return jsonify({'error':'uuid stuck or internal error'})
		create_time = datetime.datetime.now()
		content = request.json


		#print(create_time)
		#print(content)
		#queue_append(  )

		return jsonify({ modelName:action, 'UUID':spid})

	elif action == 'result' and request.method == 'GET':
		# Client GET result.
		pass
	elif action == 'report' and request.method == 'GET':
		# Dev Use
		pass
	else:
		# Wrong Methods or Actions.
		return jsonify({'error':'wrong action','action':'predict, result','method':'GET result, POST predict'})

	return jsonify({modelName:action})




#----------------------------------------------------------
#|		 API Gate <---> GPU Clusters		  |
#----------------------------------------------------------
@app.route('/v1/ser/<uuid:UUID>')
def v1_gpu(UUID):
	pass






#----------------------------------------------------------
#|		    Debug / Dev Function		  |
#----------------------------------------------------------
#@app.route('/v1/dev/help')
#def dev_help():
#	return jsonify({'help':'POST /dev/'})

@app.route('/v1/help')
def client_help():
	return jsonify({'do inference':'POST /v1/models/<modelName>:<method>', "models online":"GET /v1/help/models"})

@app.route('/v1/help/models')
def client_help_models():
	return jsonify({"Messages":"This Function Not Online Yet"})

@app.errorhandler(404)
def page404(e):
	return jsonify({'Get Help From':'GET /v1/help'})






#----------------------------------------------------------
#|			Initialize			  |
#----------------------------------------------------------
if __name__ == "__main__":
	dirsave = []
	dirsave.append(os.path.abspath(os.path.dirname(__file__)) + '/save')
	parser = argparse.ArgumentParser(
		description="API Gate of Self Designed Inference Service",
		epilog='Developed by Wei Cheng \'dyingapple\' Fang')
	parser.add_argument('--host',
		help="Host running IP, default=0.0.0.0",
		type=str,
		nargs=1,
		default='0.0.0.0')
	parser.add_argument('-p', '--port',
		help="Host running port, default=8501",
		type=str,
		nargs=1,
		default='8501')
	parser.add_argument('-s','--save',
		help="File saved location, default=.",
		type=str,
		nargs=1,
		default=dirsave)
	parsed, unparsed = parser.parse_known_args()

	save_location = os.path.abspath(parsed.save[0])
	if not os.path.exists(save_location):
		os.makedirs(save_location)



	handler = logging.FileHandler('gate.log')
	app.logger.addHandler(handler)
	app.logger.info('info log')
	app.logger.info('debug log')
	app.logger.info('warning log')
	app.logger.info('error log')
	app.logger.info('critical log')

	app.debug = True

	app.secret_key = 'v3superkey'
	app.config['SESSION_TYPE'] = 'filesystem'

	app.run(host=parsed.host, port=parsed.port, debug=True, use_reloader=True)
