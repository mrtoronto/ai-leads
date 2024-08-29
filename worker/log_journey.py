import pytz
from datetime import datetime
from app import worker_socketio, create_minimal_app, db
from app.models import Journey
from rq import get_current_job
from flask_socketio import emit
from worker import _make_min_app

import logging

logger = logging.getLogger('BDB-2EB')

def log_journey_task(data):
	job = get_current_job()
	min_app = _make_min_app()

	if not min_app:
		logger.error("Failed to create app context")
		return

	journey_type = data.get('_type', '')
	user_id = data.get('user_id', None)
	user_hash = data.get('user_hash', '')
	user_agent = data.get('user_agent', '')
	referrer = data.get('referrer', '')
	endpoint = data.get('endpoint', '')
	location = data.get('location', '')
	timestamp = data.get('timestamp')
	status_code = data.get('status_code', None)

	logger.info(data)

	### Convert timestamp from unix to UTC datetime
	timestamp = datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.utc)


	with min_app.app_context():
		journey = Journey(
			user_id=user_id,
			user_hash=user_hash,
			_type=journey_type,
			user_agent=user_agent,
			referrer=referrer,
			endpoint=endpoint,
			status_code=status_code,
			location=location,
			created_at=timestamp
		)
		db.session.add(journey)
		db.session.commit()
