import telepot 
import json 
import random
import time
import re
import _thread as thread

random.seed()
f = open('conf.cfg','r')
CONF = json.loads(f.read())
BOT = telepot.Bot(CONF['TOKEN'])

df = open('words.txt','r')
df_scramble = open('scramble.txt','r')
dictionary = json.loads(df.read())
SCRAMBLE_WORDS = json.loads(df_scramble.read())

GAME_REPLIES = ('/scramble','/type','/taboo')
GAMES_RUNNING=CONF['GAMES']
GAMES_OFF = CONF['OFF'] 
TYPE_WORDS = dictionary['words']
TABOO_WORDS = dictionary['words']
TABOO_TABOOS = {}
POINTS = CONF['POINTS']
REPLIES = CONF['REPLIES']
CALLME = CONF['CALLME']

f.close() 

def check_command(msg):
	#print(msg)
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
			
		if msg['text'].split(' ')[0] == '/help':
			send_help(msg)

		if msg['text'].split(' ')[0] == '/add_scramble':
			add_scramble(msg)

		if msg['text'].split(' ')[0] == '/leaderboard':
			leaderboard(msg)
	
		if msg['text'] == '/customrep':
			send_reps(msg)

		if msg['text'].split(' ')[0] == '/report':
			try:
				BOT.sendMessage(CONF['ADMIN'],msg['text'].split(' ',1)[1])
				BOT.sendMessage(msg['chat']['id'],'Report has been sent.')	
			except IndexError:
				BOT.sendMessage(msg['chat']['id'],'Malformed command. Send /help for more information.')

		if msg['text'].split(' ')[0] == '/callme':
			CALLME[str(msg['from']['id'])] = msg['text'].split(' ',1)[1]
			BOT.sendMessage(msg['chat']['id'],msg['from']['first_name']+',I will now call you '+CALLME[str(msg['from']['id'])])	

		if msg['text'].split(' ')[0] == '/reverse':
			BOT.sendMessage(msg['chat']['id'],msg['text'].split(' ',1)[1][::-1])
		
						
		if msg['text'].split(' ')[0] == '/remrep':
			remove(msg)
			
		try:
			for com in REPLIES[str(msg['chat']['id'])]:
				com_regex = '^'+com.replace('%s','(.*)').replace('%','.*')+'$'
				result = re.search(com_regex, msg['text']) 
				if result is not None:	
					answer = REPLIES[str(msg['chat']['id'])][com]
				
					try:
						msg_replace = result.group(1)
					except IndexError:
						msg_replace = msg['text']
					nick = name(msg)
					try: 
						username = msg['from']['username']
					except KeyError:
						username = ''

					try:
						lastname = msg['from']['last_name']
					except KeyError:
						lastname = ''

					answer = answer.replace('%s', msg_replace)
					answer = answer.replace('%u', msg['from']['username'])	
					answer = answer.replace('%n', username)
					answer = answer.replace('%f', msg['from']['first_name'])	
					answer = answer.replace('%l', lastname)	
	
					BOT.sendMessage(msg['chat']['id'],answer)
					
		except KeyError:
			REPLIES[str(msg['chat']['id'])] = {}

					
		if msg['text'].split(' ')[0] == '/addrep':		
			add(msg)	
					
	except telepot.exception.TelegramError as e:
		print(e)
		if e[1] == 403:
			BOT.sendMessage(msg['chat']['id'],'You are not chatting with me. Please send me a message and try again')
	except KeyError as e: 
		print(e)



def leaderboard(msg):
	try: 
		game = msg['text'].split(' ',1)[1]

		if '/'+game not in GAME_REPLIES:
			BOT.sendMessage(msg['chat']['id'], 'Not a game. Send /help for more information')
			return 

		show_points(msg,False)	
		game_points = POINTS[str(msg['chat']['id'])]	
		leaderboard_str = 'Leaderboard for '+game+':\n'

		for user in game_points:
			username = ''
			try:
				username = CALLME[user]
			except KeyError:
				u = BOT.getChatMember(msg['chat']['id'],user)
				username = u['user']['first_name']
				
			leaderboard_str += username+': '+str(game_points[user][game])+'\n'

		BOT.sendMessage(msg['chat']['id'], leaderboard_str)
	except IndexError:
		BOT.sendMessage(msg['chat']['id'],'Malformed command. Send /help for more information')

