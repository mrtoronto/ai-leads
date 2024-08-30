from app import worker_socketio, create_minimal_app, db
from app.models import LeadSource, Lead, Query, User, CreditLedgerType,Journey, Job, JobTypes
from rq import get_current_job
from app.llm import collect_leads_from_url
from app.llm._rewrite import rewrite_query
from flask_socketio import emit
from worker import _make_min_app
from local_settings import SERP_API_KEY
import requests

import logging
logger = logging.getLogger('BDB-2EB')


def search_serpapi(query):
	q = query.user_query
	num_requested = max(1, query.n_results_requested - query.n_results_retrieved)
	start = query.n_results_retrieved
	params = {
		'q': query.user_query,
		'hl': 'en',
		'gl': 'us',
		'google_domain': 'google.com',
		'api_key': SERP_API_KEY,
		'num': num_requested,
		'start': start
	}



	l = query.location
	if l and l.strip():
		params['location'] = l
		location_params = {
			'q': l,
			'limit': 1,
			'api_key': SERP_API_KEY
		}
		location_response = requests.get('https://serpapi.com/locations.json', params=location_params)
		logger.info(f'location_response: {location_response.status_code}, {location_response.json()}')
		if location_response.status_code == 200 and location_response.json():
			params['gl'] = location_response.json()[0].get('country_code')

	logger.info(f'Searching SERP API w/ data: {params}')

	response = requests.get('https://serpapi.com/search', params=params)
	if response.status_code == 200:
		return response.json()
	else:
		return None

def search_and_validate_leads(new_query, previous_leads, app_obj, socketio_obj, query_job_obj):
	"""
	Runs a search query and checks each source found in the query for leads and other lead sources
	"""

	if new_query.user.credits < 1:
		return [], "Insufficient credits", 0
	search_results = search_serpapi(new_query)

	# print(search_results)
	if not search_results:
		return [], "Failed to search SERP API", 0

	leads = []
	for result in search_results.get('organic_results', []):
		url = result.get('link')

		collected_leads, image_url, tokens_used_usd = collect_leads_from_url(
			url=url,
			query=new_query,
			user=new_query.user,
			previous_leads=previous_leads,
			app_obj=app_obj,
			socketio_obj=socketio_obj
		)

		logger.info(collected_leads)

		if collected_leads and collected_leads.not_enough_credits:
			return [], "Insufficient credits"

		if not collected_leads or (not collected_leads.leads and not collected_leads.lead_sources):
			continue

		new_source_obj = LeadSource.check_and_add(
			url,
			new_query.user_id,
			new_query.id,
			image_url=image_url,
			checked=True,
			name=collected_leads.name,
			description=collected_leads.description,
			valid=(True if collected_leads.name else False)
		)

		if new_source_obj and socketio_obj and app_obj:
			with app_obj.app_context():
				socketio_obj.emit('sources_updated', {'sources': [new_source_obj.to_dict()]}, to=f'user_{new_query.user_id}')

		if collected_leads.leads:
			for lead in collected_leads.leads:
				new_lead_obj = Lead.check_and_add(
					url=lead.url,
					user_id=new_query.user_id,
					query_id=new_query.id,
					source_id=None,
				)
				if new_lead_obj and app_obj:

					if new_lead_obj.query_id and new_lead_obj.query_obj.auto_check:
						new_lead_obj.checking = True
						new_lead_obj.save()

						app_obj.config['high_priority_queue'].enqueue('worker.check_lead.check_lead_task', new_lead_obj.id)

						new_job = Job(
							lead_id=new_lead_obj.id,
							_type=JobTypes.LEAD_CHECK,
						)

						new_job.save()

					if socketio_obj:
						with app_obj.app_context():
							socketio_obj.emit('leads_updated', {'leads': [new_lead_obj.to_dict()]}, to=f'user_{new_query.user_id}')

		if collected_leads.lead_sources:
			for lead_source in collected_leads.lead_sources:
				new_source_obj = LeadSource.check_and_add(
					url=lead_source.url,
					user_id=new_query.user_id,
					query_id=new_query.id
				)
				if new_source_obj and app_obj:

					if new_source_obj.query_id and new_source_obj.query_obj.auto_check:

						new_source_obj.checking = True
						new_source_obj.save()

						app_obj.config['high_priority_queue'].enqueue('worker.check_lead_source.check_lead_source_task', new_source_obj.id)

						new_job = Job(
							source_id=new_source_obj.id,
							_type=JobTypes.SOURCE_CHECK,
						)

						new_job.save()

					if socketio_obj:
						with app_obj.app_context():
							socketio_obj.emit('sources_updated', {'sources': [new_source_obj.to_dict()]}, to=f'user_{new_query.user_id}')

		new_query.n_results_retrieved += 1
		new_query.save()

		if socketio_obj and app_obj:
			with app_obj.app_context():
				socketio_obj.emit('queries_updated', {'queries': [new_query.to_dict(example_leads=True, cost=True)]}, to=f'user_{new_query.user_id}')

		if 'mini' in (new_query.user.model_preference or 'gpt-4o-mini'):
			mult = app_obj.config['PRICING_MULTIPLIERS']['check_source_mini']
		else:
			mult = app_obj.config['PRICING_MULTIPLIERS']['check_source']

		query_job_obj.total_cost_credits += tokens_used_usd * mult * 1000
		query_job_obj.unique_cost_credits += tokens_used_usd * mult * 1000
		query_job_obj.save()

		new_query.user.move_credits(
			amount=mult * -1000 * tokens_used_usd,
			cost_usd=tokens_used_usd,
			trxn_type=CreditLedgerType.CHECK_QUERY,
			socketio_obj=worker_socketio,
			app_obj=app_obj
		)

		if new_query.budget and query_job_obj.total_cost_credits > new_query.budget:
			new_query.over_budget = True
			new_query.save()
			break

	new_query.n_results_requested = new_query.n_results_retrieved
	new_query.save()

	if socketio_obj and app_obj:
		with app_obj.app_context():
			socketio_obj.emit('queries_updated', {'queries': [new_query.to_dict(example_leads=True, cost=True)]}, to=f'user_{new_query.user_id}')

	return True, ""




