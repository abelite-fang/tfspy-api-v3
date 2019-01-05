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



# -------------------
#      Functions
# -------------------



def upload_record(taskID, files, createTime, modelName):
	global save_location
	record_file = save_location + "/record.json"
	record_list = []
	init_dict = {}
	'''
	 Save metadata into two parts for client to dig
	  1. Task ID
	  2. File ID
	'''
	with open(record_file , 'a') as f:
		init_dict['task'] = str(taskID)
		init_dict['time'] = str(createTime)
		# If > one file, create id for each file_id, if only one -> file_id = task_id
		if len(files.getlist("file")) == 1:
			'''
			One File,
			FileID = TaskID
			'''
			record = init_dict.copy()
			record['file_id'] = str(taskID)
			record['file_name'] = files.getlist("file")[0].filename
			record_list.append(record)
			f.write(json.dumps(record, sort_keys=True, indent=2,separators=(',',':')))
			f.write("," + "\n")
		else:
			'''
			Multiple Files,
			FileID != TaskID
			create new FileID for each
			'''
			for l in files.getlist("file"):
				
				record = init_dict.copy()
				record['file_id'] = str(uuid.uuid4())
				record['file_name'] = l.filename
				record_list.append(record)
				#print(record)
				f.write(json.dumps(record, sort_keys=True, indent=2,separators=(',',':')))
				f.write("," + "\n")
	return record_list



def save_file(files):
	global save_location
	tmp = files.getlist("file")
	taskID = uuid.uuid4()
	directory = save_location + '/' + str(taskID)
	if os.path.exists(directory):
		# Error: UUID Repeated
		return 0
	os.makedirs(directory)

	# Store every files from upload to UUID/filename
	for l in tmp:
		filename = secure_filename(l.filename)
		l.save(os.path.join(directory, l.filename))
		# Return a UUID as the taskID
	return taskID 

def service_list_available():
	resp = requests.get('http://localhost:8502/v1/check')
	sendto = json.loads(resp.text)['sendto']
	#print("sendto =", sendto)
	return sendto




#----------------------------------------------------------
#|		    Client <---> API Gate		  |
#----------------------------------------------------------
# Client <--> API Gate
@app.route('/v1/models/<modelName>', methods=['GET','POST'], strict_slashes=False)
def v1_predict(modelName):
	global save_location

	if request.method == 'POST':
		if 'file' not in request.files:
			msg = "{'error':'no file', 'usage':'Please add key:file value=file in the body of file=@filename from curl'}"
			code = 406
			return Response(msg, status=code, mimetype='application/json')
		taskID = save_file(request.files)

		if taskID == 0:
			msg = "{'error':'uuid repeated or internal error, please try again'}"
			code = 500
			return Response(msg, status=code, mimetype='application/json')

		''' set time to UTC+8 '''
		createTime = datetime.datetime.utcnow().replace(
			tzinfo=datetime.timezone.utc).astimezone(
				datetime.timezone(datetime.timedelta(hours=8)))

		content = request.json
		record_list = upload_record(taskID, request.files, createTime, modelName)

		url = service_list_available()
		while url == '0':
			''' no available service '''
			url = service_list_available()
		url = url + '/v1/tasks/' + modelName

		files = []
		for l in record_list:
			file_location = save_location+'/'+str(taskID)+'/'+l['file_name']
			files.append( ('file',( l['file_id'], open(file_location, 'rb'))) )
		respond = requests.post(url, files=files)

		if respond.status_code == 200:
			''' return successfully '''
			print('return@ ', datetime.datetime.now())
			return respond.text
		return jsonify({"messages":"error when receive from service"})

		''' BUG!!!!! '''
		print('c = ', datetime.datetime.now())
		return respond.text

	else:
		''' else need more funcs '''
		return jsonify({
			"message":"usage: POST /v1/models/<modelname> in form-data with \'file\' header or base64 content"})
#----------------------------------------------------------
#|		 API Gate <---> GPU Clusters		  |
#----------------------------------------------------------
@app.route('/v1/ser/<uuid:UUID>',strict_slashes=False)
def v1_gpu(UUID):
	#with open()
	pass


#----------------------------------------------------------
#|		    Debug / Dev Function		  |
#----------------------------------------------------------

@app.route('/v1/help',strict_slashes=False)
def client_help():
	return jsonify({'do inference':'POST /v1/models/<modelName>', "models online":"GET /v1/help/models"})

@app.route('/v1/help/models',strict_slashes=False)
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
		description="API Gate of Self Designed Inference Service")
	parser.add_argument('--host',
		help="Host running IP, default=0.0.0.0",
		type=str,
		nargs=1,
		default='0.0.0.0')
	parser.add_argument('-p','--port',
		help="Host running port, default=8501",
		type=int,
		nargs=1,
		default=8501)
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
	
	directory = "log"
	if not os.path.exists(directory):
		os.makedirs(directory)

	handler = logging.FileHandler('log/gate.log', encoding='UTF-8')
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(formatter)
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.DEBUG)
	log.addHandler(handler)
	app.logger.addHandler(handler)


	app.secret_key = 'v3superkey'
	app.config['SESSION_TYPE'] = 'filesystem'
	if isinstance(parsed.port, list):
		parsed.port = parsed.port[0]
	app.run(host=parsed.host, port=parsed.port, debug=False, use_reloader=True)
