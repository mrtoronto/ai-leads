import time
from flask_login import UserMixin
import pytz
from datetime import datetime
from app import db
import uuid
import requests
import json

from app.models.query import Query
from app.models.lead_source import LeadSource
from app.models.lead import Lead
from app.models.credit_ledger import CreditLedger

class User(UserMixin, db.Model):
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True)
	guid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()))
	email = db.Column(db.String(150), unique=True, nullable=False)
	email_verified = db.Column(db.Boolean, default=False)
	password = db.Column(db.String(128), nullable=False)
	industry = db.Column(db.String(2000))
	preferred_org_size = db.Column(db.String(150))
	created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
	user_description = db.Column(db.String(5000))
	last_trained_lead_model_at = db.Column(db.DateTime)
	last_trained_source_model_at = db.Column(db.DateTime)
	credits = db.Column(db.Integer, default=0)
	model_preference = db.Column(db.String(50), default='gpt-4o-mini')

	is_admin = db.Column(db.Boolean, default=False)

	claimed_signup_bonus = db.Column(db.Boolean, default=False)
	claimed_verification_bonus = db.Column(db.Boolean, default=False)

	queries = db.relationship('Query', backref='user', lazy='dynamic')
	leads = db.relationship('Lead', backref='user', lazy='dynamic')
	sources = db.relationship('LeadSource', backref='user', lazy='dynamic')

	def __init__(self, username=None, email=None, password=None, id=None, **kwargs):
		self.id = id
		self.username = username
		self.email = email
		self.password = password
		self.industry = kwargs.get('industry')
		self.preferred_org_size = kwargs.get('preferred_org_size')
		self.created_at = kwargs.get('created_at', datetime.now(pytz.utc))
		self.user_description = kwargs.get('user_description')
		self.last_trained_lead_model_at = kwargs.get('last_trained_lead_model_at')
		self.last_trained_source_model_at = kwargs.get('last_trained_source_model_at')
		self.credits = kwargs.get('credits', 0)
		self.model_preference = kwargs.get('model_preference', 'gpt-4o-mini')
		return self

	def to_dict(self):
		return {
			'id': self.id,
			'username': self.username,
			'email': self.email,
			'password': self.password,
			'industry': self.industry,
			'preferred_org_size': self.preferred_org_size,
			'created_at': self.created_at.isoformat(),
			'user_description': self.user_description,
			'last_trained_lead_model_at': self.last_trained_lead_model_at,
			'last_trained_source_model_at': self.last_trained_source_model_at,
			'credits': self.credits,
			'model_preference': (self.model_preference or 'gpt-4o-mini'),
			'is_admin': self.is_admin,
			'claimed_verification_bonus': self.claimed_verification_bonus,
		}

	@classmethod
	def get_by_id(cls, user_id):
		return cls.query.get(user_id)

	@classmethod
	def get_by_email(cls, email):
		return cls.query.filter_by(email=email).first()

	@classmethod
	def get_by_username(cls, username):
		return cls.query.filter_by(username=username).first()

	def save(self):
		if not self.id:
			db.session.add(self)
		db.session.commit()

	def move_credits(self, amount, cost_usd, trxn_type, trxn_description="", app_obj=None, socketio_obj=None):
		self.credits += amount
		self.save()

		entry = CreditLedger(
			user_id=self.id,
			amount=amount,
			cost_usd=cost_usd,
			transaction_type=trxn_type,
			transaction_description=trxn_description
		)
		entry.save()

		credits_remaining = self.credits >= 0

		if socketio_obj and app_obj:
			with app_obj.app_context():
				print(f"Sending update_credits to user_{self.id}")
				socketio_obj.emit('update_credits', {'credits': self.credits}, to=f'user_{self.id}')

		return entry, credits_remaining


	def get_initial_data(self, data):
		get_requests = data.get('get_requests', True)
		get_lead_sources = data.get('get_lead_sources', True)
		get_leads = data.get('get_leads', True)
		get_hidden_leads = data.get('get_hidden_leads', False)
		get_hidden_queries = data.get('get_hidden_queries', False)
		get_in_progress = data.get('get_in_progress', False)
		request = None
		source = None
		lead = None

		requests = []
		lead_sources = []
		leads = []
		liked_leads = []
		hidden_leads = []

		query_id = data.get('query_id', None)
		source_id = data.get('source_id', None)
		lead_id = data.get('lead_id', None)

		if query_id:
			request = Query.get_by_id(query_id)
			lead_sources = LeadSource.query.filter_by(hidden=False, query_id=query_id).order_by(LeadSource.valid.desc(), LeadSource.checked, LeadSource.id.desc()).all()
			leads = Lead.query.filter_by(
				hidden=False,
				query_id=query_id
			).order_by(
				Lead.liked,
				Lead.relevant.desc(),
				Lead.valid.desc(),
				Lead.checked,
				Lead.id.desc()
			).all()

		elif source_id:
			source = LeadSource.get_by_id(source_id)
			leads = Lead.query.filter_by(
				user_id=self.id,
				hidden=False,
				source_id=source_id
			).order_by(
				Lead.liked,
				Lead.relevant.desc(),
				Lead.valid.desc(),
				Lead.checked,
				Lead.id.desc()
			).all()

		elif lead_id:
			lead = Lead.get_by_id(lead_id)

		else:
			if get_requests:
				if get_in_progress:
					requests = Query.query.filter_by(
						user_id=self.id,
						hidden=False,
						finished=False
					).order_by(Query.id.desc()).all()
				else:
					if get_hidden_queries:
						requests = Query.query.filter_by(user_id=self.id).order_by(Query.id.desc()).all()
					else:
						requests = Query.query.filter_by(user_id=self.id, hidden=False).order_by(Query.id.desc()).all()
			else:
				requests = []
			if get_lead_sources:
				if get_in_progress:
					lead_sources = LeadSource.query.filter_by(user_id=self.id, hidden=False, checking=True).order_by(LeadSource.valid.desc(), LeadSource.checked, LeadSource.id.desc()).all()
				else:
					lead_sources = LeadSource.query.filter_by(user_id=self.id, hidden=False).order_by(LeadSource.valid.desc(), LeadSource.checked, LeadSource.id.desc()).all()
			else:
				lead_sources = []

			if get_leads:
				if get_in_progress:
					leads = Lead.query.filter_by(
						user_id=self.id,
						hidden=False,
						checking=True
					).order_by(
							Lead.liked,
							Lead.relevant.desc(),
							Lead.valid.desc(),
							Lead.checked,
							Lead.id.desc()
						).all()
					hidden_leads = []
					liked_leads = []
				else:
					leads = Lead.query.filter_by(user_id=self.id).order_by(
						Lead.liked,
						Lead.relevant.desc(),
						Lead.valid.desc(),
						Lead.checked,
						Lead.id.desc()
					).all()
					hidden_leads = [l for l in leads if l.hidden]
					liked_leads = [l for l in leads if l.liked]
					if not get_hidden_leads:
						leads = [l for l in leads if not l.hidden]

		return {
			'requests': [r.to_dict() for r in requests],
			'lead_sources': [ls.to_dict() for ls in lead_sources],
			'leads': [l.to_dict() for l in leads],
			'n_liked': len(liked_leads),
			'n_hidden': len(hidden_leads),
			'query': request.to_dict(example_leads=True, cost=True) if request and query_id else (request.to_dict() if request else None),
			'source': source.to_dict() if source else None,
			'lead': lead.to_dict() if lead else None
		}
