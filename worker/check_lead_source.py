from app import worker_socketio, create_minimal_app
from app.models import LeadSource, Lead, User
from rq import get_current_job
from app.llm import collect_leads_from_url
from app.utils import _tidy_url, _useful_url_check
from flask_socketio import emit
from worker import _make_min_app

import logging

logger = logging.getLogger('BDB-2EB')

def check_lead_source_task(lead_source_id):
	job = get_current_job()
	min_app = _make_min_app()
	if not min_app:
		logger.error("Failed to create app context")
		return
	with min_app.app_context():
		lead_source = LeadSource.get_by_id(lead_source_id)
		if not lead_source:
			return

		lead_source_user = User.get_by_id(lead_source.user_id)
		previously_liked_leads = Lead.get_liked_leads(lead_source.user_id, 5)
		previous_leads = [f'{lead.name} - {lead.description}' for lead in previously_liked_leads]
		previous_leads = '\n'.join(previous_leads) + '\n'
		previous_leads = previous_leads.strip()

		validation_output = collect_leads_from_url(lead_source.url, lead_source_user, previous_leads)

		if not validation_output:
			lead_source._finished()
			lead_source.save()
			worker_socketio.emit('source_checked', {'source': lead_source.to_dict()}, to=f'user_{lead_source.user_id}')
			return

		lead_source.name = validation_output.name or lead_source.name
		lead_source.description = validation_output.description or lead_source.description
		lead_source.valid = bool(validation_output.name or validation_output.description)

		lead_source.checked = True
		lead_source.checking = False

		lead_batch = []
		source_batch = []

		if validation_output.leads:
			for new_lead in validation_output.leads:
				if new_lead and new_lead.url and _useful_url_check(new_lead.url):
					new_lead_obj = Lead.check_and_add(
						url=new_lead.url,
						user_id=lead_source.user_id,
						query_id=lead_source.query_id,
						source_id=lead_source.id
					)
					if new_lead_obj:
						lead_batch.append(new_lead_obj)

		if validation_output.lead_sources:
			for new_lead_source in validation_output.lead_sources:
				if new_lead_source and new_lead_source.url and _useful_url_check(new_lead_source.url):
					new_source_obj = LeadSource.check_and_add(
						url=new_lead_source.url,
						user_id=lead_source.user_id,
						query_id=lead_source.query_id
					)
					if new_source_obj:
						source_batch.append(new_source_obj)

		lead_source.save_checked_source(lead_batch=lead_batch, source_batch=source_batch)

		for lead in lead_batch:
			if lead:
				worker_socketio.emit('new_lead', {'lead': lead.to_dict()}, to=f'user_{lead_source.user_id}')

		for source in source_batch:
			if source:
				worker_socketio.emit('new_lead_source', {'source': source.to_dict()}, to=f'user_{lead_source.user_id}')

		worker_socketio.emit('source_checked', {'source': lead_source.to_dict()}, to=f'user_{lead_source.user_id}')
