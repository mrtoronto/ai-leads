from app import worker_socketio, create_minimal_app
from app.models import LeadSource, Lead, User, ModelTypes, UserModels, CreditLedgerType
from rq import get_current_job
from app.llm import collect_leads_from_url
from app.utils import _tidy_url, _useful_url_check
from flask_socketio import emit
from worker import _make_min_app
from worker.fasttext import FastTextModel

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

		if (lead_source.checked and lead_source.valid):
			return

		if lead_source.hidden:
			lead_source._finished()
			return

		lead_source_user = User.get_by_id(lead_source.user_id)
		previously_liked_leads = Lead.get_liked_leads(lead_source.user_id, 5)
		previous_leads = [f'{lead.name} - {lead.description}' for lead in previously_liked_leads]
		previous_leads = '\n'.join(previous_leads) + '\n'
		previous_leads = previous_leads.strip()

		validation_output, opengraph_img_url, tokens_used = collect_leads_from_url(
			lead_source.url,
			lead_source_user,
			previous_leads,
			app_obj=min_app,
			socketio_obj=worker_socketio
		)

		logger.info(validation_output)

		with min_app.app_context():
			if 'mini' in (lead_source_user.model_preference or 'gpt-4o-mini'):
				mult = min_app.config['PRICING_MULTIPLIERS']['check_source_mini']
			else:
				mult = min_app.config['PRICING_MULTIPLIERS']['check_source']

			lead_source_user.move_credits(
				mult * -1000 * tokens_used,
				CreditLedgerType.CHECK_SOURCE,
				socketio_obj=worker_socketio,
				app_obj=min_app
			)

		if not validation_output:
			lead_source._finished()
			lead_source.valid = False
			lead_source.save()
			worker_socketio.emit('sources_updated', {'sources': [lead_source.to_dict()]}, to=f'user_{lead_source.user_id}')
			return

		if validation_output.not_enough_credits:
			lead_source.checking = False
			lead_source.save()
			worker_socketio.emit('sources_updated', {'sources': [lead_source.to_dict()]}, to=f'user_{lead_source.user_id}')
			return

		if validation_output.is_lead:
			new_lead_obj = Lead.check_and_add(
				url=lead_source.url,
				user_id=lead_source.user_id,
				query_id=lead_source.query_id,
				source_id=lead_source.id
			)
			if new_lead_obj:
				worker_socketio.emit('leads_updated', {'leads': [new_lead_obj.to_dict()]}, to=f'user_{lead_source.user_id}')

		lead_source.name = validation_output.name or lead_source.name
		lead_source.description = validation_output.description or lead_source.description
		lead_source.valid = bool(validation_output.name or validation_output.description)
		lead_source.image_url = opengraph_img_url or lead_source.image_url

		lead_source.checked = True
		lead_source.checking = False

		lead_source.save()

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
						worker_socketio.emit('leads_updated', {'leads': [new_lead_obj.to_dict()]}, to=f'user_{lead_source.user_id}')

		if validation_output.lead_sources:
			for new_lead_source in validation_output.lead_sources:
				if new_lead_source and new_lead_source.url and _useful_url_check(new_lead_source.url):
					new_source_obj = LeadSource.check_and_add(
						url=new_lead_source.url,
						user_id=lead_source.user_id,
						query_id=lead_source.query_id
					)
					if new_source_obj:
						worker_socketio.emit('sources_updated', {'sources': [lead_source.to_dict()]}, to=f'user_{lead_source.user_id}')

		lead_source._finished()

		worker_socketio.emit('sources_updated', {'sources': [lead_source.to_dict()]}, to=f'user_{lead_source.user_id}')
