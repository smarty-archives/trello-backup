#!/usr/bin/python -u

import ConfigParser
import os, sys
import json
import requests

configFile = 'trello.config'
configFile = os.path.join(os.path.abspath(os.path.dirname(__file__)), configFile)

def main():
	if os.path.isfile(configFile):
		config = ConfigParser.RawConfigParser()
		config.read(configFile)
	else:
		sys.exit('Config file "{0}" does not exist.'.format(configFile))

	API_KEY = config.get('Credentials', 'API_KEY')
	API_SECRET = config.get('Credentials', 'API_KEY')
	TOKEN = config.get('Credentials', 'TOKEN')
	API_URL = config.get('Paths', 'API_URL')
	outputDirectory = config.get('Paths', 'OUTPUT_DIRECTORY')

	if not API_KEY:
		print('Get an API key and come back:')
		print("https://trello.com/1/appKey/generate")
		API_KEY = raw_input('Enter API key: ')
		print("Make sure to add the key to the config file.")

	if not TOKEN:
		print('Get a token and come back:')
		# expiration: "1hour", "1day", "30days", "never"
		print("{0}connect?key={1}&name=SS-Trello-Backup&response_type=token&expiration=never".format(API_URL, API_KEY))
		TOKEN = raw_input('Enter token: ')
		print("Make sure to add the token to the config file.")

	# whoami = requests.get(API_URL + "members/me", data={'key':API_KEY, 'token':TOKEN})
	# meData = whoami.json()
	# print('user name: {0}'.format(meData['username']))

	# Get list of boards
	boardsPayload = {
		'key':API_KEY,
		'token':TOKEN,
		'filter':'open',
		'lists':'open',
	}
	# Get board contents
	boardPayload = {
		'key':API_KEY,
		'token':TOKEN,
		'lists':'open',	
		'fields':'all',
		'actions':'all',
		'action_fields':'all',
		'actions_limit':'1000',
		'cards':'all',
		'card_fields':'all',
		'card_attachments':'true',
		'lists':'all',
		'list_fields':'all',
		'members':'all',
		'member_fields':'all',
		'checklists':'all',
		'checklist_fields':'all',
		'organization':'false',
	}
	boards = requests.get(API_URL + "members/my/boards", data=boardsPayload)
	if len(boards.json()) <= 0:
		print("No boards found.")
		return
	if not os.path.exists(outputDirectory):
		os.makedirs(outputDirectory)

	print("Backing up boards:")
	for board in boards.json():
		if board["idOrganization"] == '4f8c6c070431ad515b5cd858': # smartystreets boards only
			print("    - {0} ({1})".format(board["name"], board["id"]))
			boardContents = requests.get(API_URL + "boards/" + board["id"], data=boardPayload)
			with open(outputDirectory + '/{0}.json'.format(board["name"]), 'w') as file:
				json.dump(boardContents.json(), file)

if __name__ == '__main__':
	main()
