from datetime import datetime
import pytz
from app import db
import uuid

class CreditLedgerType:
	QUERY = 'query'
	CHECK_QUERY = 'check_query_source'
	CHECK_LEAD = 'check_lead'
	REWRITE_QUERY = 'rewrite_query'
	CHECK_SOURCE = 'check_source'
	PAID = 'paid'

class CreditLedger(db.Model):
	__tablename__ = 'credit_ledger'

	id = db.Column(db.Integer, primary_key=True)
	guid = db.Column(db.String(36), nullable=False, default=lambda: str(uuid.uuid4()))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	amount = db.Column(db.Float, nullable=False)
	cost_usd = db.Column(db.Float)
	created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.utc))
	transaction_type = db.Column(db.String(50), nullable=False)
	transaction_description = db.Column(db.String(255), nullable=True)

	def __init__(self, user_id, amount, transaction_type, cost_usd=None, transaction_description=None):
		self.user_id = user_id
		self.amount = amount
		self.cost_usd = cost_usd
		self.transaction_type = transaction_type
		self.transaction_description = transaction_description

	def save(self):
		db.session.add(self)
		db.session.commit()

	@classmethod
	def get_by_id(cls, ledger_id):
		return cls.query.get(ledger_id)
