from . import socketio
from flask_login import login_required, current_user
from .models import LeadSource, Lead, Query, User
from flask_socketio import join_room, emit
import logging

logger = logging.getLogger('BDB-2EB')
@socketio.on('connect')
def on_connect():
	if current_user.is_authenticated:
		join_room(f"user_{current_user.id}")

@socketio.on('disconnect')
def on_disconnect():
	pass

from .tasks import (
	queue_check_lead_source_task,
	queue_check_lead_task,
	queue_retrain_models_task,
	queue_update_qualities_task
)

@socketio.on('get_initial_data')
def handle_get_initial_data():
	if current_user.is_authenticated:
		initial_data = current_user.get_initial_data()
		socketio.emit('initial_data', initial_data, to=f"user_{current_user.id}")

@socketio.on('check_lead_source')
@login_required
def handle_check_lead_source(data):

	lead_source_id = data['lead_source_id']
	lead_source = LeadSource.get_by_id(lead_source_id)


	if lead_source:
		if current_user.credits < 1:
			socketio.emit('credit_error', {'message': 'Not enough credits to check a source.', 'source': lead_source.to_dict()}, to=f'user_{lead_source.user_id}')
			return
		lead_source.checking = True
		lead_source.save()
		queue_check_lead_source_task(lead_source_id)
		socketio.emit('lead_source_check_started', {'source': lead_source.to_dict()}, to=f"user_{lead_source.user_id}")
	else:
		socketio.emit('error', {'message': 'Lead source not found or already checked'}, to=f"user_{lead_source.user_id}")

@socketio.on('liked_lead')
@login_required
def handle_contacted_lead(data):
	lead_id = data['lead_id']
	lead = Lead().get_by_id(lead_id)
	if lead:
		lead.liked = not lead.liked if lead.liked != None else True
		lead.save()

		socketio.emit('lead_liked', {'lead': lead.to_dict()}, to=f"user_{lead.user_id}")

@socketio.on('check_lead')
@login_required
def handle_check_lead(data):
	lead_id = data['lead_id']
	lead = Lead().get_by_id(lead_id)

	if lead:
		if lead.checking:
			socketio.emit('error', {'message': 'Lead is already being checked'}, to=current_user.get_id())
			return

		if current_user.credits < 1:
			socketio.emit('credit_error', {'message': 'Not enough credits to check a lead.', 'lead': lead.to_dict()}, to=f"user_{lead.user_id}")
			return

		lead.checking = True
		lead.save()

		queue_check_lead_task(lead_id)
		socketio.emit('lead_check_started', {'lead': lead.to_dict()}, to=f"user_{lead.user_id}")
	else:
		socketio.emit('error', {'message': 'Lead not found'}, to=current_user.get_id())

@socketio.on('hide_request')
@login_required
def handle_hide_request(data):
	query_id = data['query_id']
	request = Query.get_by_id(query_id)
	if request:
		hidden_source_ids, hidden_lead_ids = request._hide()

		socketio.emit('requests_hidden', {'query_ids': [query_id]}, to=f"user_{request.user_id}")
		socketio.emit('leads_hidden', {'lead_ids': hidden_lead_ids}, to=f"user_{request.user_id}")
		socketio.emit('sources_hidden', {'source_ids': hidden_source_ids}, to=f"user_{request.user_id}")
	else:
		socketio.emit('error', {'message': 'Query not found'}, to=f"user_{current_user.id}")

@socketio.on('hide_source')
@login_required
def handle_hide_source(data):
	source_id = data['source_id']
	lead_source = LeadSource.get_by_id(source_id)
	if lead_source:
		print(f'Hiding source {source_id}')
		hidden_lead_ids = lead_source._hide()

		socketio.emit('sources_hidden', {'source_ids': [source_id]}, to=f"user_{lead_source.user_id}")
		socketio.emit('leads_hidden', {'lead_ids': hidden_lead_ids}, to=f"user_{lead_source.user_id}")
	else:
		socketio.emit('error', {'message': 'Lead source not found'}, to=f"user_{current_user.id}")

@socketio.on('hide_lead')
@login_required
def handle_hide_lead(data):
	lead_id = data['lead_id']
	print(f'Hiding lead {lead_id}')
	lead = Lead().get_by_id(lead_id)
	if lead:
		lead.hidden = True
		lead.save()
		socketio.emit('leads_hidden', {'lead_ids': [lead_id]}, to=f"user_{lead.user_id}")
	else:
		socketio.emit('error', {'message': 'Lead not found'}, to=f"user_{current_user.id}")


