from app.models.job import JobTypes
from . import create_minimal_app, worker_socketio
from .models import LeadSource, Lead, User, UserModels, ModelTypes, Job
from rq import get_current_job
from .llm import _llm_validate_lead
from flask_socketio import emit
from worker.check_lead import check_lead_task
from worker.check_lead_source import check_lead_source_task
from worker.process_search import search_request_task
from worker.log_journey import log_journey_task
from worker.fasttext import FastTextModel, retrain_models_task, update_qualities
from worker import _make_min_app
import time
from datetime import datetime
import pytz

import logging

logger = logging.getLogger('BDB-2EB')


def delegate_update_qualities_task(user_id):
	min_app = _make_min_app()
	if not min_app:
		logger.error('Failed to create minimal app')
		return
	with min_app.app_context():
		n_leads = Lead.get_user_lead_count(user_id)
		n_sources = LeadSource.get_user_source_count(user_id)

		if n_leads > 200:
			### Create chunks of 100 leads to process per task
			leads = Lead.get_visible_leads(user_id)
			chunk_size = 100
			n_chunks = n_leads // chunk_size
			if n_leads % chunk_size:
				n_chunks += 1

			for i in range(n_chunks):
				lead_ids = [lead.id for lead in leads[i * chunk_size:(i + 1) * chunk_size]]
				queue_update_qualities_task(user_id, lead_ids=lead_ids)
		else:
			queue_update_qualities_task(user_id, lead_ids='all')


		if n_sources > 200:
			### Create chunks of 100 sources to process per task
			sources = LeadSource.get_visible_sources(user_id)
			chunk_size = 100
			n_chunks = n_sources // chunk_size
			if n_sources % chunk_size:
				n_chunks += 1

			for i in range(n_chunks):
				source_ids = [source.id for source in sources[i * chunk_size:(i + 1) * chunk_size]]
				queue_update_qualities_task(user_id, source_ids=source_ids)

		else:
			queue_update_qualities_task(user_id, source_ids='all')



def queue_retrain_models_task(user_id):
	min_app = _make_min_app()
	if not min_app:
		logger.error('Failed to create minimal app')
		return
	min_app.config['low_priority_queue'].enqueue(retrain_models_task, user_id)

def queue_update_qualities_task(user_id, lead_ids=None, source_ids=None):
	min_app = _make_min_app()
	if not min_app:
		logger.error('Failed to create minimal app')
		return
	min_app.config['high_priority_queue'].enqueue(update_qualities, {'user_id': user_id, 'source_ids': source_ids, 'lead_ids': lead_ids})

def queue_check_lead_task(lead_id):
	min_app = _make_min_app()
	if not min_app:
		logger.error('Failed to create minimal app')
		return
	min_app.config['high_priority_queue'].enqueue(check_lead_task, lead_id)

	new_job = Job(
		lead_id=lead_id,
		_type=JobTypes.LEAD_CHECK,
	)
	new_job.save()

def queue_check_lead_source_task(source_id):
	min_app = _make_min_app()
	if not min_app:
		logger.error('Failed to create minimal app')
		return
	min_app.config['high_priority_queue'].enqueue(check_lead_source_task, source_id)

	new_job = Job(
		source_id=source_id,
		_type=JobTypes.SOURCE_CHECK,
	)
	new_job.save()

def queue_search_request(query_id):
	min_app = _make_min_app()
	if not min_app:
		logger.error('Failed to create minimal app')
		return
	min_app.config['high_priority_queue'].enqueue(search_request_task, query_id)

	new_job = Job(
		query_id=query_id,
		_type=JobTypes.QUERY_CHECK,
	)
	new_job.save()
