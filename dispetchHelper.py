import datetime
import vk_api
import threading
#import BlinovBot
#import dispetchHelper

import time
from threading import Thread, Lock
#from random import random
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from array import *


def writeMsg(toId, text):
	Gvk.messages.send(
		user_id = toId,
		message = text,
		random_id = get_random_id()
	)

def writeHelp(toId):
	Gvk.messages.send(
		user_id = toId,
		message = 'Бот работает в коммандном режиме, поддерживаются комманды:' + 
		'\n\nПРИНЯТЬ Обязательные аргументы: <№заказа> <время выполнения в минутах> <Измененная стоимость>' +
		'\nПример: ПРИНЯТЬ 12 60 200 - Принимает заказ №12, устанавлевает время приготовления на 60 минут и устанавливает итоговую стоимость на 200 рублей' + 
		'\n\nОТКЛОНИТЬ Обязательные аргументы: <№заказа> <причина>' +
		'\nПример: ОТКЛОНИТЬ 10 Неверный адресс - отклоняет заказ №10 и отправляет пользователю сообщение об отклонении \"Неверный адресс\"' +
		'\n\nОТПРАВИТЬ Обязательные аргументы: <№заказа>' +
		'\nПример: ОТПАРВИТЬ 11 - отправляет пользователю сообщение о том, что курьер выехал' +
		'\n\nСправочное сообщение закончено',
		random_id = get_random_id()
	)

def writeToClient(toId, text):
	GtoClientVk.messages.send(
		user_id = toId,
		message = text,
		random_id = get_random_id()
	)
	return

def getArgs(text):
	args = text.split()
	return args

def findOrder(order_no):
	founded = False
	founded_int = 0

	for i in range(0, len(Gorders), 3):
		if(int(Gorders[i]) == int(order_no)):
			founded_int = i
			founded = True
			break

	if founded == False:
		return -1
	elif founded == True:
		return founded_int

class dispetchHelper(object):
	"""description of class"""
	
	global orders
	thread = None 

	def WaitForConfirmation(order_no):
		j = findOrder(order_no)
		if j == -1:
			writeMsg(Gdispetcher_id,"Заказ потерян!!!")
		else:
			time.sleep(10)
			if Gorders[j+3] == 'queue':
				writeToClient(Gorders[j+2], 'Ваш заказ отклонен, причина: ' + 'Ресторан не отвечает на сообщения, возможно это связано с тем, что они закрыты :(')
				writeMsg(Gdispetcher_id, 'Заказ отклонен: превышено время ожидания. Номер заказа: ' + str(order_no))
				Gorders[j+3] = 'declined'

	def mainCycle():
		for event in Glongpoll.listen():
			if event.type == VkBotEventType.MESSAGE_NEW:
				print('Новое сообщение диспетчеру')
				from_id = event.obj.message['from_id']
				text = event.obj.message['text']

				args = getArgs(text)
				if(Gdispetcher_id == from_id and len(args) > 0):
					if args[0].upper().startswith('ПРИНЯТЬ'):
						order_no = None
						working_time = None
						price = None
						if len(args) == 4:
							try:	
								order_no = int(args[1])
								working_time = int(args[2])
								price = int(args[3])
							except:
								writeMsg(from_id, 'Неверный синтаксис команды, попробуйте ещё раз')
						else:
							writeMsg(from_id, 'Неверный синтаксис команды, попробуйте ещё раз')

						j = findOrder(order_no)
						if j >= 0:
							writeToClient(Gorders[j+2], 'Ваш заказ принят на кухню: Окончательная стоимость с учетом доставки и акций: ' + price + ' Руб, Время приготовления: ' + working_time + ' минут')
							writeMsg(from_id, 'Заказ принят! Приступайте к приготовлению')
							Gorders[j+3] = 'working'
						else:
							writeMsg(from_id, 'Заказа не существует - это могло произойти из-за перезапуска программы')
							

					elif args[0].startswith('ОТКЛОНИТЬ'):
						order_no = None
						сomment = None
						if len(args) == 3:
							try:	
								order_no = int(args[1])
								comment = str(args[2])
							except:
								writeMsg(from_id, 'Неверный синтаксис команды, попробуйте ещё раз')
						else:
							writeMsg(from_id, 'Неверный синтаксис команды, попробуйте ещё раз')

						j = findOrder(order_no)
						if j >= 0:
							writeToClient(Gorders[j+2], 'Ваш заказ отклонен, причина: ' + comment)
							writeMsg(from_id, 'Заказ успешно отклонен!')
							Gorders[j+3] = 'declined'
						else:
							writeMsg(from_id, 'Заказа не существует - это могло произойти из-за перезапуска программы')

					elif args[0].startswith('ОТПРАВИТЬ'):
						order_no = None
						if len(args) == 2:
							try:	
								order_no = int(args[1])
							except:
								writeMsg(from_id, 'Неверный синтаксис команды, попробуйте ещё раз')
						else:
							writeMsg(from_id, 'Неверный синтаксис команды, попробуйте ещё раз')

						j = findOrder(order_no)
						if j >= 0:
							if Gorders[j+3] == 'working':
								writeToClient(Gorders[j+2], 'Курьер отправился к вам')
								writeMsg(from_id, 'Заказ отправлен!')
								Gorders[j+3] = 'delivered'
							else:
								writeMsg(from_id, 'Сначала необходимо принять заказ')
						else:
							writeMsg(from_id, 'Заказа не существует - это могло произайти из-за перезапуска программы')
					else:
						writeHelp(from_id)
						writeMsg(from_id, 'Неверный синтаксис команды, попробуйте ещё раз')
				else:
					writeMsg(from_id, 'Вы не авторизированы как администратор или диспетчер')

	def __init__(self, token, group_id, dispetcher_id, toClientVk):	
		global Gorders
		Gorders = []
		global Gdispetcher_id
		Gdispetcher_id = dispetcher_id
		global Gvk
		vk_session = vk_api.VkApi(token=token)
		Gvk = vk_session.get_api()
		global Glongpoll
		Glongpoll = VkBotLongPoll(vk_session, group_id)

		global GtoClientVk
		GtoClientVk = toClientVk

		thread = Thread(target=dispetchHelper.mainCycle, name='dipetchHelper')
		print("Бот диспетчер запущен")
		thread.start()
	
	def giveOrder(self, order_no, order, client_id):
		Gorders.append(order_no)
		Gorders.append(order)
		Gorders.append(client_id)
		Gorders.append('queue')
		
		writeMsg(Gdispetcher_id, 'НОВЫЙ ЗАКАЗ: Номер:'+ str(order_no) +' Отправьте команду для работы с заказом\n' +
		   'Заказ:\n' + order)

		thread1 = Thread(target=dispetchHelper.WaitForConfirmation, args = (order_no,))
		thread1.start()

		"""
			Gorders structure - 
				order_no = # of order from main module
				order = cart string
				order_status = status of order might be: 'queue', 'working', 'delivered', 'declined'
		"""

	def clearOrders(self):
		Gorders.clear()