@socketio.on('create_lead_source')
@login_required
def handle_create_lead_source(data):
	url = data['url']
	new_lead_source = LeadSource.check_and_add(
		url=url,
		user_id=current_user.id,
		query_id=None
	)
	if new_lead_source:
		socketio.emit('new_lead_source', {'source': new_lead_source.to_dict()}, to=f'user_{new_lead_source.user_id}')

@socketio.on('create_lead')
@login_required
def handle_create_lead(data):
	url = data['url']
	new_lead = Lead.check_and_add(
		url=url,
		user_id=current_user.id,
		query_id=None,
		source_id=None
	)
	if new_lead:
		socketio.emit('new_lead', {'lead': new_lead.to_dict()}, to=f'user_{new_lead.user_id}')


@socketio.on('update_email')
@login_required
def handle_update_email(data):
	if current_user and current_user.is_authenticated:
		user = User.get_by_id(current_user.id)
		logger.info(f"Updating email wit h{data}")
		if user:
			input_email = data.get('email', '').lower().strip()
			if user.email != input_email:
				if User.get_by_email(input_email):
					emit('email_updated', {'success': False, 'message': 'This email is already in use.'}, to=f"user_{current_user.id}")
					return
				logger.info(f"Updating email for user {current_user.id}")
				user.email_verified = False
				user.email = input_email
			user.save()
			socketio.emit('email_updated', {'success': True, 'email': user.email}, to=f"user_{user.id}")

@socketio.on('update_user_settings')
@login_required
def handle_update_user_settings(data):
	if current_user and current_user.is_authenticated:
		user = User.get_by_id(current_user.id)
		if user:
			user.user_description = data.get('user_description', user.user_description)
			user.search_model_preference = data.get('search_model_preference', user.search_model_preference)
			user.source_collection_model_preference = data.get('source_collection_model_preference', user.source_collection_model_preference)
			user.lead_validation_model_preference = data.get('lead_validation_model_preference', user.lead_validation_model_preference)
			user.industry = data.get('industry', user.industry)
			user.preferred_org_size = data.get('preferred_org_size', user.preferred_org_size)

			db.session.commit()
			emit('update_user_settings_response', {'success': True}, to=f"user_{user.id}")
	else:
		emit('update_user_settings_response', {'success': False}, to=f"user_{current_user.id}")


@socketio.on('retrain_model')
def handle_retrain_model():
	user_id = current_user.id
	print(f'Retraining model for {user_id}')
	queue_retrain_models_task(user_id)
	queue_update_qualities_task(user_id)


@socketio.on('get_query_data')
@login_required
def handle_get_query_data(data):
    query_id = data['query_id']
    query = Query.get_by_id(query_id)
    if query:
        query_data = {
        	'query': query.to_dict(),
            'leads': [lead.to_dict() for lead in query.leads if not lead.hidden],
            'sources': [source.to_dict() for source in query.sources if not source.hidden]
        }
        socketio.emit('query_data', query_data, to=f"user_{current_user.id}")
    else:
        socketio.emit('error', {'message': 'Query not found'}, to=f"user_{current_user.id}")

@socketio.on('get_source_data')
@login_required
def handle_get_source_data(data):
    source_id = data['source_id']
    source = LeadSource.get_by_id(source_id)
    if source:
        source_data = {
        	'source': source.to_dict(),
            'leads': [lead.to_dict() for lead in source.leads if not lead.hidden]
        }
        socketio.emit('source_data', source_data, to=f"user_{current_user.id}")
    else:
        socketio.emit('error', {'message': 'Source not found'}, to=f"user_{current_user.id}")

@socketio.on('get_lead_data')
@login_required
def handle_get_lead_data(data):
    lead_id = data['lead_id']
    lead = Lead.get_by_id(lead_id)
    if lead:
        lead_data = {
            'lead': lead.to_dict()
        }
        socketio.emit('lead_data', lead_data, to=f"user_{current_user.id}")
    else:
        socketio.emit('error', {'message': 'Lead not found'}, to=f"user_{current_user.id}")


@socketio.on('check_email_availability')
@login_required
def handle_check_email_availability(data):
    email = data['email']

    # Check if the email is valid
    import re
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    is_valid = re.match(email_regex, email) is not None

    is_available = is_valid and User.get_by_email(email) is None
    emit('email_check_response', {'available': is_available, 'valid': is_valid}, to=f"user_{current_user.id}")
