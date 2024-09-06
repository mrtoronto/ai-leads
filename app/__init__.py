from flask import Flask, request, g, after_this_request
import os
import redis
from flask_socketio import SocketIO
from flask_login import LoginManager
from rq import Queue
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_caching import Cache
from flask import send_file
from flask_login import current_user
from logging.handlers import SMTPHandler
import time
import logging
import sqlalchemy
from flask_mail import Mail

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




def should_skip_request():
    skip_conditions = [
        '/static/' in request.url,
        'favicon' in request.endpoint,
        'serviceWorker' in request.url,
        'og-image.png' in request.url,
        any(crawler in request.headers.get('User-Agent', '').lower() for crawler in 
            ['googlebot', 'bingbot', 'yandex', 'baiduspider', 'slurp', 'duckduckbot', 'facebookexternalhit', 'twitterbot'])
    ]
    return any(skip_conditions)

def log_journey_middleware(app):
	from worker.log_journey import log_journey_task

	@app.before_request
	def log_journey():
		if should_skip_request():
			return

		user_hash = request.cookies.get('user_hash')
		if not user_hash:
			user_hash = get_request_hash(request.remote_addr or '', request.headers.get('User-Agent', ''), user_hash)
			if user_hash:
				g.set_cookie = ('user_hash', user_hash, 60 * 60 * 24 * 365)  # 1 year expiration

		g.user_hash = user_hash

		if 'twclid' in request.args:
			g.set_twclid_cookie = (request.args.get('twclid'), 60 * 60 * 24 * 30)  # 1 month expiration

	@app.after_request
	def log_journey_after(response):
		if hasattr(g, 'set_cookie'):
			response.set_cookie(*g.set_cookie)
		
		if hasattr(g, 'set_twclid_cookie'):
			response.set_cookie('_twclid', *g.set_twclid_cookie)

		if response.status_code != 404 and not should_skip_request():
			user_id = current_user.id if current_user.is_authenticated else None
			data = {
				'user_id': user_id,
				'user_hash': g.get('user_hash'),
				'endpoint': request.endpoint,
				'referrer': request.referrer or 'direct',
				'user_agent': request.headers.get('User-Agent', '').lower(),
				'timestamp': time.time(),
				'location': request.url,
				'_type': 'after_request',
				'status_code': response.status_code
			}
			app.config['low_priority_queue'].enqueue(log_journey_task, data)

		return response




def create_app(config_class=Config):
    # Initialize the Flask application
    start_time = time.time()
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    # Initialize middleware
    mobile_middleware(flask_app)
    log_journey_middleware(flask_app)

    # Log initial information
    logger.info(f'Config loaded in {time.time() - start_time} seconds')
    logger.info(f'Running on {flask_app.config["FLASK_ENV"]} environment')
    logger.info(f'Running redis at {flask_app.config["REDIS_URL"]}')
    _test_connection_string(flask_app)

    # Initialize extensions
    initialize_extensions(flask_app)

    # Set up Stripe API key
    setup_stripe(flask_app)

    logger.info(f'Initialized plugins in {time.time() - start_time} seconds')

    # Set up Redis queues
    setup_redis_queues(flask_app)

    # Register blueprints
    from app.routes import bp as room_bp
    flask_app.register_blueprint(room_bp)

    # Set up user loader for Flask-Login
    setup_user_loader()

    # Import socket events and routes
    import app.socket_events, app.routes # noqa

    # Set up custom static file handling
    setup_static_file_handling(flask_app)

    # Set up error logging for production
    if os.environ.get('FLASK_ENV', 'dev') == 'prod':
        setup_error_logging(flask_app)

    logger.info(f'Returning app after {time.time() - start_time} seconds')

    return flask_app

def initialize_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, message_queue=app.config['SOCKETIO_REDIS_URL'])
    login_manager.init_app(app)
    cache.init_app(app)
    mail.init_app(app)

def setup_stripe(app):
    if app.config['FLASK_ENV'] == 'prod':
        stripe.api_key = local_settings.PROD_STRIPE_SECRET_KEY
    else:
        stripe.api_key = local_settings.DEV_STRIPE_SECRET_KEY

def setup_redis_queues(app):
    redis_conn = redis.from_url(os.environ.get('REDIS_URL', app.config['REDIS_URL']))
    app.config['task_queue'] = Queue(connection=redis_conn)
    app.config['high_priority_queue'] = Queue('high_priority', connection=redis_conn)
    app.config['low_priority_queue'] = Queue('low_priority', connection=redis_conn)

def setup_user_loader():
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)

def setup_static_file_handling(app):
    @app.route('/static/<path:filename>')
    def custom_static(filename):
        if "gzip" in request.headers.get('Accept-Encoding', ''):
            return send_file(os.path.join(app.static_folder, filename+'.gz'),
                            as_attachment=False,
                            attachment_filename=filename,
                            mimetype='application/json',
                            headers={'Content-Encoding': 'gzip'})
        else:
            return app.send_static_file(filename)

def setup_error_logging(app):
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()

        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr=app.config['ADMINS'][0],
            toaddrs=app.config['ADMINS'],
            subject='AI-LEADS ERRRRROOOOOORRRRRRRRR',
            credentials=auth,
            secure=secure
        )

        mail_handler.setLevel(logging.ERROR)
        logger.addHandler(mail_handler)

def create_minimal_app(config_class=Config):
	flask_app = Flask(__name__)
	flask_app.config.from_object(config_class)

	db.init_app(flask_app)
	migrate.init_app(flask_app, db)
	mail.init_app(flask_app)

	setup_redis_queues(flask_app)

	worker_socketio.init_app(flask_app, message_queue=flask_app.config['SOCKETIO_REDIS_URL'])

	_test_connection_string(flask_app)

	logger.info(f'Running on {flask_app.config["FLASK_ENV"]} environment')
	logger.info(f'Running redis at {flask_app.config["REDIS_URL"]}')

	if os.environ.get('FLASK_ENV', 'dev') == 'prod':
		setup_error_logging(flask_app)

	return flask_app

import app.models # noqa
