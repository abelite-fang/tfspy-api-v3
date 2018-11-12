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
import requests
import base64
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
	#print('update_reg hit')
	global app
	now = datetime.datetime.now()
	print(now)
	pass
scheduler.add_job(update_reg, 'interval', minutes=1)
scheduler.start()




def upload_record(uid, files, createTime, modelName):
	global save_location
	record_file = save_location + "/record.json"
	resp = []
	record = {}
	'''
	 Save metadata into two parts for client to dig
	  1. Task ID
	  2. File ID
	'''
	with open(record_file , 'w+') as f:
		record['task'] = str(uid)
		record['time'] = str(createTime)
		# If > one file, create id for each file_id, if only one -> file_id = task_id
		if len(files.getlist("file")) == 1:
			record['file_id'] = str(uid)
			record['file_name'] = files.getlist("file")[0].filename
			f.write(json.dumps(record, sort_keys=True, indent=2,separators=(',',':')))
			f.write("," + "\n")
			resp.append(record)
		else:
			for l in files.getlist("file"):
				record['file_id'] = str(uuid.uuid4())
				record['file_name'] = l.filename
				f.write(json.dumps(record, sort_keys=True, indent=2,separators=(',',':')))
				f.write("," + "\n")
				resp.append(record)
	return resp


def save_file(files):
	global save_location
	print(files)
	print('!' * 10)
	tmp = files.getlist("file")
	print(tmp)
	spid = uuid.uuid4()
	directory = save_location + '/' + str(spid)
	if os.path.exists(directory):
		# Error: UUID Repeated
		return 0
	os.makedirs(directory)

	# Store every files from upload to UUID/filename
	for l in tmp:
		filename = secure_filename(l.filename)
		l.save(os.path.join(directory, l.filename))
		# Return a UUID as the taskID
	return spid  






#----------------------------------------------------------
#|		    Client <---> API Gate		  |
#----------------------------------------------------------
# Client <--> API Gate
@app.route('/v1/models/<modelName>', methods=['GET','POST'])
def v1_predict(modelName):
	global save_location
	print (save_location)
	print(request.method)
	if request.method == 'POST':
		print("-d Predict")
		if 'file' not in request.files:
			msg = "{'error':'no file', 'usage':'Please add key:file value=file in the body of file=@filename from curl'}"
			code = 406
			return Response(msg, status=code, mimetype='application/json')
		spid = save_file(request.files)

		if spid == 0:
			msg = "{'error':'uuid repeated or internal error, please try again'}"
			code = 500
			return Response(msg, status=code, mimetype='application/json')
		

		# set time to UTC+8
		createTime = datetime.datetime.utcnow().replace(
			tzinfo=datetime.timezone.utc).astimezone(
				datetime.timezone(datetime.timedelta(hours=8)))

		content = request.json
		resp = upload_record(spid, request.files, createTime, modelName)
		print(resp)
		url = 'http://localhost:8500/v1/tasks'
		files = []
		for l in resp:
			print(l)
			loca = save_location+'/'+str(spid)+'/'+l['file_name']
			files.append( ('file',( l['file_id'], open(loca, 'rb'))) )
		print(files)
		res = requests.post(url, files=files)
		print(res)
		# send()
		return jsonify({ modelName:modelName, 'UUID':spid})

	elif request.method == 'GET':
		if 'id' not in request.headers:
			msg = "{'error':'no ID for request', 'usage':'Please add ID: file_id or task_id in the header'}"
			code = 406
			return Response(msg, status=code, mimetype='application/json')
		print(request.headers.get('id'))
		# Client GET result.

		pass
#	elif action == 'report' and request.method == 'GET':
#		print("-d Report")
#		# Dev Use
#		pass
	else:
		# Wrong Methods or Actions.
		msg = "{'error':'wrong action','action':'predict, result','method':'GET result, POST predict'}"
		code = 500
		return Response(msg, status=code, mimetype='application/json')
		
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
