import telepot 
import json 
import random
import time
import _thread as thread

random.seed()
f = open('conf.cfg','r')
CONF = json.loads(f.read())
BOT = telepot.Bot(CONF['TOKEN'])

df = open('words.txt','r')
dictionary = json.loads(df.read())
GAME_REPLIES = ('/scramble','/type','/taboo')
GAMES_RUNNING=CONF['GAMES']
GAMES_OFF = CONF['OFF'] 
SCRAMBLE_WORDS = [item for item in dictionary['words'] if len(item)>3 and len(item)<7]
TYPE_WORDS = dictionary['words']
TABOO_WORDS = dictionary['words']
TABOO_TABOOS = {}
POINTS = CONF['POINTS']
REPLIES = CONF['REPLIES']
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
				if str(msg['chat']['id']) in GAMES_RUNNING:
					BOT.sendMessage(msg['chat']['id'], 'Aborted game, the solution was '+GAMES_RUNNING[str(msg['chat']['id'])]['solution'])
					abort_game(msg)
				else:
					BOT.sendMessage(msg['chat']['id'], 'Currently no running game')
			elif msg['text'] in GAME_REPLIES and str(msg['chat']['id']) in GAMES_RUNNING:
				BOT.sendMessage(msg['chat']['id'],'Already running a game',None,None,None,GAMES_RUNNING[str(msg['chat']['id'])]['message_id'])
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
			elif str(msg['chat']['id']) in GAMES_RUNNING: 
				handle_games(msg)
		else:
			if msg['text'] in GAME_REPLIES or msg['text'] == '/running' or msg['text'] == '/abortgame':
				BOT.sendMessage(msg['chat']['id'], 'Games turned off in this chat.\nSend /togglegames to turn on')
			elif msg['text'] == '/togglegames':
				BOT.sendMessage(msg['chat']['id'],'Games have been turned on in this chat')
				del GAMES_OFF[GAMES_OFF.index(msg['chat']['id'])]

		if msg['text'] == '/points':
			show_points(msg)
			
		if msg['text'] == '/help':
			send_help(msg)

		if msg['text'] == '/customcom':
			send_comm(msg)

		if msg['text'] == '/customrep':
			send_reps(msg)

		if msg['text'].split(' ')[0] == '/callme':
			CALLME[str(msg['from']['id'])] = msg['text'].split(' ',1)[1]
			BOT.sendMessage(msg['chat']['id'],msg['from']['first_name']+',I will now call you '+CALLME[str(msg['from']['id'])])	
		
		
		if msg['text'].split(' ')[0] == '/remcom':
			remove(msg,COMMANDS)		
				
		if msg['text'].split(' ')[0] == '/remrep':
			remove(msg,REPLIES)
			
		try:
			for com in REPLIES[str(msg['chat']['id'])]:
				if com in msg['text'].upper():
					BOT.sendMessage(msg['chat']['id'],REPLIES[str(msg['chat']['id'])][com])
		except KeyError:
			REPLIES[str(msg['chat']['id'])] = {}
	
		try:
			for com in COMMANDS[str(msg['chat']['id'])]:
				if com == msg['text'].upper():
					BOT.sendMessage(msg['chat']['id'],COMMANDS[str(msg['chat']['id'])][com])
		except KeyError:
			COMMANDS[str(msg['chat']['id'])] = {}	


		if msg['text'].split(' ')[0] == '/addrep':		
			add(msg,COMMANDS,'command')
					
		if msg['text'].split(' ')[0] == '/addcom':		
			add(msg,REPLIES,'reply')	
					
	except telepot.exception.TelegramError as e:
		print(e)
		BOT.sendMessage(msg['chat']['id'],'You are not chatting with me. Please send me a message and try again')
	except KeyError as e: 
		print(e)

#adds a command or reply
def add(msg,dic,name):
	try:
		comm = msg['text'].split(' ',1)[1]
		comm = comm.split(':',1)
		if comm[1] == '':
			raise IndexError('no empty'+name)

		try:	
			if comm[0].upper() not in dic[str(msg['chat']['id'])]:		
				REPLIES[str(msg['chat']['id'])][comm[0].upper()] = comm[1]
			else:
				BOT.sendMessage(msg['chat']['id'],comm[0]+' - '+name+' already exists. Try again with a different name')
		except KeyError:
			dic[str(msg['chat']['id'])] = {}
			dic[str(msg['chat']['id'])][comm[0].upper()] = comm[1]
		BOT.sendMessage(msg['chat']['id'],'Added '+name+': '+comm[0])
	except IndexError:
		BOT.sendMessage(msg['chat']['id'],'Malformed command. Send /help for more information')	


#removes a command or reply
def remove(msg, dic):
	comm = msg['text'].split(' ',1)
	try:	
		if comm[1].upper() in dic[str(msg['chat']['id'])]:
			del dic[str(msg['chat']['id'])][comm[1].upper()]
			BOT.sendMessage(msg['chat']['id'],'Reply '+comm[1]+' has been deleted')
		else:
			BOT.sendMessage(msg['chat']['id'],'Not a reply.')
	except IndexError:
		BOT.sendMessage(msg['chat']['id'],'Malformed command. Try /help for more information')


