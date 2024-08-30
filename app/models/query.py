import pytz
from datetime import datetime
import uuid
import requests
import json
from app import db
from app.models.lead import Lead
from app.models.lead_source import LeadSource
from app.models.job import Job

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

	auto_check = db.Column(db.Boolean, default=False)
	auto_hide_invalid = db.Column(db.Boolean, default=False)

	budget = db.Column(db.Float)
	over_budget = db.Column(db.Boolean, default=False)

	location = db.Column(db.String(255))
	location_country = db.Column(db.String(10))

	n_results_retrieved = db.Column(db.Integer, default=0)
	n_results_requested = db.Column(db.Integer, default=0)

	leads = db.relationship('Lead', backref='query_obj', lazy='dynamic')
	sources = db.relationship('LeadSource', backref='query_obj', lazy='dynamic')

	jobs = db.relationship('Job', backref='query_obj', lazy='dynamic')

	def _get_place_in_queue(self):
		if self.checking:
			jobs = self.jobs
			if jobs:
				job = jobs.filter_by(finished=False).order_by(Job.created_at.desc()).first()
				if job:
					return job.place_in_queue()
		return None

	def to_dict(self, example_leads=False, cost=False):
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
			'place_in_queue': self._get_place_in_queue(),
			'hidden': self.hidden,
			'n_sources': self.sources.filter_by(hidden=False).count(),
			'n_leads': self.leads.filter_by(hidden=False).count(),
			'example_leads': [l.to_dict() for l in self.leads.filter_by(example_lead=True).all()] if example_leads else [],
			'location': self.location,
			'location_country': self.location_country,
			'budget': self.budget,
			'n_results_retrieved': self.n_results_retrieved,
			'n_results_requested': self.n_results_requested,
			'over_budget': self.over_budget,
			'auto_check': self.auto_check,
			'auto_hide_invalid': self.auto_hide_invalid,
			'cost': self.jobs.order_by(Job.id.desc()).first().total_cost_credits if cost else None

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

	def _finished(self, run_notes=None, socketio_obj=None, app_obj=None):
		self.checking = False
		self.finished = True
		if run_notes:
			self.run_notes = run_notes
		self.save()

		### Finish all jobs
		for job in self.jobs.filter_by(finished=False).all():
			job._finished(socketio_obj=socketio_obj, app_obj=app_obj)

		if self.over_budget:
			### If query is overbudget, finish all started leads and sources
			for lead in self.leads.filter_by(checking=True).all():
				lead._finished(checked=False, socketio_obj=socketio_obj, app_obj=app_obj)
			for source in self.sources.filter_by(checking=True).all():
				source._finished(checked=False, socketio_obj=socketio_obj, app_obj=app_obj)

			db.session.commit()

		if app_obj and socketio_obj:
			with app_obj.app_context():
				socketio_obj.emit('queries_updated', {'queries': [self.to_dict()]}, to=f'user_{self.user_id}')

	def get_leads(self):
		return Lead.query.filter_by(query_id=self.id).all()

	def get_sources(self):
		return LeadSource.query.filter_by(query_id=self.id).all()

	def _hide(self, socketio_obj=None, app_obj=None):
		self.hidden = True
		self.finished = True
		self.n_results_requested = self.n_results_retrieved
		self.checking = False
		self.hidden_at = datetime.now(pytz.utc)
		self.save()

		if app_obj and socketio_obj:
			with app_obj.app_context():
				socketio_obj.emit('queries_updated', {'queries': [self.to_dict()]}, to=f'user_{self.user_id}')

		for lead in self.get_leads():
			if not lead.hidden:
				lead._hide(auto_hidden=True, app_obj=app_obj, socketio_obj=socketio_obj)

			lead._finished(checked=lead.checked, socketio_obj=socketio_obj, app_obj=app_obj)


		for lead_source in self.get_sources():
			if not lead_source.hidden:
				lead_source._hide(auto_hidden=True, app_obj=app_obj, socketio_obj=socketio_obj)
			lead_source._finished(checked=lead_source.checked, socketio_obj=socketio_obj, app_obj=app_obj)

		for job in self.jobs.filter_by(finished=False).all():
			job._finished(socketio_obj=socketio_obj, app_obj=app_obj)

		if app_obj and socketio_obj:
			with app_obj.app_context():
				socketio_obj.emit('queries_updated', {'queries': [self.to_dict()]}, to=f'user_{self.user_id}')


	def _unhide(self, socketio_obj=None, app_obj=None):
		self.hidden = False
		self.save()

		if app_obj and socketio_obj:
			with app_obj.app_context():
				socketio_obj.emit('queries_updated', {'queries': [self.to_dict()]}, to=f"user_{self.user_id}")

		for lead_source in self.get_sources():
			if lead_source.auto_hidden:
				lead_source._unhide(app_obj=app_obj, socketio_obj=socketio_obj)

		for lead in self.get_leads():
			if lead.auto_hidden:
				lead = lead._unhide(app_obj=app_obj, socketio_obj=socketio_obj)

		if app_obj and socketio_obj:
			with app_obj.app_context():
				socketio_obj.emit('queries_updated', {'queries': [self.to_dict()]}, to=f"user_{self.user_id}")