def search_request_task(query_id):

	min_app = _make_min_app()
	if not min_app:
		logger.error("Failed to create app context")
		return
	with min_app.app_context():
		job = get_current_job()

		query_job_obj = Job.query.filter_by(query_id=query_id).first()
		if query_job_obj:
			query_job_obj._started(job.id if job else None)
		else:
			new_job = Job(
				query_id=query_id,
				_type=JobTypes.QUERY_CHECK,
			)
			new_job.save()
			new_job._started(job.id if job else None)
			query_job_obj = new_job
		request = Query.get_by_id(query_id)

		if not request:
			return

		if request.finished:
			return
		if request.hidden:
			request._finished(
				socketio_obj=worker_socketio,
				app_obj=min_app
			)
			return

		request_user = request.user
		previously_liked_leads = Lead.get_liked_leads(request_user.id, 5)

		previous_leads = [f'{lead.name} - {lead.description}' for lead in previously_liked_leads]
		previous_leads = '\n'.join(previous_leads) + '\n'
		previous_leads = previous_leads.strip()

		if request:
			logger.info(f'Searching for leads for query: {request.user_query}')
			# rephrased_query = rewrite_query(request, socketio_obj=worker_socketio)
			# if rephrased_query:
			# 	logger.info(f'Rephrased query: {rephrased_query.rewritten_query}')
			# 	request.reformatted_query = rephrased_query.rewritten_query
			# 	request.save()
			# else:
			# 	logger.error(f'Failed to rephrase query: {request.user_query}')

			# request.reformatted_query = request.user_query
			# request.save()


			# worker_socketio.emit('queries_updated', {'queries': [request.to_dict(example_leads=True)]}, to=f'user_{request.user_id}')

			with min_app.app_context():

				token_charge = min_app.config['PRICING_MULTIPLIERS']['query']

				request.user.move_credits(
					amount=token_charge * -1,
					cost_usd=0.01,
					trxn_type=CreditLedgerType.QUERY,
					socketio_obj=worker_socketio,
					app_obj=min_app
				)

			query_job_obj.total_cost_credits += token_charge
			query_job_obj.unique_cost_credits += token_charge
			query_job_obj.save()

			success, error = search_and_validate_leads(
				request,
				previous_leads,
				app_obj=min_app,
				socketio_obj=worker_socketio,
				query_job_obj=query_job_obj
			)

			if error:
				request._finished(
					run_notes=f'Error // {error}',
					socketio_obj=worker_socketio,
					app_obj=min_app
				)
				worker_socketio.emit('queries_updated', {'queries': [request.to_dict(example_leads=True, cost=True)]}, to=f'user_{request.user_id}')
				return

			request._finished(
				socketio_obj=worker_socketio,
				app_obj=min_app
			)
			worker_socketio.emit('queries_updated', {'queries': [request.to_dict(example_leads=True, cost=True)]}, to=f'user_{request.user_id}')

		return