def add_scramble(msg):
	try:
		new_word = msg['text'].split(' ',1)[1]
		if new_word not in SCRAMBLE_WORDS:		
			SCRAMBLE_WORDS.append(new_word)
			BOT.sendMessage(msg['chat']['id'],'New word '+new_word+' has been added to scramble dictionary')
		else: 
			BOT.sendMessage(msg['chat']['id'],'Word already in scramble dictionary')
	except IndexError:
		BOT.sendMessage(msg['chat']['id'],'Malformed command. Send /help for more information') 

#adds a command or reply
def add(msg):
	try:
		comm = msg['text'].split(' ',1)[1]
		comm = comm.split(':',1)
		if comm[1] == '':
			raise IndexError('no empty reply')

		try:	
			if comm[0] not in REPLIES[str(msg['chat']['id'])]:		
				REPLIES[str(msg['chat']['id'])][comm[0]] = comm[1]
			else:
				BOT.sendMessage(msg['chat']['id'],comm[0]+' - reply already exists. Try again with a different name')
		except KeyError:
			REPLIES[str(msg['chat']['id'])] = {}
			REPLIES[str(msg['chat']['id'])][comm[0]] = comm[1]
		BOT.sendMessage(msg['chat']['id'],'Added reply: '+comm[0])
	except IndexError:
		BOT.sendMessage(msg['chat']['id'],'Malformed command. Send /help for more information')	


#removes a command or reply
def remove(msg):
	comm = msg['text'].split(' ',1)
	try:	
		if comm[1] in REPLIES[str(msg['chat']['id'])]:
			del REPLIES[str(msg['chat']['id'])][comm[1]]
			BOT.sendMessage(msg['chat']['id'],'reply '+comm[1]+' has been deleted')
		else:
			BOT.sendMessage(msg['chat']['id'],'Not a reply.')
	except IndexError:
		BOT.sendMessage(msg['chat']['id'],'Malformed command. Send /help for more information')


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
	try: 
		command = msg['text'].split(' ')[1]
		if command == 'abortgame':
			message = 'aborts the running game, if one is running.'
		elif command == 'scramble':
			message = 'starts a game of scramble, if no game is currently running\n'
			mesage += 'the bot will send a word with letters in a random order, players have to send the correct original word to win'
		elif command == 'type':
			message = 'starts a game of type, if no game is currently running\n'
			message += 'the bot will send a word, the player that types and sends the word fastest wins the game'
		elif command == 'taboo':
			message = 'starts a game of taboo, if no game is currently running\n'
			message += 'the bot will send the player that started the game a word and the other players have to guess the word based on the clues that player gives. The player that guesses the word first wins. If the starting player mentiones the word themselves the game will be aborted and the player loses a point'
		elif command == 'running':
			message = 'forwards the message of the current running game, if one is running'
		elif command == 'togglegames':
			message = 'turns games for the current chat on or off'
		elif command == 'points':
			message == 'sends a message with the current points of the player that requested it'
		elif command =='help':
			message == 'Usage: /help or /help command\n'
			message += 'sends the general help message or a help message for a specific command'
		elif command == 'add_scramble':
			message = 'Usage: /add_scramble word\n'
			message += 'adds word to the scramble dictionary if it\'s not in it already'
		elif command == 'leaderboard':
			message = 'Usage: /leaderboard game\n'
			message += 'Sends the leaderboard of game in the current chat'
		elif command == 'customrep':
			message = 'sends a list of custom replies to the user'
		elif command == 'report':
			message = 'Usage: /report message\n'
			message += 'sends message to the specified adminstrator'
		elif command == 'callme':
			message = 'Usage: /callme name\n'
			message += 'Changes the name the bot calls the user to name'
		elif command == 'reverse':
			message = 'Usage /reverse message\n'
			message += 'Sends the message but reversed'
		elif command == 'remrep':
			message = 'Usage /remrep reply\n'
			mesage += 'Removes the specified reply'
		elif command == 'addrep':
			message = 'Usage /addrep trigger:reply\n'
			message += 'Adds a new reply with trigger\n'
			message += 'Trigger can contain the wildcard % which will match anything(so %test%:test will answer to any message containing the string "test" with test\n'
			message += 'Trigger can also contain the wildcard %s which will also match anything, but will save it for usage in the reply\n'
			message += 'Reply can contain %s, %u, %n, %f and %l\n'
			message += '%s will be replaced with the message that triggered the reply or whatever got matched in the trigger(so test%stest:%s will anwer to "testtesttest" with "test", but "test:%s" will answer "test" to message "test")\n'
			message += '%u will be replaced with the username of the user who\'s message triggered the reply\n'
			message += '%n will be replaced with the nickname of the user(set with /callme), if no nickname is present, the first name will be used\n'
			message += '%f will be replaced with the first name of the user'
			message += '%l will be replaced with the last name of the user'
	except IndexError:
		message = """/taboo - starts a game of taboo\n
/scramble - starts a game of scramble\n
/type - starts a game of type \n
/running - shows the running game\n
/abortgame - aborts the running game\n
/togglegames - toggles games on or off\n
/points - shows user\'s points in current chat\n
/leaderboard game - shows the leaderboard for game in the chat\n
/reverse message - reverses a message\n
/add_scramble word - adds word to scramble\n
/addrep command:return - adds a custom reply\n
/remrep command - removes a custom reply\n
/callme name - changes the name the bot calls you\n
/customrep - sends all custom replies\n
/report message - sends a message to admin"""
	
	BOT.sendMessage(msg['from']['id'],message)
	if msg['from']['id'] != msg['chat']['id']:
		BOT.sendMessage(msg['chat']['id'],'Help has been sent in PM')

