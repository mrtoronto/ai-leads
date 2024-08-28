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

	started = db.Column(db.Boolean, default=False)
	started_at = db.Column(db.DateTime)
	finished = db.Column(db.Boolean, default=False)
	finished_at = db.Column(db.DateTime)

	redis_job_id = db.Column(db.String(255))

	total_cost_credits = db.Column(db.Float, default=0)
	unique_cost_credits = db.Column(db.Float, default=0)

	def save(self):
		if not self.id:
			db.session.add(self)
		db.session.commit()

	def _finished(self, app_obj=None, socketio_obj=None):
		self.finished = True
		db.session.commit()

		if app_obj and socketio_obj:
			### Get all unstarted, unfinished jobs, emit their updated place in the queue
			with app_obj.app_context():
				jobs = Job.query.filter_by(finished=False).all()
				queries_updated = []
				sources_updated = []
				leads_updated = []
				unique_users = set()
				for job in jobs:
					if job.query_id:
						queries_updated.append(job.query_obj)
						unique_users.add(job.query_obj.user_id)
					elif job.source_id:
						sources_updated.append(job.lead_source)
						unique_users.add(job.lead_source.user_id)

					elif job.lead_id:
						leads_updated.append(job.lead)
						unique_users.add(job.lead.user_id)


				queries_updated = [q.to_dict() for q in queries_updated]
				sources_updated = [s.to_dict() for s in sources_updated]
				leads_updated = [l.to_dict() for l in leads_updated]

				for user_id in unique_users:
					user_queries = [q for q in queries_updated if q['user_id'] == user_id]
					user_sources = [s for s in sources_updated if s['user_id'] == user_id]
					user_leads = [l for l in leads_updated if l['user_id'] == user_id]
					if user_queries:
						socketio_obj.emit('queries_updated', {'queries': user_queries}, to=f'user_{user_id}')
					if user_sources:
						socketio_obj.emit('sources_updated', {'sources': user_sources}, to=f'user_{user_id}')
					if user_leads:
						socketio_obj.emit('leads_updated', {'leads': user_leads}, to=f'user_{user_id}')


		self.finished_at = datetime.now(pytz.utc)
		db.session.commit()

		elapsed_time = self.finished_at - self.started_at
		print('Job {} finished in {} seconds'.format(self.guid, elapsed_time.total_seconds()))

	def _started(self, redis_job_id):
		self.started = True
		self.started_at = datetime.now(pytz.utc)
		self.redis_job_id = redis_job_id
		db.session.commit()


	def place_in_queue(self):
		"""
		Calculates jobs place in the queue
		"""

		# Get all jobs of the same type
		jobs = Job.query.filter_by(finished=False).all()
		# Get the job's place in the queue
		place = 0
		for job in jobs:
			if job.created_at < self.created_at:
				place += 1
		return place
