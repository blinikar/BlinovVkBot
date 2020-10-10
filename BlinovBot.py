#Copyright ©Blinov Yegor, 2020. All rights reserved!
#Licensed as Microsoft Reference Source License (Ms-RSL)(https://referencesource.microsoft.com/license.html)


import datetime
import dispetchHelper
import vk_api

import xml.etree.ElementTree as ET
from datetime import time
#from random import random
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from array import *

tree = ET.parse("config.xml")
root = tree.getroot()

users = []
orders_count = 1

client_orders_log_dir = 'client_orders_log.txt'
technikal_log_dir = 'technikal_log.log'

server_v = "CONSTRUCTION BUILD"
license_owner = "YEGOR BLINOV"
token = root.find("token").text
group_id = root.find("group_id").text
secretcode = root.find("secret_code").text # code for data clearing

vk_session = vk_api.VkApi(token=token)
longpoll = VkBotLongPoll(vk_session, group_id)
vk = vk_session.get_api()

dispetch_token = root.find("dispetcher_token").text #You need to replace abc123 to your COMMUNITY token
dispetcher_id = root.find("dispetcher_id").text # id of dispetcher VK PAGE (profile, no community)
dispetch_group_id = root.find("dispetcher_group_id").text #You need to replace 123 to dispetcher community ID 

dispetch = dispetchHelper.dispetchHelper(dispetch_token, dispetch_group_id, dispetcher_id, vk)

def log(text):
	f = open(technikal_log_dir, 'a')
	nowdt = datetime.datetime.today().strftime('%d.%m.%Y %H:%M:%S')
	f.write('\n===\nDateTime: ' + nowdt + ' - ' + text + '\n')

def checkForWorkTime():
	return True

class User:
	def __init__(self, id):
		self.id = id
		self.cart = [] # store all cart by [PRODUCT1, COUNT1, PRODUCT2, COUNT2, ...]
		self.deliveryAddress = "none"  
		self.product = None
		self.phone = ''
		self.stage = 'lobby' # can be lobby, cart, delivery, confirm, phone
	
	def getProduct(self):
		return self.product

	def addToCart(self, productId, count):
		self.cart.append(productId)
		self.cart.append(count)

	def getCart(self):
		return self.cart

	def setStage(self, stage):
		self.stage = stage

	def getStage(self):
		return self.stage

	def setProduct(self, product):
		self.product = product

	def getId(self):
		return self.id

	def clearCart(self):
		self.cart = []

	def setAddress(self, address):
		self.deliveryAddress = address

	def getAddress(self):
		return self.deliveryAddress
	
	def getId(self):
		return self.id

	def getPhone(self):
		return self.phone

	def setPhone(self, phone):
		self.phone = phone

def searchUser(connectedUser):
	founded = False
	for i in users:
		if(connectedUser.id == i.id):
			founded = i
			break

	return founded

def getKeyboardForMainMenu():
	keyboard = VkKeyboard(one_time=True)
	keyboard.add_button('Готово', color=VkKeyboardColor.POSITIVE)
	keyboard.add_button('Отмена', color=VkKeyboardColor.NEGATIVE)
	return keyboard

def getKeyboardWithAccept():
	keyboard = VkKeyboard(one_time=True)
	keyboard.add_button('Да', color=VkKeyboardColor.POSITIVE)
	keyboard.add_button('Отмена', color=VkKeyboardColor.NEGATIVE)
	return keyboard

def writeMsgWithKeyboard(toId, text, keyboard):
	vk.messages.send(
		user_id = toId,
		message = text,
		keyboard = keyboard.get_keyboard(),
		random_id = get_random_id()
	)

def writeMsg(toId, text):
	vk.messages.send(
		user_id = toId,
		message = text,
		random_id = get_random_id()
	)
	log('Отправлено сообщение: ' + str(toId) + ' текст: ' + text)

def getAllCartToStr(workingUser):
	cart = workingUser.getCart()
	fullPrice = 0
	allCount = 0
	result = ""
	for i in range(len(cart)):
		if (i % 2 == 0):
			product = cart[i]
			allCount = allCount + 1
			label = product['title']
			price = int(product['price']['amount'])/100
			count = cart[i+1]
			fullPrice = fullPrice + (price * count)
			
			result = result + str(str(allCount)  + ") " + label + " x" + str(count) + " цена: " + str(price) + " итог: " + str(float(price*count)) + "\n")
	if (allCount>0):
		result = result + "ИТОГО: " + str(fullPrice) + "\n"
	else: 
		result = "Твоя корзина пуста"
	return result

