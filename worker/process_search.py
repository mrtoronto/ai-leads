from app import worker_socketio, create_minimal_app
from app.models import LeadSource, Lead, Query, User, CreditLedgerType
from rq import get_current_job
from app.llm import search_and_validate_leads, rewrite_query
from flask_socketio import emit
from worker import _make_min_app

import logging

logger = logging.getLogger('BDB-2EB')

def search_request_task(query_id):
	job = get_current_job()
	min_app = _make_min_app()
	if not min_app:
		logger.error("Failed to create app context")
		return
	with min_app.app_context():
		request = Query.get_by_id(query_id)

		if not request:
			return

		if request.finished:
			return
		if request.hidden:
			request._finished()
			return

		request_user = request.user
		previously_liked_leads = Lead.get_liked_leads(request_user.id, 5)

		previous_leads = [f'{lead.name} - {lead.description}' for lead in previously_liked_leads]
		previous_leads = '\n'.join(previous_leads) + '\n'
		previous_leads = previous_leads.strip()

		if request:
			logger.info(f'Searching for leads for query: {request.user_query}')
			rephrased_query = rewrite_query(request.user_query, request.user, socketio_obj=worker_socketio)
			if rephrased_query:
				logger.info(f'Rephrased query: {rephrased_query.rewritten_query}')
				request.reformatted_query = rephrased_query.rewritten_query
				request.save()
			else:
				logger.error(f'Failed to rephrase query: {request.user_query}')
				request.reformatted_query = request.user_query
				request.save()


			worker_socketio.emit('requests_updated', {'requests': [request.to_dict()]}, to=f'user_{request.user_id}')

			with min_app.app_context():
				request.user.move_credits(
					min_app.config['PRICING_MULTIPLIERS']['query'] * -1,
					CreditLedgerType.QUERY,
					socketio_obj=worker_socketio,
					app_obj=min_app
				)

			success, error, tokens_used = search_and_validate_leads(
				request,
				previous_leads,
				app_obj=min_app,
				socketio_obj=worker_socketio
			)


			with min_app.app_context():
				if 'mini' in (request.user.model_preference or 'gpt-4o-mini'):
					mult = min_app.config['PRICING_MULTIPLIERS']['check_source_mini']
				else:
					mult = min_app.config['PRICING_MULTIPLIERS']['check_source']
				request.user.move_credits(
					mult * -1000 * tokens_used,
					CreditLedgerType.CHECK_QUERY,
					socketio_obj=worker_socketio,
					app_obj=min_app
				)

			if error:

				request._finished(f'Error // {error}')
				worker_socketio.emit('requests_updated', {'queries': [request.to_dict()]}, to=f'user_{request.user_id}')
				return

			request._finished()
			worker_socketio.emit('requests_updated', {'queries': [request.to_dict()]}, to=f'user_{request.user_id}')
		return
