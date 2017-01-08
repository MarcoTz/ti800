import telepot 
import json 
import random

random.seed()
f = open('conf.cfg','r')
CONF = json.loads(f.read())
BOT = telepot.Bot(CONF['TOKEN'])

df = open('words.txt','r')
dictionary = json.loads(df.read())
GAME_COMMANDS = ('/scramble','/type','/taboo')
GAMES_RUNNING={}
GAMES_OFF = CONF['OFF'] 
SCRAMBLE_WORDS = [item for item in dictionary['words'] if len(item)>4]
TYPE_WORDS = dictionary['words']
TABOO_WORDS = dictionary['words']
TABOO_TABOOS = {}
POINTS = CONF['POINTS']
COMMANDS = CONF['COMMANDS']
CALLME = CONF['CALLME']

f.close() 
 
def check_command(msg):
	try:
		split = msg['text'].split('@')
		try:	
			if split[1]=='ti800bot':
				msg['text'] = split[0]
		except IndexError:
			pass

		if msg['chat']['id'] not in GAMES_OFF: 
			
			if msg['text'] == '/abortgame':
				if msg['chat']['id'] in GAMES_RUNNING:
					BOT.sendMessage(msg['chat']['id'], 'Aborted game, the solution was '+GAMES_RUNNING[msg['chat']['id']]['solution'])
					abort_game(msg)
				else:
					BOT.sendMessage(msg['chat']['id'], 'Currently no running game')
			elif msg['text'] in GAME_COMMANDS and msg['chat']['id'] in GAMES_RUNNING:
				BOT.sendMessage(msg['chat']['id'],'Already running a game',None,None,None,GAMES_RUNNING[msg['chat']['id']]['message_id'])
			elif msg['text'] == '/scramble':
				game(msg,SCRAMBLE_WORDS,'scramble')
			elif msg['text'] == '/type':
				game(msg,TYPE_WORDS,'type')
			elif msg['text'] == '/taboo':
				game(msg,TABOO_WORDS,'taboo')
			elif msg['text'] == '/running':
				show_game(msg)
			elif msg['text'] == '/togglegames':
				BOT.sendMessage(msg['chat']['id'], 'Games have been turned off in this chat')
				GAMES_OFF.append(msg['chat']['id'])
				abort_game(msg)
			elif msg['chat']['id'] in GAMES_RUNNING: 
				handle_games(msg)
		else:
			if msg['text'] in GAME_COMMANDS or msg['text'] == '/running' or msg['text'] == '/abortgame':
				BOT.sendMessage(msg['chat']['id'], 'Games turned off in this chat.\nSend /togglegames to turn on')
			elif msg['text'] == '/togglegames':
				BOT.sendMessage(msg['chat']['id'],'Games have been turned on in this chat')
				del GAMES_OFF[GAMES_OFF.index(msg['chat']['id'])]

		if msg['text'] == '/points':
			show_points(msg)
			
		if msg['text'] == '/help':
			send_help(msg)

		if msg['text'].split(' ')[0] == '/callme':
			CALLME[str(msg['from']['id'])] = msg['text'].split(' ',1)[1]
			BOT.sendMessage(msg['chat']['id'],msg['from']['first_name']+'I will now call you'+CALLME[msg['from']['id']])
	
		if msg['text'].split(' ')[0] == '/addcomm':	
			try:
				comm = msg['text'].split(' ',1)[1]
				comm = comm.split(':')
				print(comm[1])
				try:
					COMMANDS[str(msg['chat']['id'])][comm[0]] = comm[1]
				except KeyError:
					COMMANDS[str(msg['chat']['id'])] = {}
					COMMANDS[str(msg['chat']['id'])][comm[0]] = comm[1]
				BOT.sendMessage(msg['chat']['id'],'Added command '+comm[0]+':'+comm[1])
			except IndexError:
				BOT.sendMessage(msg['chat']['id'],'Malformed command. Send /help for more information')

		if msg['text'].split(' ')[0] == '/remcomm':
			comm = msg['text'].split(' ')
			if comm[1] in COMMANDS[str(msg['chat']['id'])]:
				del COMMANDS[str(msg['chat']['id'])][comm[1]]
				BOT.sendMessage(msg['chat']['id'],'Command '+comm[1]+' has been deleted')
			else:
				BOT.sendMessage(msg['chat']['id'],'Not a command.')
		
		for com in COMMANDS[str(msg['chat']['id'])]:
			if com in msg['text']:
				BOT.sendMessage(msg['chat']['id'],COMMANDS[str(msg['chat']['id'])][com])
	
	except telepot.exception.TelegramError:
		BOT.sendMessage(msg['chat']['id'],'You are not chatting with me. Please send me a message and try again')
	except KeyError: 
		print('keyerror')

