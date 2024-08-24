import time
import pytz
from datetime import datetime
import uuid
from app import db

class Journey(db.Model):
	__tablename__ = 'journey'
	id = db.Column(db.Integer, primary_key=True)
	guid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
	_type = db.Column(db.String(255))
	created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	user_hash = db.Column(db.String(255))
	location = db.Column(db.String(255))
	endpoint = db.Column(db.String(255))
	referrer = db.Column(db.String(255))
	user_agent = db.Column(db.String(256))
	last_active = db.Column(db.DateTime(timezone=True), index=True, default=lambda: datetime.now(pytz.utc))
