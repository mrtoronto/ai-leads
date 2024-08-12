import pytz
from datetime import datetime
import uuid
import requests
import json
from app import db
from app.models.lead import Lead
from app.models.lead_source import LeadSource

class Query(db.Model):
	__tablename__ = 'query'
	id = db.Column(db.Integer, primary_key=True)
	guid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	user_query = db.Column(db.String(255), nullable=False)
	reformatted_query = db.Column(db.String(255))
	finished = db.Column(db.Boolean, default=False)
	run_notes = db.Column(db.Text)
	created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
	hidden_at = db.Column(db.DateTime)
	checking = db.Column(db.Boolean, default=True)
	hidden = db.Column(db.Boolean, default=False)

	leads = db.relationship('Lead', backref='query_obj', lazy='dynamic')
	sources = db.relationship('LeadSource', backref='query_obj', lazy='dynamic')

	jobs = db.relationship('Job', backref='query_obj', lazy='dynamic')

	def to_dict(self):
		return {
			'id': self.id,
			'guid': self.guid,
			'user_id': self.user_id,
			'user_query': self.user_query,
			'reformatted_query': self.reformatted_query,
			'finished': self.finished,
			'run_notes': self.run_notes,
			'created_at': self.created_at.isoformat(),
			'hidden_at': self.hidden_at.isoformat() if self.hidden_at else None,
			'checking': self.checking,
			'hidden': self.hidden,
			'n_sources': self.sources.filter_by(hidden=False).count(),
			'n_leads': self.leads.filter_by(hidden=False).count()
		}

	@classmethod
	def get_by_id(cls, query_id):
		return cls.query.get(query_id)

	@classmethod
	def get_by_guid(cls, query_guid):
		return cls.query.filter_by(guid=query_guid).first()

	def save(self):
		if not self.id:
			db.session.add(self)
		db.session.commit()

	def _finished(self, run_notes=None):
		self.checking = False
		self.finished = True
		if run_notes:
			self.run_notes = run_notes
		self.save()

	def get_leads(self):
		return Lead.query.filter_by(query_id=self.id).all()

	def get_sources(self):
		return LeadSource.query.filter_by(query_id=self.id).all()

	def _hide(self):
		self.hidden = True
		self.save()

		hidden_lead_ids = []
		hidden_source_ids = []

		for lead in self.get_leads():
			lead.hidden = True
			lead.save()
			hidden_lead_ids.append(lead.id)

		for lead_source in self.get_sources():
			lead_source.hidden = True
			lead_source.save()
			hidden_source_ids.append(lead_source.id)

		return hidden_source_ids, hidden_lead_ids
