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
import tensorflow as tf
from tensorflow.python.platform import gfile
from tensorflow.core.protobuf import saved_model_pb2
from tensorflow.python.util import compat

'''
try:
    import gpu_utils
    gpu_exist = 1
except:
    print("no gpu_utils")
    gpu_exist = 0
'''

try:
		from pynvml import *
		use_pynvml = 1
		print("use pynvml")
except:
		use_pynvml = 0
		print("no pynvml")


PATH = os.path.dirname(os.path.abspath(__file__)) + '/models/'


class tf_inference():
	def readConfig(self):
		global PATH
		with open('config.json', 'rt') as f:
			print('file config.json loading')
			js = json.load(f)
			print('json load = ')
			print(js)
			version = 0
			for models in js:
				try: 
					version = models['version']
					print('get model version from json file, version:', version)
				except:
					dirs = os.listdir(models['base_path'])
					dirs.sort()
					version = int(float(dirs[-1]))
					print('no version info in file, get from dirctory sturcture, version:', version)
				path = models['base_path'] + '/' + str(version)
				pb_file = path + "/saved_model.pb"
				#with gfile.FastGFile(pb_file, 'rb') as pb:
				print(pb_file)
				with gfile.FastGFile(pb_file, 'rb') as pb:
					data = compat.as_bytes(pb.read())
					sm = saved_model_pb2.SavedModel()
					sm.ParseFromString(data)
				#	print("("*30)
				#	print(type(sm))
				#	parsed = json.loads(str(sm))
				#	print(parsed)
				#	for i in sm.meta_graphs:
				#		print("-" * 30)
				#		print(i)
				#	print(sm.meta_graphs)
				'''     Next Test     '''
				'''
					try:
						print(sm.meta_graphs[5])
					except:
						print("no 0")
					print("\)" * 30)
					try:
						print(sm.meta_graphs[0].signature_def["predict"].inputs)
					except:
						print("no 1")
					try:
						print(sm.meta_graphs[0].signature_def["predict"])
					except:
						print("no 1")
					pass
				'''
				#	graph_def = tf.GraphDef()
				#	print("&" * 30)
				#	print(pb.read())
				#	graph_def.ParseFromString(pb.read().strip())
				#	graph_def.ParseFromString(pb.read())
				#	print("-" * 30)
				#	print(graph_def)
				#	print("-" * 30)
					

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
				#with tf.device(	
				meta_graph_def = tf.saved_model.load(self.sess,['serve'],path)
				self.meta_graph_defss[models['name']] = meta_graph_def
				#print(type(meta_graph_def))


	def detect_gpu(self):
		try:
			nvmlInit()
		except:
			print('nvmlInit failed, use cpu only')
			return
		self.freeGPU = []
		try:
			nvmlDeviceGetCount()
		except NVMLError as error:
			print(error)
		deviceCount = nvmlDeviceGetCount()

		print("deviceCount = ", deviceCount)
		for i in range(deviceCount):
			handle = nvmlDeviceGetHandleByIndex(i)
			mem = nvmlDeviceGetMemoryInfo(handle)
			print(mem.free/mem.total)
			if (mem.free/mem.total) >= 0.5:
				self.freeGPU.append(i)

		os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
		if self.freeGPU != '':
			os.environ["CUDA_VISIBLE_DEVICES"]=str(self.freeGPU[0])
			print(self.freeGPU[0])
       
		self.gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=memory*0.9)

	def workable(self):
		return self.Workable
	def on(self):
		self.Workable = 1
		return self.Workable
	def off(self):
		self.Workable = 0
		return self.Workable


	def __init__(self, memory):
		self.Workable = 0
		os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"]="python"
		if use_pynvml:
			# if using pynvml, can select one gpu
			self.detect_gpu() # self Func
		
		self.config=tf.ConfigProto(log_device_placement=False)
		self.sess = tf.Session(graph=tf.Graph(), config=self.config)
		
		self.meta_graph_defss = dict()
		self.modelConfigs = dict()
		# self Func
		self.readConfig()


		self.signature_key = 'predict'
		self.input_key = 'image_bytes'
		self.output_key = []
		self.output_key.append('probabilities')
		self.output_key.append('classes')
		self.Workable = 1


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
	
	def deeper(self, path, listofInference, modelName):
		global Workable
		self.Workable = 0
		print(self.meta_graph_defss[modelName].signature_def)
		signature = self.meta_graph_defss[modelName].signature_def
		x_tensor_name = signature[self.signature_key].inputs[self.input_key].name
		y = []
		y_tensor_name = []
		y_tensor_name.append(signature[self.signature_key].outputs[self.output_key[0]].name)
		y_tensor_name.append(signature[self.signature_key].outputs[self.output_key[1]].name)
		x = self.sess.graph.get_tensor_by_name(x_tensor_name)

		y.append(self.sess.graph.get_tensor_by_name(y_tensor_name[0]))
		y.append(self.sess.graph.get_tensor_by_name(y_tensor_name[1]))
		
		output = []
    
		for l in listofInference.getlist('file'):
			data = l.stream.read()

			c = self.sess.run( y , feed_dict={x:(data,)})
			
			for i in range(len(c)):
				if isinstance(c[i][0], numpy.ndarray):
					output.append( { self.output_key[i]: c[i][0].tolist()} )	
				elif isinstance(c[i][0], numpy.int64):
					#print(type(c[i][0].item()))
					output.append( { self.output_key[i]: c[i][0].item()} )	
				else:
					output.append( { self.output_key[i]: c[i][0]} )
			
			tf.reset_default_graph()
		self.Workable = 1
		return output


	def infer(self, modelName, listofInference):
		global PATH
		print('Inference get')
		self.Workable = 0
		self.modelName = modelName
		print(self.modelName)
		serial = self.config_model(modelName)
		path = PATH + modelName + '/' + str(serial)
		re = self.deeper(path, listofInference, modelName)
		print('inference return to service')
		return re

