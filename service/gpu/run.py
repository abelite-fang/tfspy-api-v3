# ---------------------- 
#
# run inference script
#    by follow the config.txt
# ----------------------

import os
import tensorflow as tf

class tf_inference():
	def __init__(self):
		self.modelName = ""
		with tf.Session() as sess:
			pass
	def infer(self, modelName):
		self.modelName = modelName
		print(self.modelName)
		return "hi" 
