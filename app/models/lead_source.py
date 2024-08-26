import time
from app.utils import get_base_url, get_standard_url, _real_url_check
import pytz
from datetime import datetime
from app.models.user_models import ModelTypes
import uuid
import requests
import json
from app import db
from app.models.lead import Lead
from app.models.job import Job

class LeadSource(db.Model):
	__tablename__ = 'lead_source'

	id = db.Column(db.Integer, primary_key=True)
	guid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True)
	name = db.Column(db.String(255))
	description = db.Column(db.Text)
	url = db.Column(db.String(255))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	query_id = db.Column(db.Integer, db.ForeignKey('query.id'))
	valid = db.Column(db.Boolean, default=False)
	created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
	checked = db.Column(db.Boolean, default=False)
	checking = db.Column(db.Boolean, default=False)
	image_url = db.Column(db.String(255))
	quality_score = db.Column(db.Float)

	hidden = db.Column(db.Boolean, default=False)
	hidden_at = db.Column(db.DateTime)
	auto_hidden = db.Column(db.Boolean, default=False)

	jobs = db.relationship('Job', backref='lead_source', lazy='dynamic')
	leads = db.relationship('Lead', backref='lead_source', lazy='dynamic')

	def _get_place_in_queue(self):
		if self.checking:
			jobs = self.jobs
			if jobs:
				job = jobs.filter_by(finished=False).order_by(Job.created_at.desc()).first()
				if job:
					return job.place_in_queue()

		return None

	def to_dict(self):
		return {
			'id': self.id,
			'guid': self.guid,
			'name': self.name,
			'description': self.description,
			'url': self.url,
			'user_id': self.user_id,
			'query_id': self.query_id,
			'query_obj': self.query_obj.to_dict() if self.query else None,
			'checked': self.checked,
			'valid': self.valid,
			'hidden': self.hidden,
			'created_at': self.created_at.isoformat() if self.created_at else None,
			'hidden_at': self.hidden_at.isoformat() if self.hidden_at else None,
			'checking': self.checking,
			'place_in_queue': self._get_place_in_queue(),
			'image_url': self.image_url,
			'quality_score': self.quality_score,
			'n_leads': self.leads.count()
		}

	@classmethod
	def get_by_id(cls, source_id):
		return cls.query.get(source_id)

	@classmethod
	def get_by_guid(cls, source_guid):
		return cls.query.filter_by(guid=source_guid).first()

	@classmethod
	def get_user_sources(cls, user_id):
		return cls.query.filter_by(user_id=user_id, hidden=False).all()

	@classmethod
	def batch_update_quality_scores(cls, user_id, user, model, source_ids=None):
		if not source_ids or source_ids == 'all':
			sources = cls.get_visible_sources(user_id)
		else:
			sources = cls.query.filter(cls.id.in_(source_ids)).all()
		start_time = time.time()
		print(f'Updating quality scores for {len(sources)} sources')

		updates = []
		failed_updates = []

		for source in sources:
			quality_score = model.predict_source(user, source)
			if quality_score is not None:
				source.quality_score = quality_score
				updates.append(source)
			else:
				failed_updates.append(source.id)

		db.session.bulk_save_objects(updates)
		db.session.commit()

		user.last_trained_source_model_at = datetime.now(pytz.utc)
		user.save()

		print(f'Quality scores updated in {time.time() - start_time} seconds')
		print(f'Failed to update quality score for sources: {failed_updates}')

		return updates, failed_updates, user.last_trained_source_model_at

	def save(self):
		if not self.id:
			db.session.add(self)
		db.session.commit()

	@classmethod
	def get_hidden_sources(cls, user_id):
		return cls.query.filter_by(user_id=user_id, hidden=True).all()

	@classmethod
	def get_visible_sources(cls, user_id):
		return cls.query.filter_by(user_id=user_id, hidden=False, valid=True).all()

	@classmethod
	def check_and_add(cls, url, user_id, query_id, image_url=None, checked=False, name=None, description=None, valid=False):
		url = get_standard_url(url)
		existing_source = cls.query.filter_by(url=url, hidden=False).first()
		if existing_source or not _real_url_check(url):
			return None
		new_source = cls(
			url=url,
			user_id=user_id,
			query_id=query_id,
			image_url=image_url,
			checked=checked,
			valid=valid,
			name=name,
			description=description
		)
		try:
			new_source.save()
			return new_source
		except Exception as e:
			print(f'Failed to save source {url} - {e}')
			db.session.rollback()
			return None

	def _finished(self, socketio_obj=None, app_obj=None):
		self.checking = False
		self.checked = True
		self.save()

		### Finish all jobs
		for job in self.jobs.filter_by(finished=False, started=True).all():
			job._finished(socketio_obj=socketio_obj, app_obj=app_obj)

	def _hide(self):
		self.hidden = True
		hidden_leads = []
		for lead in self.get_leads():
			if not lead.hidden:
				lead.hidden = True
				lead.auto_hidden = True
				lead.hidden_at = datetime.now(pytz.utc)
				hidden_leads.append(lead)

		db.session.commit()
		return hidden_leads

	def _unhide(self):
		self.hidden = False
		hidden_leads = []
		for lead in self.get_leads():
			if lead.auto_hidden:
				lead.hidden = False
				lead.auto_hidden = False
				lead.hidden_at = None
				hidden_leads.append(lead)

		db.session.commit()
		return hidden_leads

	def get_leads(self):
		return Lead.query.filter_by(source_id=self.id).all()

	@classmethod
	def batch_get_sources(cls, source_ids):
		return cls.query.filter(cls.id.in_(source_ids)).all()

	@classmethod
	def get_user_source_count(cls, user_id):
		return cls.query.filter_by(user_id=user_id, hidden=False).count()

	@classmethod
	def train_sources_model(cls, user, liked_leads, hidden_leads, hidden_sources, model):
		lead_source_ids = [lead.source_id for lead in liked_leads + hidden_leads if lead.source_id]
		lead_sources = LeadSource.batch_get_sources(lead_source_ids)
		lead_source_dict = {source.id: source for source in lead_sources}

		data_path = f"source_training_data_user_{user.id}.txt"

		with open(data_path, "w") as f:
			for lead in liked_leads:
				if lead.source_id and lead.source_id in lead_source_dict:
					source = lead_source_dict[lead.source_id]
					input_text = model.make_source_input_text(user, source)
					if input_text and input_text.strip():
						f.write(f"__label__good {input_text}\n")
				else:
					input_text = model.make_lead_input_text(user, lead)
					if input_text and input_text.strip():
						f.write(f"__label__good {input_text}\n")

			for lead in hidden_leads:
				if lead.source_id and lead.source_id in lead_source_dict:
					source = lead_source_dict[lead.source_id]
					input_text = model.make_source_input_text(user, source)
					if input_text and input_text.strip():
						f.write(f"__label__bad {input_text}\n")

			for source in hidden_sources:
				input_text = model.make_source_input_text(user, source)
				if input_text and input_text.strip():
					f.write(f"__label__bad {input_text}\n")

		model.train_grid_search(data_path)
