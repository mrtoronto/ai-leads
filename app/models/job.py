import time
import pytz
from datetime import datetime
import uuid
from app import db

class JobTypes:
	LEAD_CHECK = 'lead_check'
	SOURCE_CHECK = 'source_check'
	QUERY_CHECK = 'query_check'
	TRAIN_MODELS = 'train_models'

class Job(db.Model):
	__tablename__ = 'job'
	id = db.Column(db.Integer, primary_key=True)
	guid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
	_type = db.Column(db.String(255))
	lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
	source_id = db.Column(db.Integer, db.ForeignKey('lead_source.id'))
	query_id = db.Column(db.Integer, db.ForeignKey('query.id'))
	model_id = db.Column(db.Integer, db.ForeignKey('user_model.id'))

	created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
