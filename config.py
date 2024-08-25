import os
from dotenv import load_dotenv
import requests
import socket
import logging
import certifi

import local_settings

logger = logging.getLogger('BDB-2EB')
basedir = os.path.abspath(os.path.dirname(__file__))

if os.path.exists(os.path.join(basedir, '.env')) and os.environ.get('FLASK_ENV') != 'prod':
	load_dotenv(os.path.join(basedir, '.env'))

class Config(object):

	FLASK_ENV = os.environ.get('FLASK_ENV') or 'dev'
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

	REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379') + '/0'
	SOCKETIO_REDIS_URL = os.environ.get('SOCKETIO_REDIS_URL', os.environ.get('REDIS_URL', 'redis://localhost:6379')) + '/1'
	CACHE_TYPE = 'redis'
	CACHE_REDIS_URL = REDIS_URL
	CACHE_DEFAULT_TIMEOUT = 300
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
	PROJECT_ID = os.environ.get('PROJECT_ID')

	DB_USER = os.environ.get('DB_USER')
	DB_PASS = os.environ.get('DB_PASS')
	DB_NAME = os.environ.get('DB_NAME')
	DB_HOST = os.environ.get('DB_HOST', 'localhost')
	DB_PORT = os.environ.get('DB_PORT', 5432)

	SQLALCHEMY_TRACK_MODIFICATIONS = False

	SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


	MAIL_SERVER = 'smtp.sendgrid.net'
	MAIL_PORT = 587
	MAIL_USE_TLS = True
	MAIL_USE_SSL = False
	MAIL_USERNAME = 'apikey'  # This is the literal string 'apikey', not your API key
	MAIL_PASSWORD = local_settings.SENDGRID_API_KEY
	MAIL_DEFAULT_SENDER = ('Matt — aiLeads', 'matt@ai-leads.xyz')

	ADMINS = [
		'matt@ai-leads.xyz'
	]

	SECURITY_PASSWORD_SALT = local_settings.SECURITY_PASSWORD_SALT

	PRICING_MULTIPLIERS = {
		'query': 400,
		'check_source': 4,
		'check_lead': 4,
		'check_source_mini': 10,
		'check_lead_mini': 10,
	}