def loggingOrder(workingUser):
	f = open(client_orders_log_dir, 'a')
	nowdt = datetime.datetime.today().strftime("%d.%m.%Y %H:%M:%S")
	f.write("\n===DateTime: " + nowdt +"\nUser: " + str(workingUser.getId()) +"\nOrder no\n"+ str(orders_count) + "\nOrder:\n" + getAllCartToStr(workingUser) + "\nPhone: "+ workingUser.getPhone() + "\nAdress: " + workingUser.getAddress() + "\n===\n")
	log('Обработан заказ от: ' + str(workingUser.getId()))
	return

def sendOrderToRestaraunt(workingUser):
	loggingOrder(workingUser)
	dispetch.giveOrder(orders_count, getAllCartToStr(workingUser) + "\nАдрес: " + str(workingUser.getAddress()) + "\nТелефон: " + str(workingUser.getPhone()) +"\nСсылка: vk.com/id" + str(workingUser.getId()), workingUser.getId())
	return

def mainMenu(from_id):
	writeMsgWithKeyboard(from_id, "Добро пожаловать в Блинов Бот - бот для заказа еды.\nПравила сервиса - rulesURL\nЧтобы сформировать заказ отправь мне товар из моего списка: marketURL\nИНФО для информации, ТП для технической поддержки\nЕсли ты хочешь вернуться в главное меню отправь \"ЛОББИ\"", getKeyboardForMainMenu())

def lobby(workingUser, from_id, text, product):
	if (product!=None):
		writeMsg(from_id, "Сколько этого товара ты хочешь заказать, отправь число (не словами)? Например: 1")
		workingUser.setProduct(product)
		workingUser.setStage('cart')
	elif (text.upper() == 'ИНФО'):
		writeMsg(from_id, "full_info_text")
		mainMenu(from_id)
	elif (text.upper == 'ТП'):
		writeMsg(from_id, "Для технической поддержки напиши сюда: supportURL")
		mainMenu(from_id)
	elif (text.upper() == 'ОТМЕНА'):
		workingUser.clearCart()
		writeMsg(from_id, "Мы отчистили корзину, теперь ты можешь снова формировать заказ")
		mainMenu(from_id)
	elif (text.upper() == 'ГОТОВО'):
		if(workingUser.getCart() != []):
			writeMsg(from_id, "Отлично!\n Скажи свой номер телефона без 8 и +7 для того, чтобы я точно знал как с тобой свзаться в случае проблем. Например: \"9123456789\"")
			workingUser.setStage('phone')
		else:
			writeMsg(from_id, "Мы не можем оформить твой заказ, так как твоя корзина пуста")
			mainMenu(from_id)
	else:
		mainMenu(from_id)

def cart(workingUser, from_id, text):
	try:
		if (int(text)>0 and int(text)<100):
			workingUser.addToCart(workingUser.getProduct(), int(text))
			workingUser.setStage('lobby')
			writeMsgWithKeyboard(from_id, "Отлично. Твоя корзина: \n\n" + getAllCartToStr(workingUser) + "\nМожешь отправить мне ещё товар и продолжить формировать заказ или отправить мне слово \"ГОТОВО\" для продолжения оформления заказа, если хочешь очистить корзину то отправь \"ОТМЕНА\"", getKeyboardForMainMenu())
		else:
			writeMsg(from_id, "Число должно быть больше 0 и меньше ста :), попробуй ещё раз")
	except:
		writeMsg(from_id, "Кажется, ты отправил не число :(, попробуй ещё раз")

def phone(workingUser, from_id, text):
	try:
		if(int(text)>=9000000000 and int(text)<=9999999999):
			workingUser.setPhone(text)
			workingUser.setStage('delivery')
			writeMsg(from_id, "Супер!\nОтправь мне свой адрес, чтобы я знал куда доставить товар, например \"Сладкий проспект, 12, 2\", если вы хотите забрать заказ сами напишите \"самовывоз\"")
		else:
			writeMsg(from_id, "Не похоже на телефон... Попробуй ещё")
	except:
		writeMsg(from_id, "Кажется, ты отправил не число :(, попробуй ещё раз")