#sends all replies
def send_reps(msg):
	message = 'custom replies:\n'
	
	try:
		for com in REPLIES[str(msg['chat']['id'])]:
			message+=com+'\n'
		if message=='custom replies:\n':
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
		POINTS[str(msg['chat']['id'])][str(msg['from']['id'])] = {'taboo':0, 'scramble':0, 'type':0}

		user_points = {'taboo':0, 'scramble':0, 'type':0}
	
	if send:
		points_str = 'taboo: '+str(user_points['taboo'])+'\nscramble: '+str(user_points['scramble'])+'\ntype: '+str(user_points['type'])	
		BOT.sendMessage(msg['chat']['id'],name(msg)+', your points:\n'+points_str)

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
	GAMES_RUNNING[str(msg['chat']['id'])]['game'] = game_name

#shows the game running in the chat
def show_game(msg):
	if str(msg['chat']['id']) in GAMES_RUNNING:
		BOT.forwardMessage(msg['chat']['id'],msg['chat']['id'],GAMES_RUNNING[str(msg['chat']['id'])]['message_id'])
	else: 
		BOT.sendMessage(msg['chat']['id'],'Currently no running game')

#checks running games
def handle_games(msg):
	try:
		game = GAMES_RUNNING[str(msg['chat']['id'])]['game']
		if msg['from']['id'] == GAMES_RUNNING[str(msg['chat']['id'])]['player'] and game == 'taboo' and (msg['text'] in GAMES_RUNNING[str(msg['chat']['id'])]['taboo'] or GAMES_RUNNING[str(msg['chat']['id'])]['solution'] in msg['text']):
			show_points(msg,False)
			POINTS[str(msg['chat']['id'])][str(msg['from']['id'])][game] -= 1
			if POINTS[str(msg['chat']['id'])][str(msg['from']['id'])][game] < 0:
				POINTS[str(msg['chat']['id'])][str(msg['from']['id'])][game] = 0
			BOT.sendMessage(msg['chat']['id'],'TABOO WORD MENTIONED! ABORTING GAME\n You just lost 1 point\nYour current points are '+str(POINTS[str(msg['chat']['id'])][str(msg['from']['id'])][game]))	
			del GAMES_RUNNING[str(msg['chat']['id'])]
		elif GAMES_RUNNING[str(msg['chat']['id'])]['solution'] == msg['text'].upper():	
			show_points(msg,False)
			POINTS[str(msg['chat']['id'])][str(msg['from']['id'])][game] += 1	
			BOT.sendMessage(msg['chat']['id'], 'You win, '+name(msg)+', the solution was '+msg['text']+'\nYour current points are '+str(POINTS[str(msg['chat']['id'])][str(msg['from']['id'])][game]))
			del GAMES_RUNNING[str(msg['chat']['id'])]
	except KeyError as err:
		print(err)

def save():
	f = open('conf.cfg','w')
	f.write(json.dumps(CONF))
	f.close()
	f = open('scramble.txt','w')
	f.write(json.dumps(SCRAMBLE_WORDS))
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
