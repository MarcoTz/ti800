import telepot 
import json 
import random

random.seed()
f = open('conf.cfg','r')
CONF = json.loads(f.read())
BOT = telepot.Bot(CONF['TOKEN'])

GAME_COMMANDS = ('/scramble','/type')
GAMES_RUNNING={}

SCRAMBLE_WORDS = ['test','anotherone']
TYPE_WORDS = ['test','anotherone']

def handle(msg):
	print(msg)
	check_command(msg)	

def check_command(msg):
	try:
		if msg['text'] in GAME_COMMANDS and msg['chat']['id'] in GAMES_RUNNING:
			BOT.sendMessage(msg['chat']['id'],'Already running a game',None,None,None,GAMES_RUNNING[msg['chat']['id']]['message_id'])
		elif msg['text'] == '/scramble':
			game_1(msg,SCRAMBLE_WORDS,True)
		elif msg['text'] == '/type':
			game_1(msg,TYPE_WORDS,False)
		elif msg['text'] == '/running':
			show_game(msg)
		else: 
			handle_games(msg)
		
	except KeyError: 
		print('keyerror')


#starts a game of scramble or type
def game_1(msg,words,scramble):
	nr=random.randint(0,len(words)-1)	
	message=''

	if scramble:
		word = ''.join(sorted(words[nr]))
		message = 'Unscramble: '+word
	else:
		message = 'Type: '+words[nr]
	
	GAMES_RUNNING[msg['chat']['id']] = BOT.sendMessage(msg['chat']['id'],message)
	GAMES_RUNNING[msg['chat']['id']]['solution'] = words[nr]

#shows the game running in the chat
def show_game(msg):
	if msg['chat']['id'] in GAMES_RUNNING:
		BOT.forwardMessage(msg['chat']['id'],msg['chat']['id'],GAMES_RUNNING[msg['chat']['id']]['message_id'])
	else: 
		BOT.sendMessage(msg['chat']['id'],'Currently no running game')

#checks running games
def handle_games(msg):
	try:
		if msg['chat']['id'] in GAMES_RUNNING and GAMES_RUNNING[msg['chat']['id']]['solution'] == msg['text']:
			BOT.sendMessage(msg['chat']['id'], 'correct')
			del GAMES_RUNNING[msg['chat']['id']]
	except KeyError:
		print('keyerror2')

BOT.message_loop(handle)
input('')
