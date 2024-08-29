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
	status_code = db.Column(db.Integer)
	user_agent = db.Column(db.String(256))
	last_active = db.Column(db.DateTime(timezone=True), index=True, default=lambda: datetime.now(pytz.utc))

	def to_dict(self):
		return {
			'id': self.id,
			'guid': self.guid,
			'type': self._type,
			'created_at': self.created_at.astimezone(pytz.utc).isoformat() if self.created_at else None,
			'user_id': self.user_id,
			'user_hash': self.user_hash,
			'status_code': self.status_code,
			'location': self.location,
			'endpoint': self.endpoint,
			'referrer': self.referrer,
			'user_agent': self.user_agent,
			'last_active': self.last_active.astimezone(pytz.utc).isoformat() if self.last_active else None
		}
