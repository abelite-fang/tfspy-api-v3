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
		self.output_key1 = 'probabilities'
		self.output_key2 = 'classes'

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
		y1_tensor_name = signature[self.signature_key].outputs[self.output_key1].name
		y2_tensor_name = signature[self.signature_key].outputs[self.output_key2].name
		print(x_tensor_name)
		print(y1_tensor_name)
		print(y2_tensor_name)
		x = self.sess.graph.get_tensor_by_name(x_tensor_name)
		y1 = self.sess.graph.get_tensor_by_name(y1_tensor_name)
		y2 = self.sess.graph.get_tensor_by_name(y2_tensor_name)
		print(x)
		print(y1)
		print(y2)
		#print(listofInference.data)
		print(listofInference.getlist('file'))

		output = []
		for l in listofInference.getlist('file'):
			print(l)
			data = l.stream.read()
			#print(type(data))
			
			#_x = tf.convert_to_tensor(l.stream.read(), dtype=tf.string)
			#_x = tf.image.decode_image(l.stream.read())
			#_x = tf.decode_base64(data)
			#_x = str(data) 
			#_x = tf.constant(data)
			#print(_x)
			#print(_x)
			#_x = str(base64.b64encode(l.stream.read()))
			#print(type(_x))
			print('ininininin')

			a, b = self.sess.run( [y1,y2] , feed_dict={x:(data,)})
			output.append([a,b])
			#print(y)
			#print(_y)
		return output


	def infer(self, modelName, listofInference):
		global PATH
		self.modelName = modelName
		print(self.modelName)
		serial = self.config_model(modelName)
		path = PATH + modelName + '/' + str(serial)
		re = self.deeper(path, listofInference)
		print('*' * 20)
		print(re)
		print('*' * 20)
		return "hi" 

