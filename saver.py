import pickle
from threading import Thread
from time import sleep
from datetime import datetime

class Saver:
	def __init__(self, data, period=60, save_name='save.sv', to_start=False):
		self.data = data
		self.period = period
		self.save_name = save_name
		if to_start:
			self.start()
		self.to_stop = False
		self.last_save_datetime = None

	def start(self):
		thread = Thread(target=self.saving_process)
		thread.start()

	def saving_process(self):
		while not self.to_stop:
			self.save()
			self.last_save_datetime = datetime.now()
			sleep(self.period)

	def save(self):
		#print('q')
		try:
			file = open(self.save_name, 'wb')
			pickle.dump(self, file)
			file.close()
			#print('Saved!')
		except Exception as e:
			print('[!!!]', e)
			return 1

	def load(self):
		try:
			file = open(self.save_name, 'rb')
			#print('Loaded!')
			return pickle.load(file)
		except:
			print('[ ! ]', 'no save file found')
			return self