#returns callme name for user
def name(msg):	
	try:
		name = CALLME[str(msg['from']['id'])]
	except IndexError:
		name = msg['from']['first_name']
	
	return name

#sends help to user
def send_help(msg):
	message = """/taboo - starts a game of taboo\n
				/scramble - starts a game of scramble\n
				/type - starts a game of type \n
				/running - shows the running game\n
				/abortgame - aborts the running game\n
				/togglegame - toggles games on or off\n
				/points - shows user's points in current chat\n
				/addcomm command:return - adds a custom command\n
				/remcomm command - removes a custom command\n"""
	try:
		message += '-------\ncustom commands:'+json.dumps(COMMANDS[str(msg['chat']['id'])])
	except KeyError:
		pass

	BOT.sendMessage(msg['from']['id'],message)
	if msg['from']['id'] != msg['chat']['id']:
		BOT.sendMessage(msg['chat']['id'],'Help has been sent in PM')

#shows points of user
def show_points(msg,send=True):
	try: 
		chat_points = POINTS[str(msg['chat']['id'])]
	except KeyError:
		POINTS[str(msg['chat']['id'])] = {}
		chat_points = POINTS[str(msg['chat']['id'])]

	try:
		user_points = chat_points[str(msg['from']['id'])]
	except KeyError:
		POINTS[str(msg['chat']['id'])][str(msg['from']['id'])] = 0
		user_points = 0
	
	if send:
			BOT.sendMessage(msg['chat']['id'],name(msg)+', you have '+str(user_points)+' points')

#aborts running game
def abort_game(msg):
	if msg['chat']['id'] in GAMES_RUNNING:
		del GAMES_RUNNING[msg['chat']['id']]

#starts a game of scramble or type
def game(msg,words,name):
	nr=random.randint(0,len(words)-1)	
	message=''
	taboo=[]

	if name=='scramble':
		word = ''.join(sorted(words[nr]))
		message = 'Unscramble: '+word
	elif name=='type':
		message = 'Type: '+words[nr]
	elif name=='taboo':
		if msg['chat']['type'] == 'private':
			BOT.sendMessage(msg['chat']['id'],'Taboo can only be played in groups, sorry pal.')
			return

		message = 'The taboo has been sent in PM'
		BOT.sendMessage(msg['from']['id'],'The word to guess is: '+words[nr])
		taboo = []	
		#taboo = TABOO_TABOOS[words[nr]]
		taboo.append(words[nr])
	
	GAMES_RUNNING[msg['chat']['id']] = BOT.sendMessage(msg['chat']['id'],message)
	GAMES_RUNNING[msg['chat']['id']]['solution'] = words[nr].upper()
	GAMES_RUNNING[msg['chat']['id']]['taboo'] = taboo
	GAMES_RUNNING[msg['chat']['id']]['player'] = msg['from']['id']

#shows the game running in the chat
def show_game(msg):
	if msg['chat']['id'] in GAMES_RUNNING:
		BOT.forwardMessage(msg['chat']['id'],msg['chat']['id'],GAMES_RUNNING[msg['chat']['id']]['message_id'])
	else: 
		BOT.sendMessage(msg['chat']['id'],'Currently no running game')

#checks running games
def handle_games(msg):
	try:
		if msg['from']['id'] == GAMES_RUNNING[msg['chat']['id']]['player'] and msg['text'] in GAMES_RUNNING[msg['chat']['id']]['taboo']:
			show_points(msg,False)
			POINTS[str(msg['chat']['id'])][str(msg['from']['id'])] -= 1
			if POINTS[str(msg['chat']['id'])][str(msg['from']['id'])] < 0:
				POINTS[str(msg['chat']['id'])][str(msg['from']['id'])] = 0
			BOT.sendMessage(msg['chat']['id'],'TABOO WORD MENTIONED! ABORTING GAME\n You just lost 1 point\nYour current points are '+str(POINTS[str(msg['chat']['id'])][str(msg['from']['id'])]))	
			del GAMES_RUNNING[msg['chat']['id']]
		elif GAMES_RUNNING[msg['chat']['id']]['solution'] == msg['text'].upper():
			show_points(msg,False)
			POINTS[str(msg['chat']['id'])][str(msg['from']['id'])] += 1
			BOT.sendMessage(msg['chat']['id'], 'You win, '+name(msg)+', the solution was '+msg['text']+'\nYour current points are '+str(POINTS[str(msg['chat']['id'])][str(msg['from']['id'])]))
			del GAMES_RUNNING[msg['chat']['id']]
	except KeyError as err:
		print(err)

BOT.message_loop(check_command)
input('')
f = open('conf.cfg','w')
f.write(json.dumps(CONF))
f.close()
