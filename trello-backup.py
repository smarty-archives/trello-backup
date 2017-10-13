#!/usr/bin/env python -u

import ConfigParser
import os, sys
import json
import requests
import time
import io

configFile = 'trello-backup.config'
configFile = os.path.join(os.path.abspath(os.path.dirname(__file__)), configFile)

API_KEY = TOKEN = API_URL = ''

def main():
	if os.path.isfile(configFile):
		config = ConfigParser.RawConfigParser()
		config.read(configFile)
	else:
		sys.exit('Config file "{0}" does not exist.'.format(configFile))

	global API_KEY, TOKEN, API_URL
	API_KEY = config.get('Credentials', 'API_KEY')
	TOKEN = config.get('Credentials', 'TOKEN')

	API_URL = config.get('Paths', 'API_URL')
	OUTPUT_DIRECTORY = config.get('Paths', 'OUTPUT_DIRECTORY')

	TOKEN_EXPIRATION = config.get('Options', 'TOKEN_EXPIRATION')
	APP_NAME = config.get('Options', 'APP_NAME')
	ORGANIZATION_IDS = config.get('Options', 'ORGANIZATION_IDS')
	ORGANIZATION_NAMES = config.get('Options', 'ORGANIZATION_NAMES')
	PRETTY_PRINT = config.get('Options', 'PRETTY_PRINT') == 'yes'

	if not API_KEY:
		print('You need an API key to run this app.')
		print('Visit this url: https://trello.com/1/appKey/generate')
		API_KEY = raw_input('Then enter the API key here: ')
		print('\n[IMPORTANT] Make sure to add the key to the config file.\n')
		raw_input('Press enter to continue...\n')

	if not TOKEN:
		print('You need a token to run this app.')
		print("Visit this url: {0}connect?key={1}&name={2}&response_type=token&expiration={3}".format(API_URL, API_KEY, APP_NAME, TOKEN_EXPIRATION))
		TOKEN = raw_input('Then enter the token here: ')
		print('\n[IMPORTANT] Make sure to add the token to the config file.\n')
		raw_input('Press enter to continue...\n')

	if ORGANIZATION_NAMES and not ORGANIZATION_IDS:
		ORGANIZATION_IDS = get_organization_ids(ORGANIZATION_NAMES)

	# Parameters to get list of boards
	boardsPayload = {
		'key':API_KEY,
		'token':TOKEN,
		'filter':'open',
		'lists':'open',
	}
	# Parameters to get board contents
	boardPayload = {
		'key':API_KEY,
		'token':TOKEN,
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
	boards = requests.get(API_URL + "members/me/boards", params=boardsPayload)
	try:
		if len(boards.json) <= 0:
			print('No boards found.')
			return
	except ValueError:
		print('Unable to access your boards. Check your key and token.')
		return
	if not os.path.exists(OUTPUT_DIRECTORY):
		os.makedirs(OUTPUT_DIRECTORY)

	print('Backing up boards:')
	epoch_time = str(int(time.time()))

	for board in boards.json:
		if ORGANIZATION_IDS and (not board["idOrganization"] or not board["idOrganization"] in ORGANIZATION_IDS):
			continue

		print(u"    - {0} - {1} ({2})".format(board["idOrganization"], board["name"], board["id"]))
		boardContents = requests.get(API_URL + "boards/" + board["id"], params=boardPayload)
		filename = boardFilename(OUTPUT_DIRECTORY, board, epoch_time)
		with io.open(filename, 'w', encoding='utf8') as file:
			args = dict( sort_keys=True, indent=4) if PRETTY_PRINT else dict()
			data = json.dumps(boardContents.json, ensure_ascii=False, **args)
			file.write(unicode(data))

def boardFilename(output_dir, board, epoch_time):
	organization_id = sanitize(board["idOrganization"])
	boardName = sanitize(board["name"])

	formatted = u'{0}-{1}_'.format(organization_id, boardName)
	filename = formatted + epoch_time + '.json'
	return os.path.join(output_dir, filename)

def sanitize(name):
	return name.replace("/","-").replace(":","-")

def get_organization_ids(ORGANIZATION_NAMES):
	selected_organizations = []
	for organization in ORGANIZATION_NAMES.split(','):
		selected_organizations.append(organization.strip())
	organization_ids = []

	# Parameters to get a list of organizations
	organizationsPayload = {
		'key':API_KEY,
		'token':TOKEN,
	}

	organizations = requests.get(API_URL + "members/my/organizations", params=organizationsPayload)
	if len(organizations.json) <= 0:
		print('No organizations found.')
	else:
		for organization in organizations.json:
			if organization["name"] in selected_organizations:
				organization_ids.append(organization["id"])
	return organization_ids


if __name__ == '__main__':
	main()
