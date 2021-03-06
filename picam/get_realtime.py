import picamera
from mcp3208 import MCP3208
import datetime as dt
import time
import sys
import signal
import os
from multiprocessing import Process
#6
import tensorflow as tf
import pandas as pd
import json
import numpy as np
from firebase import firebase
#
class NumpyEncoder(json.JSONEncoder):
		def default(self, obj):
			if isinstance(obj, np.ndarray):
				return obj.tolist()
			return json.JSONEncoder.default(self, obj)

#Import Datasets & set datasets
firebase = firebase.FirebaseApplication('https://pnu-dubleve.firebaseio.com')

adc = MCP3208()

g_data = " "
g_cnt = 0
g_dtime = 0
g_sr = 0
g_dt = 0

g_disk = os.statvfs("/")
g_first_avail = g_disk.f_bsize * g_disk.f_bavail

#fname = "data"+str(dt.datetime.now())+".txt"
#f=open(fname, "w")

s_buff = ''
r_buff = list()
room_buff = list()

#ret_flag = False # Ture: complete, False: keep going!

def sender():
	while True:
		try:
#			print("hello, I'm sender!")

			dtime = time.time()-start_time
			mydt = long(dtime*1000)/10
			cdt = int(mydt%100)

			global pdt
			global cnt

			if cdt!=pdt: # read datas for 0.01 second
				read = adc.read(6)
				sr = cnt/dtime
				#data = data + str(read) + " "
				data = str(read)
				pdt = cdt
					
				buff.append(map(int, data.split()))
				print "num of buff: ", len(buff), ", cnt: ", cnt
						
				if len(buff)>=100 :
					ret_flag = True
					cnt = cnt + 1
					s_buff = buff[first_idx:last_idx]
					if cnt==15: # for 0.15 second
							# for removing first 15 datas of list
						buff.reverse()
						for i in range(15):
							buff.pop()
						buff.reverse()

						s_buff = sum(s_buff, []) # 2 dimension list to 1 dimension list

						print "s_buff: ", s_buff

#						room_buff.append(s_buff)

						del s_buff[:]
						cnt = 0
					
		#			cam.annotate_text = (dt.datetime.now().strftime('%m-%d %H:%M:%S.%f')[:-4]
		#			+ " sr : " + str(round(sr, 1)) + " sn : " + str(cnt) + "\npir : " + data[0:30])

			if cdt==0: # write datas in file for 1 second
#				f.write(data)
				data = ""
				print "sr", sr, "dt", str(dt.datetime.now())

			avail = g_disk.f_bsize * g_disk.f_bavail

			if avail < (g_first_avail * 3 / 5) :
				raise KeyboardInterrupt

		except KeyboardInterrupt:
			break

def receiver():


	while True:

#		print("Nice to meet you!")
		X_data = room_buff[0]

		X = tf.placeholder(tf.float32)

		W1 = tf.Variable(tf.random_uniform([100, 50], -1., 1.))
		W2 = tf.Variable(tf.random_uniform([50, 2], -1., 1.))
		b1 = tf.Variable(tf.zeros([50]))
		b2 = tf.Variable(tf.zeros([2]))

		L1 = tf.add(tf.matmul(X, W1), b1)
		Y = tf.nn.softmax(tf.matmul(L1, W2) + b2)

		sess = tf.Session()

		#tf.reset_default_graph()
		with tf.Session() as sess:
			saver = tf.train.Saver()
			sess.run(tf.global_variables_initializer())

			ckpt_path = saver.restore(sess, tf.train.latest_checkpoint("./model"))
			init_op = tf.global_variables_initializer()
			sess.run(init_op)
			predictions = sess.run(Y, feed_dict={X:X_data})

			print(predictions)

			for i in range(len(predictions)):
				if str(predictions[i]) == "[1. 0.]":
					print('exist')
				else:
					print('not exist')

#			ret_flag = True

if __name__ == '__main__':
	#signal.signal(signal.SIGUSR1, getpir)

	#os.kill(os.getpid(),signal.SIGUSR1)
	pid = os.fork()

	mydt = 0
	pdt = 0
	sr = 0
	cnt = 0
	data = ''

	p_send = Process(target=sender)
	p_recv = Process(target=receiver)

	buff = list() # buffer that collects datas(more than 100 datas)			
#	s_buff = list() # buffer for sending datas

	first_idx = 0
	last_idx = first_idx + 99

	start_time = time.time()

	if pid == 0:
		p_send.start()
		p_recv.start()
		p_send.join()	
		p_recv.join()

#	f.close()