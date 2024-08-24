from app import worker_socketio, create_minimal_app
from app.models import LeadSource, Lead, ModelTypes, User, CreditLedgerType, Job
from rq import get_current_job
from app.llm import _llm_validate_lead, collect_leads_from_url
from app.utils import _tidy_url, _useful_url_check
from flask_socketio import emit
from worker.fasttext import FastTextModel
from app import db
from worker import _make_min_app

import logging

logger = logging.getLogger('BDB-2EB')

def check_lead_task(lead_id):
	"""
	Task to check if a specific lead is:
		- Valid
		- Not a duplicate
		- Relevant to the user
		- Has contact information
	"""
	job = get_current_job()
	min_app = _make_min_app()
	if not min_app:
		logger.error("Failed to create app context")
		return
	with min_app.app_context():
		job = get_current_job()

		job_obj = Job.query.filter_by(lead_id=lead_id).first()
		if job_obj:
			job_obj._started(job.id if job else None)

		lead = Lead().get_by_id(lead_id)
		if not lead:
			return

		if lead.checked and lead.valid:
			return

		if lead.hidden:
			lead._finished(
				socketio_obj=worker_socketio,
				app_obj=min_app
			)
			return

		total_tokens_used_usd = 0

		lead_user = User.get_by_id(lead.user_id)
		first_validation_output, opengraph_img_url, tokens_used_usd = _llm_validate_lead(
			link=lead.url,
			query=lead.query_obj,
			user=lead_user
		)
		total_tokens_used_usd += tokens_used_usd
		final_validation_output = first_validation_output

		# logger.info(first_validation_output)
		if not first_validation_output:
			lead._finished(
				socketio_obj=worker_socketio,
				app_obj=min_app
			)
			lead.save()
			worker_socketio.emit('leads_updated', {'leads': [lead.to_dict()]}, to=f'user_{lead.user_id}')
			return

		if (first_validation_output.next_link or first_validation_output.contact_page) and not first_validation_output.email_address:
			loop_idx = 0
			validation_output = first_validation_output
			while (validation_output.next_link or validation_output.contact_page) and not (validation_output.email_address):
				next_link = (validation_output.next_link or validation_output.contact_page or "")

				if next_link.startswith('/') and lead.url:
					base_url = lead.url.split('/')
					base_url = '/'.join(base_url[:3])
					next_link = base_url + next_link

				validation_output, opengraph_img_url, tokens_used_usd = _llm_validate_lead(
					link=next_link,
					user=lead_user,
					query=lead.query_obj,
				)

				total_tokens_used_usd += tokens_used_usd
				# logger.info(validation_output)
				if validation_output:

					if validation_output.not_enough_credits or final_validation_output.not_enough_credits:
						lead.checking = False
						lead.save()
						worker_socketio.emit('leads_updated', {'leads': [lead.to_dict()]}, to=f'user_{lead.user_id}')
						return

					if not final_validation_output:
						final_validation_output = validation_output
					if validation_output.contact_page and not final_validation_output.contact_page:
						final_validation_output.contact_page = validation_output.contact_page

					if validation_output.email_address and not final_validation_output.email_address:
						final_validation_output.email_address = validation_output.email_address

					if validation_output.name and not final_validation_output.name:
						final_validation_output.name = validation_output.name

					if validation_output.description and not final_validation_output.description:
						final_validation_output.description = validation_output.description

					if not final_validation_output.leads:
						final_validation_output.leads = validation_output.leads

					if not final_validation_output.relevant_to_user:
						final_validation_output.relevant_to_user = validation_output.relevant_to_user

					if validation_output.leads:
						if final_validation_output.leads:
							final_validation_output.leads += validation_output.leads
						else:
							final_validation_output.leads = validation_output.leads

					if not final_validation_output.lead_sources:
						final_validation_output.lead_sources = validation_output.lead_sources

					if validation_output.lead_sources:
						if final_validation_output.lead_sources:
							final_validation_output.lead_sources += validation_output.lead_sources
						else:
							final_validation_output.lead_sources = validation_output.lead_sources


				if not validation_output or loop_idx > 3:
					break
				loop_idx += 1

		# logger.info(final_validation_output)

		if not final_validation_output:
			logger.error("No validation output")
			lead._finished(
				socketio_obj=worker_socketio,
				app_obj=min_app
			)
			lead.save()
			worker_socketio.emit('leads_updated', {'leads': [lead.to_dict()]}, to=f'user_{lead.user_id}')
			return

		if final_validation_output.not_enough_credits:
			lead.checking = False
			lead.save()
			worker_socketio.emit('leads_updated', {'leads': [lead.to_dict()]}, to=f'user_{lead.user_id}')
			return

		lead.name = final_validation_output.name or lead.name
		lead.relevant = final_validation_output.relevant_to_user or lead.relevant
		lead.image_url = opengraph_img_url or lead.image_url
		lead.description = final_validation_output.description or lead.description
		lead.contact_info = final_validation_output.email_address or lead.contact_info
		lead.valid = bool(final_validation_output.email_address or final_validation_output.contact_page or final_validation_output.next_link or final_validation_output.no_email_found)
		lead.contact_page = _tidy_url(lead.url, final_validation_output.contact_page or final_validation_output.next_link) if (final_validation_output.contact_page or final_validation_output.next_link) else ""
		lead.checked = True
		lead.checking = False
		lead.save()

		if final_validation_output.lead_sources:
			for new_lead_source in final_validation_output.lead_sources:
				if new_lead_source and new_lead_source.url and _useful_url_check(new_lead_source.url):
					new_source = LeadSource.check_and_add(
						url=new_lead_source.url,
						user_id=lead.user_id,
						query_id=lead.query_id
					)
					if new_source:
						worker_socketio.emit('sources_updated', {'sources': [new_source.to_dict()]}, to=f'user_{lead.user_id}')


		### If lead check had leads in to,
		### Add lead as a source and save new leads to that source
		if final_validation_output.leads:
			new_source = LeadSource.check_and_add(
				url=lead.url,
				user_id=lead.user_id,
				query_id=lead.query_id,
				checked=True,
				name=lead.name,
				description=lead.description,
				image_url=lead.image_url,
			)
			if new_source:
				worker_socketio.emit('sources_updated', {'sources': [new_source.to_dict()]}, to=f'user_{lead.user_id}')

			for new_lead in final_validation_output.leads:
				if new_lead and new_lead.url and _useful_url_check(new_lead.url):
					new_lead_obj = Lead.check_and_add(
						url=new_lead.url,
						user_id=lead.user_id,
						query_id=lead.query_id,
						source_id=new_source.id if new_source else lead.source_id
					)
					if new_lead_obj:
						worker_socketio.emit('leads_updated', {'leads': [new_lead_obj.to_dict()]}, to=f'user_{lead.user_id}')

		model = FastTextModel(lead.user_id, ModelTypes.LEAD)
		lead.quality_score = model.predict_lead(lead_user, lead)
		lead._finished(
			socketio_obj=worker_socketio,
			app_obj=min_app
		)
		db.session.commit()

		if 'mini' in (lead_user.model_preference or 'gpt-4o-mini'):
			mult = min_app.config['PRICING_MULTIPLIERS']['check_lead_mini']
		else:
			mult = min_app.config['PRICING_MULTIPLIERS']['check_lead']

		with min_app.app_context():
			lead_user.move_credits(
				tokens_used_usd * -1000 * mult,
				CreditLedgerType.CHECK_LEAD,
				socketio_obj=worker_socketio,
				app_obj=min_app
			)

		worker_socketio.emit('leads_updated', {'leads': [lead.to_dict()]}, to=f'user_{lead.user_id}')
