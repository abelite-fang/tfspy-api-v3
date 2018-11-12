# ---------------------- 
#
# run inference script
#    by follow the config.txt
# ----------------------

import os
import json
import base64
import tensorflow as tf

PATH = os.path.dirname(os.path.abspath(__file__)) + '/models/'

def config_model(self,modelName):
	with open('config.json', 'rt') as f:
		j = json.load(f)
		serialNumber = 1
		print(j[0])
		for name in j:
			print(name['name'])
			if name['name'] == modelName:
				serialNumber = name['version']
	return serialNumber



class tf_inference():
	def __init__(self):
		self.sess = tf.Session(graph=tf.Graph())
		self.signature_key = 'predict'
		self.input_key = 'image_bytes'
		self.output_key = 'probabilities'

	def config_model(self,modelName):
		with open('config.json', 'rt') as f:
			j = json.load(f)
			serialNumber = 1
			print(j[0])
			for name in j:
				print(name['name'])
				if name['name'] == modelName:
					serialNumber = name['version']
		return serialNumber

	def deeper(self, path, listofInference):
		meta_graph_def = tf.saved_model.load(self.sess,['serve'],path)
		signature = meta_graph_def.signature_def
		print(self.signature_key)
		x_tensor_name = signature[self.signature_key].inputs[self.input_key].name
		y_tensor_name = signature[self.signature_key].outputs[self.output_key].name
		print(x_tensor_name)
		print(y_tensor_name)
		x = self.sess.graph.get_tensor_by_name(x_tensor_name)
		y = self.sess.graph.get_tensor_by_name(y_tensor_name)
		print(x)
		print(y)
		#print(listofInference.data)
		#print(listofInference.stream)
		#print(listofInference['file'])
		for l in listofInference.getlist('file'):
			data = base64.b64encode(l.stream.read())
			print(type(data))
			#_x = tf.decode_base64(data)
			_x = str(data) 
			#_x = tf.constant(data)
			print(type(_x))
			#print(_x)
			#_x = str(base64.b64encode(l.stream.read()))
			#print(type(_x))
			print('ininininin')
			re = self.sess.run(y , feed_dict={x:_x})
			#print(y)
			#print(_y)
		return re


	def infer(self, modelName, listofInference):
		global PATH
		self.modelName = modelName
		print(self.modelName)
		serial = self.config_model(modelName)
		path = PATH + modelName + '/' + str(serial)
		re = self.deeper(path, listofInference)
		print('*' * 20)
		#print(re)
		print('*' * 20)
		return "hi" 