#returns callme name for user
def name(msg):	
	name = ''
	try:
		name = CALLME[str(msg['from']['id'])]
	except KeyError:
		return msg['from']['first_name']
	return name

#sends help to user
def send_help(msg):
	message = """/taboo - starts a game of taboo\n
/scramble - starts a game of scramble\n
/type - starts a game of type \n
/running - shows the running game\n
/abortgame - aborts the running game\n
/togglegame - toggles games on or off\n
/points - shows user\'s points in current chat\n
/addrep command:return - adds a custom command\n
/remrep command - removes a custom command\n
/callme name - changes the name the bot calls you\n
/customcom - sends all custom commands\n
/customrep - sends all custom replies"""
	
	BOT.sendMessage(msg['from']['id'],message)
	if msg['from']['id'] != msg['chat']['id']:
		BOT.sendMessage(msg['chat']['id'],'Help has been sent in PM')

#sends all custom commands
def send_comm(msg):
	message = 'custom commands:\n'
	
	try:
		for com in COMMANDS[str(msg['chat']['id'])]:
			message+=com+'\n'
		if len(COMMANDS[str(msg['chat']['id'])])==0:
			message+='no custom commands'
	except KeyError:
		message+='no custom commands'
	
	BOT.sendMessage(msg['from']['id'],message)
	if msg['from']['id'] != msg['chat']['id']:
		BOT.sendMessage(msg['chat']['id'],'Help has been sent in PM')


#sends all replies
def send_reps(msg):
	message = 'custom replies:\n'
	
	try:
		for com in REPLIES[str(msg['chat']['id'])]:
			message+=com+'\n'
		if len(REPLIES[str(msg['chat']['id'])])==0:
			message+='no custom replies'
	except KeyError:
		message+='no custom replies'
		
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
	if str(msg['chat']['id']) in GAMES_RUNNING:
		del GAMES_RUNNING[str(msg['chat']['id'])]

#starts a game of scramble or type
def game(msg,words,game_name):
	nr=random.randint(0,len(words)-1)	
	message=''
	taboo=[]

	if game_name=='scramble':
		word = ''.join(random.sample(words[nr],len(words[nr])))
		message = 'Unscramble: '+word
	elif game_name=='type':
		message = 'Type: '+words[nr]
	elif game_name=='taboo':
		if msg['chat']['type'] == 'private':
			BOT.sendMessage(msg['chat']['id'],'Taboo can only be played in groups, sorry pal.')
			return

		message = name(msg)+', the taboo has been sent in PM'
		BOT.sendMessage(msg['from']['id'],'The word to guess is: '+words[nr])
		taboo = []	
		#taboo = TABOO_TABOOS[words[nr]]
		taboo.append(words[nr])
	
	GAMES_RUNNING[str(msg['chat']['id'])] = BOT.sendMessage(msg['chat']['id'],message)
	GAMES_RUNNING[str(msg['chat']['id'])]['solution'] = words[nr].upper()
	GAMES_RUNNING[str(msg['chat']['id'])]['taboo'] = taboo
	GAMES_RUNNING[str(msg['chat']['id'])]['player'] = msg['from']['id']

#shows the game running in the chat
def show_game(msg):
	if str(msg['chat']['id']) in GAMES_RUNNING:
		BOT.forwardMessage(msg['chat']['id'],msg['chat']['id'],GAMES_RUNNING[str(msg['chat']['id'])]['message_id'])
	else: 
		BOT.sendMessage(msg['chat']['id'],'Currently no running game')

#checks running games
def handle_games(msg):
	try:
		if msg['from']['id'] == GAMES_RUNNING[str(msg['chat']['id'])]['player'] and msg['text'] in GAMES_RUNNING[str(msg['chat']['id'])]['taboo'] or GAMES_RUNNING[str(msg['chat']['id'])]['solution'] in msg['text']:
			show_points(msg,False)
			POINTS[str(msg['chat']['id'])][str(msg['from']['id'])] -= 1
			if POINTS[str(msg['chat']['id'])][str(msg['from']['id'])] < 0:
				POINTS[str(msg['chat']['id'])][str(msg['from']['id'])] = 0
			BOT.sendMessage(msg['chat']['id'],'TABOO WORD MENTIONED! ABORTING GAME\n You just lost 1 point\nYour current points are '+str(POINTS[str(msg['chat']['id'])][str(msg['from']['id'])]))	
			del GAMES_RUNNING[str(msg['chat']['id'])]
		elif GAMES_RUNNING[str(msg['chat']['id'])]['solution'] == msg['text'].upper():	
			show_points(msg,False)
			POINTS[str(msg['chat']['id'])][str(msg['from']['id'])] += 1
			BOT.sendMessage(msg['chat']['id'], 'You win, '+name(msg)+', the solution was '+msg['text']+'\nYour current points are '+str(POINTS[str(msg['chat']['id'])][str(msg['from']['id'])]))
			del GAMES_RUNNING[str(msg['chat']['id'])]
	except KeyError as err:
		print(err)




def save():
	f = open('conf.cfg','w')
	f.write(json.dumps(CONF))
	f.close()

def save_background():
	start = time.time()
	while True:
		if time.time()-start >= 600:
			save()
			start=time.time()
			print('saved config')

BOT.message_loop(check_command)
thread.start_new_thread(save_background,())
print('bot running')
input('')
save()

