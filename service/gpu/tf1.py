# ---------------------- 
#
# run inference script
#    by follow the config.txt
# ----------------------

import os
import json
import numpy
import base64
import datetime
import gpu_utils
import threading
import tensorflow as tf
from pynvml import *
PATH = os.path.dirname(os.path.abspath(__file__)) + '/models/'

class tf_inference():
	def readConfig(self):
		global PATH
		with open('config.json', 'rt') as f:
			js = json.load(f)
			version = 0
			for models in js:
				try: 
					version = models['version']
				except:
					dirs = os.listdir(models['base_path'])
					dirs.sort()
					#print(dirs[-1])
					#print(type(dirs[-1]))
					version = int(float(dirs[-1]))
				path = models['base_path'] + '/' + str(version)
				#print('modelpath = ', path)
				keys = dict()
				input_key = []
				output_key = []
				input_key.append('image_bytes')
				output_key.append('probabilities') 
				output_key.append('classes')
				keys['input'] = input_key
				keys['output'] = output_key
				keys['path'] = path
				keys['version'] = int(float(version))
				#print('keys = ', keys)
				#print('models = ', models['name'])
				self.modelConfigs[models['name']] = keys
					
				meta_graph_def = tf.saved_model.load(self.sess,['serve'],path)
				self.meta_graph_defss[models['name']] = meta_graph_def
		
	def __init__(self, memory, device):
		nvmlInit()
		deviceCount = nvmlDeviceGetCount()
		print("deviceCount = ", deviceCount)
		
		
		self.gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.45)
		self.config=tf.ConfigProto(log_device_placement=False,gpu_options=self.gpu_options)
		self.sess = tf.Session(graph=tf.Graph(), config=self.config)
		
		self.meta_graph_defss = dict()
		self.modelConfigs = dict()
		self.readConfig()
		self.signature_key = 'predict'
		self.input_key = 'image_bytes'
		self.output_key = []
		self.output_key.append('probabilities')
		self.output_key.append('classes')
		


		# do thread
	def config_model(self,modelName):
		with open('config.json', 'rt') as f:
			path = ""
			j = json.load(f)
			serialNumber = 1
			
			#print(j[0])
			for name in j:
				#print(name['name'])
				if name['name'] == modelName:
					try:
						serialNumber = name['version']
					except:
						l = os.listdir(name['base_path'])
						l.sort()
						#print(l[-1])
						serialNumber = int(float(l[-1]))
					path = name['base_path']
		return serialNumber
	#def change_model(self, path, x[], y[])
	def deeper(self, path, listofInference, modelName):
		#a = datetime.datetime.now()
		#print('a = ', a)
		#meta_graph_def = tf.saved_model.load(self.sess,['serve'],path)
		
		#a1 = datetime.datetime.now()
		#print('a->a1 = ', a1-a)
		#signature = meta_graph_def.signature_def
		signature = self.meta_graph_defss[modelName].signature_def
		#print(self.signature_key)
		#a2 = datetime.datetime.now()
		#print('a1->a2 = ', a2-a1)
		x_tensor_name = signature[self.signature_key].inputs[self.input_key].name
		
		#a3 = datetime.datetime.now()
		#b = datetime.datetime.now()
		#print('a3->b = ', b-a3)
		#print('a->b = ', b-a)
		y = []
		y_tensor_name = []
		y_tensor_name.append(signature[self.signature_key].outputs[self.output_key[0]].name)
		y_tensor_name.append(signature[self.signature_key].outputs[self.output_key[1]].name)
		#c = datetime.datetime.now()
		#print('b->c = ', c-b)
		#y2_tensor_name = signature[self.signature_key].outputs[self.output_key2].name
		#print(x_tensor_name)
		#print(y1_tensor_name)
		#print(y2_tensor_name)
		x = self.sess.graph.get_tensor_by_name(x_tensor_name)

		#d = datetime.datetime.now()
		#print('c->d = ', d-c)
		y.append(self.sess.graph.get_tensor_by_name(y_tensor_name[0]))
		y.append(self.sess.graph.get_tensor_by_name(y_tensor_name[1]))
		
		#e = datetime.datetime.now()
		#print('d->e = ', e-d)
		#y1 = self.sess.graph.get_tensor_by_name(y1_tensor_name)
		#y2 = self.sess.graph.get_tensor_by_name(y2_tensor_name)
		#print(listofInference.getlist('file'))

		output = []
		#f = datetime.datetime.now()
		#print('e->f = ', f-e)
		for l in listofInference.getlist('file'):
			#print(l)
			#t1 = datetime.datetime.now()
			#print('f->t1 = ', f-t1)
			data = l.stream.read()
			#t2 = datetime.datetime.now()
			#print('t1->t2 = ', t2-t1)
			
			#_x = tf.convert_to_tensor(l.stream.read(), dtype=tf.string)
			#_x = tf.image.decode_image(l.stream.read())
			#_x = tf.decode_base64(data)
			#_x = str(data) 
			#_x = tf.constant(data)
			#_x = str(base64.b64encode(l.stream.read()))

			#a, b = self.sess.run( [y1,y2] , feed_dict={x:(data,)})
			c = self.sess.run( y , feed_dict={x:(data,)})
			
			#t3 = datetime.datetime.now()
			#print('t2->t3 = ', t3-t2)
			for i in range(len(c)):
				#if i != 0:
				if isinstance(c[i][0], numpy.ndarray):
					output.append( { self.output_key[i]: c[i][0].tolist()} )	
				elif isinstance(c[i][0], numpy.int64):
					#print(type(c[i][0].item()))
					output.append( { self.output_key[i]: c[i][0].item()} )	
				else:
					output.append( { self.output_key[i]: c[i][0]} )	
			
			tf.reset_default_graph()
			#t4 = datetime.datetime.now()
			#print('t3->t4 = ', t4-t3)
		return output


	def infer(self, modelName, listofInference):
		global PATH
		self.modelName = modelName
		print(self.modelName)
		serial = self.config_model(modelName)
		path = PATH + modelName + '/' + str(serial)
		re = self.deeper(path, listofInference, modelName)
		return re

