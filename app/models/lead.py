import time
from app.utils import get_base_url, get_standard_url, _useful_url_check
import pytz
from datetime import datetime

import uuid
import requests
import json
from app import db
from app.models.user_models import ModelTypes

class Lead(db.Model):
	__tablename__ = 'lead'
	id = db.Column(db.Integer, primary_key=True)
	guid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
	name = db.Column(db.String(255))
	base_url = db.Column(db.String(255))
	url = db.Column(db.String(255), nullable=False)
	final_url = db.Column(db.String(255))
	contact_info = db.Column(db.Text)
	contact_page = db.Column(db.String(255))
	description = db.Column(db.Text)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	query_id = db.Column(db.Integer, db.ForeignKey('query.id'))
	source_id = db.Column(db.Integer, db.ForeignKey('lead_source.id'))
	created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
	valid = db.Column(db.Boolean, default=False)
	checked = db.Column(db.Boolean, default=False)
	hidden = db.Column(db.Boolean, default=False)
	liked = db.Column(db.Boolean, default=False)
	checking = db.Column(db.Boolean, default=False)
	hidden_at = db.Column(db.DateTime)
	quality_score = db.Column(db.Float)
	image_url = db.Column(db.String(255))
	jobs = db.relationship('Job', backref='lead', lazy='dynamic')

	def to_dict(self):
		return {
			'id': self.id,
			'guid': self.guid,
			'name': self.name,
			'base_url': self.base_url,
			'url': self.url,
			'final_url': self.final_url,
			'contact_info': self.contact_info,
			'contact_page': self.contact_page,
			'description': self.description,
			'user_id': self.user_id,
			'query_id': self.query_id,
			'source_id': self.source_id,
			'created_at': self.created_at.isoformat() if self.created_at else None,
			'valid': self.valid,
			'checked': self.checked,
			'hidden': self.hidden,
			'liked': self.liked,
			'checking': self.checking,
			'hidden_at': self.hidden_at.isoformat() if self.hidden_at else None,
			'quality_score': self.quality_score,
			'image_url': self.image_url,
			'lead_source': self.lead_source.to_dict() if self.lead_source else None,
			'query_obj': self.query_obj.to_dict() if self.query_obj else None,
		}

	@classmethod
	def get_by_id(cls, lead_id):
		return cls.query.get(lead_id)

	@classmethod
	def get_user_lead_count(cls, user_id):
		return cls.query.filter_by(user_id=user_id, hidden=False).count()

	@classmethod
	def get_user_leads(cls, user_id):
		return cls.query.filter_by(user_id=user_id, hidden=False).all()

	@classmethod
	def get_by_guid(cls, lead_guid):
		return cls.query.filter_by(guid=lead_guid).first()

	@classmethod
	def get_liked_leads(cls, user_id, n=None):
		query = cls.query.filter(cls.user_id == user_id, cls.liked == True, cls.hidden == False, cls.valid == True)
		if n:
			return query.order_by(db.func.random()).limit(5).all()
		return query.all()

	@classmethod
	def get_liked_leads_count(cls, user_id):
		return cls.query.filter_by(user_id=user_id, liked=True, hidden=False, valid=True).count()

	@classmethod
	def get_hidden_leads_count(cls, user_id):
		return cls.query.filter(cls.user_id == user_id, cls.hidden == True).count()

	@classmethod
	def get_hidden_leads(cls, user_id):
		return cls.query.filter(cls.user_id == user_id, cls.hidden == True).all()

	@classmethod
	def get_visible_leads(cls, user_id):
		return cls.query.filter(cls.user_id == user_id, cls.hidden == False, cls.valid == True).all()

	def save(self):
		if not self.id:
			db.session.add(self)
		db.session.commit()

	@classmethod
	def batch_update_quality_scores(cls, user_id, user, model, lead_ids=None):
		if not lead_ids or lead_ids == 'all':
			leads = cls.get_visible_leads(user_id)
		else:
			leads = cls.query.filter(cls.id.in_(lead_ids)).all()
		start_time = time.time()
		print(f'Updating quality scores for {len(leads)} sources')

		updates = []
		failed_updates = []

		for lead in leads:
			quality_score = model.predict_lead(user, lead)
			if quality_score is not None:
				lead.quality_score = quality_score
				updates.append(lead)
			else:
				failed_updates.append(lead.id)

		# Perform batch update
		for lead in updates:
			lead.save()

		# Update user's last trained timestamp
		user.last_trained_source_model_at = datetime.now(pytz.utc)
		user.save()

		print(f'Quality scores updated in {time.time() - start_time} seconds')
		print(f'Failed to update quality score for sources: {failed_updates}')

		return updates, failed_updates, user.last_trained_source_model_at

	@classmethod
	def check_and_add(cls, url, user_id, query_id, source_id, image_url=None):
		url = get_standard_url(url)
		base_url = get_base_url(url)

		existing_lead = cls.query.filter_by(base_url=base_url, hidden=False).first()
		if existing_lead or not _useful_url_check(url):
			return None
		new_lead = cls(
			url=url,
			base_url=base_url,
			user_id=user_id,
			query_id=query_id,
			source_id=source_id,
			image_url=image_url,
		)
		try:
			new_lead.save()
			return new_lead
		except Exception as e:
			print(f'Error adding lead: {e}')
			db.session.rollback()
			return None

	def _finished(self):
		self.checked = True
		self.checking = False

		self.save()


	@classmethod
	def batch_get_leads(cls, lead_ids):
		leads = cls.query.filter(cls.id.in_(lead_ids)).all()
		return leads

	@classmethod
	def train_leads_model(cls, user, liked_leads, hidden_leads, model):
		data_path = f"lead_training_data_{user.id}.txt"

		with open(data_path, "w") as f:
			for lead in liked_leads:
				input_text = model.make_lead_input_text(user, lead)
				if input_text.strip():
					f.write(f"__label__good {input_text}\n")
			for lead in hidden_leads:
				input_text = model.make_lead_input_text(user, lead)
				if input_text.strip():
					f.write(f"__label__bad {input_text}\n")

		# Perform random search to find best hyperparameters
		model.train_grid_search(data_path)
