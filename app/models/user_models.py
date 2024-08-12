import pytz
from datetime import datetime
import uuid
from app import db

class ModelTypes:
	LEAD = 'lead'
	LEAD_SOURCE = 'lead_source'

class UserModels(db.Model):
	__tablename__ = 'user_model'
	id = db.Column(db.Integer, primary_key=True)
	guid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	model_type = db.Column(db.String(64), nullable=False)
	positive_examples = db.Column(db.Text, nullable=True)
	negative_examples = db.Column(db.Text, nullable=True)
	created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc), nullable=False)

	def __init__(self, id=None, **kwargs):
		self.id = id
		self.user_id = kwargs.get('user_id')
		self.model_type = kwargs.get('model_type')
		self.positive_examples = kwargs.get('positive_examples')
		self.negative_examples = kwargs.get('negative_examples')
		self.created_at = kwargs.get('created_at', datetime.now(pytz.utc))

	def to_dict(self):
		return {
			'id': self.id,
			'user_id': self.user_id,
			'model_type': self.model_type,
			'positive_examples': self.positive_examples,
			'negative_examples': self.negative_examples,
			'created_at': self.created_at.isoformat()
		}

	@classmethod
	def get_by_id(cls, model_id):
		return cls.query.get(model_id)

	def save(self):
		db.session.add(self)
		db.session.commit()
