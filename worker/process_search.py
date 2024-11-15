from app import worker_socketio, create_minimal_app, db
from app.models import LeadSource, Lead, Query, User, CreditLedgerType,Journey, Job, JobTypes
from worker.check_lead import check_lead_task
from rq import get_current_job
from app.llm import collect_leads_from_url
from app.llm._rewrite import rewrite_query
from flask_socketio import emit
from worker import _make_min_app
from local_settings import SERP_API_KEY
import requests
from sqlalchemy.orm import joinedload


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

def search_and_validate_leads(new_query_id, previous_leads, app_obj, socketio_obj, query_job_obj, session):
	"""
	Runs a search query and checks each source found in the query for leads and other lead sources
	"""
	new_query = session.query(Query).get(new_query_id)
	if not new_query:
		return [], "Query not found", 0

	user = session.query(User).get(new_query.user_id)
	if user.credits < 1:
		return [], "Insufficient credits", 0

	search_results = search_serpapi(new_query)
	if not search_results:
		return [], "Failed to search SERP API", 0

	if 'mini' in (user.model_preference or 'gpt-4o-mini'):
		mult = app_obj.config['PRICING_MULTIPLIERS']['check_source_mini']
	else:
		mult = app_obj.config['PRICING_MULTIPLIERS']['check_source']

	total_tokens_used_usd = 0
	for result in search_results.get('organic_results', []):
		url = result.get('link')
		collected_leads, image_url, tokens_used_usd = collect_leads_from_url(
			url=url,
			query=new_query,
			user=user,
			previous_leads=previous_leads,
		)
		total_tokens_used_usd += tokens_used_usd
		
		if new_query.total_cost_credits:
			new_query.total_cost_credits += tokens_used_usd * mult * 1000
		else:
			new_query.total_cost_credits = tokens_used_usd * mult * 1000
		if new_query.unique_cost_credits:
			new_query.unique_cost_credits += tokens_used_usd * mult * 1000
		else:
			new_query.unique_cost_credits = tokens_used_usd * mult * 1000

		user.move_credits(
			amount=mult * -1000 * tokens_used_usd,
			cost_usd=tokens_used_usd,
			trxn_type=CreditLedgerType.CHECK_QUERY,
			socketio_obj=socketio_obj,
			app_obj=app_obj,
			session=session
		)

		if new_query.budget and new_query.total_cost_credits and new_query.total_cost_credits > new_query.budget:
			new_query.over_budget = True

		session.commit()

		if socketio_obj and app_obj:
			with app_obj.app_context():
				socketio_obj.emit('queries_updated', {'queries': [new_query.to_dict(example_leads=True, cost=True)]}, to=f'user_{new_query.user_id}')

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
			valid=(True if collected_leads.name else False),
			session=session
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
					checking=True,
					source_id=None,
					session=session
				)
				if new_lead_obj:
					new_job = Job(
						lead_id=new_lead_obj.id,
						_type=JobTypes.LEAD_CHECK,
					)
					new_job.save()
					
					
					if app_obj:
						with app_obj.app_context():
							socketio_obj.emit('leads_updated', {'leads': [new_lead_obj.to_dict()]}, to=f'user_{new_query.user_id}')
					
					try:
						check_lead_task(new_lead_obj.id)
					except Exception as e:
						logger.error(f'Error queuing lead check for lead {new_lead_obj.id}: {e}')
						new_lead_obj._finished(
							socketio_obj=socketio_obj,
							app_obj=app_obj,
							session=session
						)
						new_job._finished(
							socketio_obj=socketio_obj,
							app_obj=app_obj,
							session=session
						)
						session.commit()

		if collected_leads.lead_sources:
			for lead_source in collected_leads.lead_sources:
				new_source_obj = LeadSource.check_and_add(
					lead_source.url,
					new_query.user_id,
					new_query.id,
					checked=False,
					session=session
				)
				if new_source_obj and app_obj:
					if new_source_obj.query_id and new_source_obj.query_obj.auto_check:
						new_source_obj.checking = True
						session.commit()
						new_job = Job(
							source_id=new_source_obj.id,
							_type=JobTypes.SOURCE_CHECK,
						)
						session.add(new_job)
						session.commit()
						app_obj.config['high_priority_queue'].enqueue('worker.check_lead_source.check_lead_source_task', new_source_obj.id)

					if socketio_obj:
						with app_obj.app_context():
							socketio_obj.emit('sources_updated', {'sources': [new_source_obj.to_dict()]}, to=f'user_{new_query.user_id}')

		new_query.n_results_retrieved += 1
		session.commit()

		if socketio_obj:
			socketio_obj.emit('queries_updated', {'queries': [new_query.to_dict(example_leads=True, cost=True)]}, to=f'user_{new_query.user_id}')

	if new_query.total_cost_credits:
		new_query.total_cost_credits += total_tokens_used_usd * mult * 1000
	else:
		new_query.total_cost_credits = total_tokens_used_usd * mult * 1000
	if new_query.unique_cost_credits:
		new_query.unique_cost_credits += total_tokens_used_usd * mult * 1000
	else:
		new_query.unique_cost_credits = total_tokens_used_usd * mult * 1000

	user.move_credits(
		amount=mult * -1000 * total_tokens_used_usd,
		cost_usd=total_tokens_used_usd,
		trxn_type=CreditLedgerType.CHECK_QUERY,
		socketio_obj=socketio_obj,
		app_obj=app_obj,
		session=session
	)

	if new_query.budget and query_job_obj.total_cost_credits and query_job_obj.total_cost_credits > new_query.budget:
		new_query.over_budget = True

	session.commit()

	new_query.n_results_requested = new_query.n_results_retrieved
	session.commit()

	if socketio_obj:
		socketio_obj.emit('queries_updated', {'queries': [new_query.to_dict(example_leads=True, cost=True)]}, to=f'user_{new_query.user_id}')

	return True, ""




