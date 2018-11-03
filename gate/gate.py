#!/usr/bin/python3
import os
import sys
import json
import uuid
import time
import sched
import logging
import argparse
import datetime
from flask import Flask, jsonify, request, redirect, Response
from werkzeug import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler



#----------------------------------------------------------
#|		   Global		  |
#----------------------------------------------------------
### Configs
save_location = '0'
app = Flask(__name__)
scheduler = BackgroundScheduler()



### Functions
# Call Registry for Updating Config
def update_reg():
	print('update_reg hit')
	#global logger
	global app
	now = datetime.datetime.now()
	#logger.info('update reg')
	print(now)
	pass
scheduler.add_job(update_reg, 'interval', minutes=1)
scheduler.start()






def upload_record(uid, files, createTime, modelName):
	global save_location
	record_file = save_location + "/record.json"
	record = {}


	with open(record_file , 'w+') as f:
		record['task'] = str(uid)
		record['time'] = str(createTime)
		if len(files.getlist("file")) == 1:
			record['file_id'] = str(uid)
			record['file_name'] = files.getlist("file")[0].filename
			f.write(json.dumps(record, sort_keys=True, indent=2,separators=(',',':')))
			f.write("," + "\n")
		else:
			for l in files.getlist("file"):
				record['file_id'] = str(uuid.uuid4())
				record['file_name'] = l.filename
				f.write(json.dumps(record, sort_keys=True, indent=2,separators=(',',':')))
				f.write("," + "\n")
	return 0


def save_file(files):
	global save_location
	tmp = files.getlist("file")
	spid = uuid.uuid4()
	directory = save_location + '/' + str(spid)
	if os.path.exists(directory):
		# Error: UUID Repeated
		return 0
	os.makedirs(directory)

	# Store every files from upload to UUID/sample.file
	for l in tmp:
		filename = secure_filename(l.filename)
		l.save(os.path.join(directory, l.filename))
	# Return a UUID as the taskID
	return spid







#----------------------------------------------------------
#|		    Client <---> API Gate		  |
#----------------------------------------------------------
# Client <--> API Gate
@app.route('/v1/models/<modelName>:<action>', methods=['POST'])
def v1_predict(modelName, action):
	global save_location
	print (save_location)

	if action == 'predict' and request.method == 'POST':
		if 'file' not in request.files:
			return Response("{'error':'no file', 'usage':'Please add key:file in the header'}", status=406, mimetype='application/json')
		spid = save_file(request.files)
		if spid == 0:
			return Response("{'error':'uuid repeated or internal error, please try again'}", status=500, mimetype='application/json')
		# Else: no error, then 
		print(spid)

		createTime = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=8)))
		content = request.json
		# record 
		upload_record(spid, request.files, createTime, modelName)

		return jsonify({ modelName:action, 'UUID':spid})

	elif action == 'result' and request.method == 'GET':
		if 'file' not in request.files:
			return Response("{'error':'no id for request', 'usage':'Please add id:id in the header'}", status=406, mimetype='application/json')
		# Client GET result.
		pass
	elif action == 'report' and request.method == 'GET':
		# Dev Use
		pass
	else:
		# Wrong Methods or Actions.
		return Response("{'error':'wrong action','action':'predict, result','method':'GET result, POST predict'}", status=500, mimetype='application/json')
		
	# For Now
	return jsonify({modelName:action})




#----------------------------------------------------------
#|		 API Gate <---> GPU Clusters		  |
#----------------------------------------------------------
@app.route('/v1/ser/<uuid:UUID>')
def v1_gpu(UUID):
	#with open()
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
	# Default path of saving files
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


	# Set Logs 
	#formatter = logging.Formatter(
	#	"[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	
	handler = logging.FileHandler('gate.log', encoding='UTF-8')
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(formatter)
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.DEBUG)
	log.addHandler(handler)
	app.logger.addHandler(handler)


	app.secret_key = 'v3superkey'
	app.config['SESSION_TYPE'] = 'filesystem'
	app.run(host=parsed.host, port=parsed.port, debug=True, use_reloader=True)
