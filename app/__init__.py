import os
import redis
from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager
from rq import Queue
from sqlalchemy import MetaData, create_engine
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from config import Config
from flask_caching import Cache
import time
# from google.auth.exceptions import DefaultCredentialsError
import logging
from sqlalchemy.exc import OperationalError
import sqlalchemy
from flask_mail import Mail, Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('BDB-2EB')

socketio = SocketIO(cors_allowed_origins="*",async_mode='gevent')
worker_socketio = SocketIO(cors_allowed_origins="*",async_mode='gevent')
login_manager = LoginManager()
cache = Cache()
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

if not os.path.exists('data'):
	os.makedirs('data')
if not os.path.exists('data/models'):
	os.makedirs('data/models')
if not os.path.exists('data/models/lead'):
	os.makedirs('data/models/lead')
if not os.path.exists('data/models/lead_source'):
	os.makedirs('data/models/lead_source')

convention = {
	"ix": 'ix_%(column_0_label)s',
	"uq": "uq_%(table_name)s_%(column_0_name)s",
	"ck": "ck_%(table_name)s_%(constraint_name)s",
	"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
	"pk": "pk_%(table_name)s"
}

from sqlalchemy.engine.url import URL

def _get_connection_string(flask_app):
    db_host = flask_app.config['DB_HOST']
    db_user = flask_app.config['DB_USER']
    db_pass = flask_app.config['DB_PASS']
    db_name = flask_app.config['DB_NAME']
    db_port = flask_app.config['DB_PORT']

    logger.info(f'DB_HOST: {db_host}')
    logger.info(f'DB_PORT: {db_port}')
    logger.info(f'DB_PASS: {db_pass}')
    logger.info(f'DB_USER: {db_user}')

    connection_string = URL.create(
        drivername="postgresql",
        username=db_user,
        password=db_pass,
        host=db_host,
        port=db_port,
        database=db_name
    )

    return str(connection_string)

def _test_connection_string(flask_app):
	db_host = flask_app.config['DB_HOST']
	db_user = flask_app.config['DB_USER']
	db_pass = flask_app.config['DB_PASS']
	db_name = flask_app.config['DB_NAME']
	db_port = flask_app.config['DB_PORT']
	connection_string = flask_app.config['SQLALCHEMY_DATABASE_URI']
	logger.info(f'SQLALCHEMY_DATABASE_URI: {flask_app.config["SQLALCHEMY_DATABASE_URI"]}')
	logger.info(f"Attempting to connect to database: {db_host}:{db_port} as {db_user}")
	try:
		engine = sqlalchemy.create_engine(str(connection_string))
		connection = engine.connect()
		logger.info("Successfully connected to the database")
		if hasattr(connection, 'close'):
			connection.close()
	except Exception as e:
		logger.error(f"Database connection error: {str(e)}")
		logger.error(f"Connection string: {connection_string}")


def create_app(config_class=Config):
	# Initialize the Flask application
	start_time = time.time()
	flask_app = Flask(__name__)
	flask_app.config.from_object(config_class)
	logger.info(f'Config loaded in {time.time() - start_time} seconds')
	logger.info(f'Running on {flask_app.config["FLASK_ENV"]} environment')
	logger.info(f'Running redis at {flask_app.config["REDIS_URL"]}')
	_test_connection_string(flask_app)

	db.init_app(flask_app)
	migrate.init_app(flask_app, db)
	socketio.init_app(flask_app, message_queue=flask_app.config['SOCKETIO_REDIS_URL'])
	login_manager.init_app(flask_app)
	cache.init_app(flask_app)
	mail.init_app(flask_app)

	logger.info(f'Initialized plugins in {time.time() - start_time} seconds')

	redis_conn = redis.from_url(os.environ.get('REDIS_URL', flask_app.config['REDIS_URL']))
	task_queue = Queue('default', connection=redis_conn)

	from app.routes import bp as room_bp
	flask_app.register_blueprint(room_bp)

	from app.models import User
	@login_manager.user_loader
	def load_user(user_id):
		return User.get_by_id(user_id)

	import app.socket_events, app.routes

	logger.info(f'Running on {flask_app.config["FLASK_ENV"]} environment')
	logger.info(f'Running redis at {flask_app.config["REDIS_URL"]}')
	logger.info(f'Running with SQL instance: {flask_app.config["SQLALCHEMY_DATABASE_URI"]}')

	logger.info(f'Making DB after {time.time() - start_time} seconds')


	with flask_app.app_context():
		try:
			db.create_all()
		except Exception as e:
			logger.error(f"Database connection error: {str(e)}")
			# Print out all configuration variables (except passwords)
			for key, value in flask_app.config.items():
				if 'PASS' not in key.upper():
					logger.info(f"{key}: {value}")


	logger.info(f'Returning app after {time.time() - start_time} seconds')


	return flask_app


def create_minimal_app(config_class=Config):
	flask_app = Flask(__name__)
	flask_app.config.from_object(config_class)

	db.init_app(flask_app)
	migrate.init_app(flask_app, db)
	mail.init_app(flask_app)

	redis_conn = redis.from_url(os.environ.get('REDIS_URL', flask_app.config['REDIS_URL']))

	flask_app.config['task_queue'] = Queue(connection=redis_conn)
	flask_app.config['high_priority_queue'] = Queue('high_priority', connection=redis_conn)
	flask_app.config['low_priority_queue'] = Queue('low_priority', connection=redis_conn)

	worker_socketio.init_app(flask_app, message_queue=flask_app.config['SOCKETIO_REDIS_URL'])

	_test_connection_string(flask_app)

	logger.info(f'Running on {flask_app.config["FLASK_ENV"]} environment')
	logger.info(f'Running redis at {flask_app.config["REDIS_URL"]}')
	logger.info(f'Running with SQL instance: {flask_app.config["SQLALCHEMY_DATABASE_URI"]}')


	return flask_app

import app.models