def delivery(workingUser, from_id, text):
	workingUser.setAddress(text)
	workingUser.setStage('confirm')
	writeMsgWithKeyboard(from_id, "Проверь все и подтверди свой заказ, чтобы это сделать отправь мне \"ДА\", для отмены - любой текст. Твой заказ: \n\n" + getAllCartToStr(workingUser) +"\nАдрес доставки: " + workingUser.getAddress() + "\nТелефон для связи: " + workingUser.getPhone() + "\n\nПосле подтверждения ресторан примет или отклонит твой заказ", getKeyboardWithAccept())

def confirm(workingUser, from_id, text):
	if(text.upper() == "ДА"):
		if (checkForWorkTime()):
			sendOrderToRestaraunt(workingUser)
			workingUser.setStage('lobby')
			workingUser.clearCart()
			writeMsg(from_id, "Отлично, мы отправили информацию о твоем заказе в ресторан, скоро тебе придет подтверждение.")
		else:
			writeMsg(from_id, "Сейчас мы не работаем, поэтому твой заказ не принят, чтобы мы приняли заказ отправь нам \"ДА\" в рабочее время, для отмены отправь \"ГОТОВО\"")
	else:
		workingUser.setStage('lobby')
		workingUser.clearCart()
		writeMsg(from_id, "Твой заказ отменен :(")
		mainMenu(from_id)

def main():
	startdt = datetime.datetime.today().strftime("%d.%m.%Y %H:%M:%S")
	startd = datetime.datetime.today().strftime("%d.%m.%Y")
	print('Сервер запущен в ' + startdt)
	
	log('Сервер запущен, переход в основной цикл')

	for event in longpoll.listen():
		if event.type == VkBotEventType.MESSAGE_NEW:
			nowd = datetime.datetime.today().strftime("%d.%m.%Y")
			if(nowd != startd):
				users.clear()
				print('Users очищен автоматически')
				log('Users очищен автоматически')
			
			print('Новое сообщение:')

			#receiving data
			from_id = event.obj.message['from_id']
			print('Для меня от: ', end='')
			print(from_id)

			connectedUser = User(from_id)
			workingUser = None
			#user checking
			if(searchUser(connectedUser) == False):
				workingUser = connectedUser
				users.append(workingUser)
			else:
				workingUser = searchUser(connectedUser)

			product = None
			if (event.obj.message['attachments']):
				print('Вложение: ', end='')
				try:
					if(event.obj.message['attachments'][0]['market'] and event.obj.message['attachments'][0]['market']['owner_id'] == 0-group_id): #test for group attachments
						product = event.obj.message['attachments'][0]['market']
						productId = event.obj.message['attachments'][0]['market']['id']
						print(productId)
					else:
						writeMsg(from_id, 'Вложение которое ты отправил явно содержит ошибку, проверь что во вложении товар из нашей группы. В случае проблем обратись к подробной инструкции или в техническую поддержку')
				except:
					writeMsg(from_id, 'Вложение которое ты отправил явно содержит ошибку, проверь что во вложении товар из нашей группы. В случае проблем обратись к подробной инструкции или в техническую поддержку')
			
			text = event.object.message['text']
			print('Текст:', text)

			log('Принято сообщение от ' + str(from_id) + ' текст: ' + str(text))

			if(text.upper() == 'ОТМЕНА'):
				workingUser.setStage('lobby')
				workingUser.clearCart()
				text = 'this is your time'
			elif(text.upper() == secretcode):
				users.clear()
				dispetchHelper.dispetchHelper.clearOrders()
				writeMsg(from_id, 'Сброс до заводских настроек... ОК!')
				print("Очистка данных по коду... ОК")
				print("===")
				log('Вызван код очистки данных')
				continue

			#working with data
			if (workingUser.getStage() == 'lobby'):
				lobby(workingUser, from_id, text, product)

			elif (workingUser.getStage() == 'cart'):
				cart(workingUser, from_id, text)

			elif (workingUser.getStage() == 'phone'):
				phone(workingUser, from_id, text)

			elif (workingUser.getStage() == 'delivery'):
				delivery(workingUser, from_id, text)

			elif (workingUser.getStage() == 'confirm'):
				confirm(workingUser, from_id, text)

			log('Обработано сообщение от ' + str(from_id) + ' текст: ' + str(text))
			print('===')

if __name__ == '__main__':
	main()