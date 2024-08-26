from flask import Flask, request, g, make_response, after_this_request
import os
import redis
from flask import Flask, request
from flask_socketio import SocketIO
from flask_login import LoginManager
from rq import Queue
from sqlalchemy import MetaData, create_engine
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from config import Config
from flask_caching import Cache
from flask import send_file
from flask_login import current_user
from logging.handlers import SMTPHandler
import time
import logging
from sqlalchemy.exc import OperationalError
import sqlalchemy
from flask import g
from flask_mail import Mail, Message

from sqlalchemy.engine.url import URL
from user_agents import parse
from app.utils import get_request_hash
import local_settings
import stripe

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

def _test_connection_string(flask_app):
	db_host = flask_app.config['DB_HOST']
	db_user = flask_app.config['DB_USER']
	db_pass = flask_app.config['DB_PASS']
	db_name = flask_app.config['DB_NAME']
	db_port = flask_app.config['DB_PORT']
	connection_string = flask_app.config['SQLALCHEMY_DATABASE_URI']
	try:
		engine = sqlalchemy.create_engine(str(connection_string))
		connection = engine.connect()
		if hasattr(connection, 'close'):
			connection.close()
	except Exception as e:
		logger.error(f"Database connection error: {str(e)}")
		logger.error(f"Connection string: {connection_string}")




def mobile_middleware(app):
    @app.before_request
    def detect_mobile():
        user_agent = request.headers.get('User-Agent', "")
        user_agent_parsed = parse(user_agent)
        g.is_mobile = user_agent_parsed.is_mobile




def log_journey_middleware(app):
	from worker.log_journey import log_journey_task

	@app.before_request
	def log_journey():

		if request.endpoint and ('static' in request.endpoint):
			return

		if request.url and ('serviceWorker' in request.url):
			return

		user_agent = request.headers.get('User-Agent', '').lower()
		crawlers = ['googlebot', 'bingbot', 'yandex', 'baiduspider', 'slurp', 'duckduckbot', 'facebookexternalhit', 'twitterbot']
		if any(crawler in user_agent for crawler in crawlers):
			return

		user_hash = request.cookies.get('user_hash')

		if not user_hash:
			user_hash = get_request_hash(request.remote_addr or '', request.headers.get('User-Agent', ''), user_hash)
			if user_hash:
				@after_this_request
				def add_cookie(response):
					response.set_cookie('user_hash', user_hash, max_age=60 * 60 * 24 * 365)  # 1 year expiration
					return response

			g.user_hash = user_hash
		else:
			g.user_hash = user_hash

		if 'twclid' in request.url:
			twclid = request.args.get('twclid')
			@after_this_request
			def add_cookie_twclid(response):
				response.set_cookie('_twclid', twclid, max_age=60 * 60 * 24 * 30)  # 1 month expiration
				return response

		user_id = current_user.id if current_user.is_authenticated else None
		data = {
			'user_id': user_id,
			'user_hash': g.user_hash,
			'endpoint': request.endpoint,
			'referrer': request.referrer or 'direct',
			'timestamp': time.time(),
			'location': request.url,
			'_type': 'before_request'
		}
		app.config['low_priority_queue'].enqueue(log_journey_task, data)


def create_app(config_class=Config):
	# Initialize the Flask application
	start_time = time.time()
	flask_app = Flask(__name__)
	mobile_middleware(flask_app)
	log_journey_middleware(flask_app)
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

	if flask_app.config['FLASK_ENV'] == 'prod':
		stripe.api_key = local_settings.PROD_STRIPE_SECRET_KEY
	else:
		stripe.api_key = local_settings.DEV_STRIPE_SECRET_KEY

	logger.info(f'Initialized plugins in {time.time() - start_time} seconds')

	redis_conn = redis.from_url(os.environ.get('REDIS_URL', flask_app.config['REDIS_URL']))
	flask_app.config['task_queue'] = Queue(connection=redis_conn)
	flask_app.config['high_priority_queue'] = Queue('high_priority', connection=redis_conn)
	flask_app.config['low_priority_queue'] = Queue('low_priority', connection=redis_conn)

	from app.routes import bp as room_bp
	flask_app.register_blueprint(room_bp)

	from app.models import User
	@login_manager.user_loader
	def load_user(user_id):
		return User.get_by_id(user_id)

	import app.socket_events, app.routes

	logger.info(f'Running on {flask_app.config["FLASK_ENV"]} environment')
	logger.info(f'Running redis at {flask_app.config["REDIS_URL"]}')
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

	@flask_app.route('/static/<path:filename>')
	def custom_static(filename):
		if "gzip" in request.headers.get('Accept-Encoding', ''):
			return send_file(os.path.join(flask_app.static_folder, filename+'.gz'),
							as_attachment=False,
							attachment_filename=filename,
							mimetype='application/json',
							headers={'Content-Encoding': 'gzip'})
		else:
			return flask_app.send_static_file(filename)

	if os.environ.get('FLASK_ENV', 'dev') == 'prod':
		if flask_app.config['MAIL_SERVER']:
			auth = None
			if flask_app.config['MAIL_USERNAME'] or flask_app.config['MAIL_PASSWORD']:
				auth = (flask_app.config['MAIL_USERNAME'], flask_app.config['MAIL_PASSWORD'])
			secure = None
			if flask_app.config['MAIL_USE_TLS']:
				secure = ()

			mail_handler = SMTPHandler(
				mailhost=(flask_app.config['MAIL_SERVER'], flask_app.config['MAIL_PORT']),
				fromaddr=flask_app.config['ADMINS'][0],
				toaddrs=flask_app.config['ADMINS'],
				subject='AI-LEADS ERRRRROOOOOORRRRRRRRR',
				credentials=auth,
				secure=secure
			)

			mail_handler.setLevel(logging.ERROR)
			logger.addHandler(mail_handler)


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


	return flask_app

import app.models