from app import db

def search_request_task(query_id):
	min_app = _make_min_app()
	if not min_app:
		logger.error("Failed to create app context")
		return

	with min_app.app_context():
		session = db.session

		new_query = session.query(Query).options(joinedload(Query.user)).get(query_id)
		if not new_query:
			logger.error(f"Query with id {query_id} not found")
			return

		job = get_current_job()

		query_job_obj = session.query(Job).filter_by(query_id=query_id).first()
		if query_job_obj:
			query_job_obj._started(job.id if job else None)
		else:
			new_job = Job(
				query_id=query_id,
				_type=JobTypes.QUERY_CHECK,
			)
			session.add(new_job)
			session.commit()
			new_job._started(job.id if job else None)
			query_job_obj = new_job

		if new_query.finished:
			return
		if new_query.hidden:
			new_query._finished(
				socketio_obj=worker_socketio,
				app_obj=min_app,
				session=session
			)
			return

		request_user = new_query.user
		previously_liked_leads = Lead.get_liked_leads(request_user.id, 5)

		previous_leads = [f'{lead.name} - {lead.description}' for lead in previously_liked_leads]
		previous_leads = '\n'.join(previous_leads) + '\n'
		previous_leads = previous_leads.strip()

		logger.info(f'Searching for leads for query: {new_query.user_query}')

		token_charge = min_app.config['PRICING_MULTIPLIERS']['query']

		request_user.move_credits(
			amount=token_charge * -1,
			cost_usd=0.01,
			trxn_type=CreditLedgerType.QUERY,
			socketio_obj=worker_socketio,
			app_obj=min_app,
			session=session
		)

		new_query.total_cost_credits += token_charge
		new_query.unique_cost_credits += token_charge
		session.commit()

		success, error = search_and_validate_leads(
			new_query.id, previous_leads, min_app, worker_socketio, query_job_obj, session
		)

		if error:
			new_query._finished(
				run_notes=f'Error // {error}',
				socketio_obj=worker_socketio,
				app_obj=min_app,
				session=session
			)
			worker_socketio.emit('queries_updated', {'queries': [new_query.to_dict(example_leads=True, cost=True)]}, to=f'user_{new_query.user_id}')
			return

		new_query._finished(
			socketio_obj=worker_socketio,
			app_obj=min_app,
			session=session
		)
		worker_socketio.emit('queries_updated', {'queries': [new_query.to_dict(example_leads=True, cost=True)]}, to=f'user_{new_query.user_id}')

	return
