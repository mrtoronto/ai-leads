import os
from dotenv import load_dotenv
import requests
import socket
import logging
import certifi

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
	DB_INSTANCE_HOST = os.environ.get('DB_INSTANCE_HOST', 'localhost')
	DB_PORT = os.environ.get('DB_PORT', 5432)

	SQLALCHEMY_TRACK_MODIFICATIONS = False
