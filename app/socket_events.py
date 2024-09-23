import re
from app import socketio, db
from datetime import datetime
import pytz
from flask import current_app
from flask_login import login_required, current_user
from app.models import LeadSource, Lead, Query, User, Journey, Chat, Message
from flask_socketio import join_room, emit
import logging
import time
from app.llm._rewrite import rewrite_query
from functools import wraps
from app.routes import send_email

logger = logging.getLogger('BDB-2EB')
@socketio.on('connect')
def on_connect():
	if current_user.is_authenticated:
		join_room(f"user_{current_user.id}")

@socketio.on('disconnect')
def on_disconnect():
	pass

def time_socket_event(func):
	@wraps(func)
	def wrapped(*args, **kwargs):
		start_time = time.time()
		result = func(*args, **kwargs)  # Call the original function
		elapsed_time = time.time() - start_time
		event_name = func.__name__
		logger.info(f"Socket event '{event_name}' execution time: {elapsed_time:.4f} seconds")  # Use your logger
		return result
	return wrapped


from .tasks import (
	queue_check_lead_source_task,
	queue_check_lead_task,
	# queue_retrain_models_task,
	# queue_update_qualities_task
)

@socketio.on('get_initial_data')
def handle_get_initial_data(data):
	if current_user.is_authenticated:
		initial_data = current_user.get_initial_data(data)
		socketio.emit('initial_data', initial_data, to=f"user_{current_user.id}")

@socketio.on('check_lead_source')
@time_socket_event
def handle_check_lead_source(data):
	if not current_user.is_authenticated:
		return
	lead_source_id = data['lead_source_id']
	lead_source = LeadSource.get_by_id(lead_source_id)


	if lead_source:
		if current_user.credits < 1:
			socketio.emit('credit_error', {'message': 'Not enough credits to check a source.', 'source': lead_source.to_dict()}, to=f'user_{lead_source.user_id}')
			return
		lead_source.checking = True
		lead_source.save()
		queue_check_lead_source_task(lead_source_id)
		socketio.emit('sources_updated', {'sources': [lead_source.to_dict()]}, to=f"user_{lead_source.user_id}")
	else:
		socketio.emit('source_check_update_error', {'source_id': lead_source_id, 'message': 'Lead source not found or already checked'}, to=f"user_{lead_source.user_id}")

@socketio.on('liked_lead')
@time_socket_event
def handle_contacted_lead(data):
	if not current_user.is_authenticated:
		return
	lead_id = data['lead_id']
	lead = Lead().get_by_id(lead_id)
	if lead:
		lead.liked = not lead.liked if lead.liked != None else True
		lead.save()

		socketio.emit('leads_updated', {'leads': [lead.to_dict()]}, to=f"user_{lead.user_id}")

@socketio.on('check_lead')
@time_socket_event
def handle_check_lead(data):
	if not current_user.is_authenticated:
		return
	lead_id = data['lead_id']
	lead = Lead().get_by_id(lead_id)

	if lead:
		if current_user.credits < 1:
			socketio.emit('credit_error', {'message': 'Not enough credits to check a lead.', 'lead': lead.to_dict()}, to=f"user_{lead.user_id}")
			return

		lead.checking = True
		lead.save()

		queue_check_lead_task(lead_id)
		socketio.emit('leads_updated', {'leads': [lead.to_dict()]}, to=f"user_{lead.user_id}")
	else:
		socketio.emit('error', {'message': 'Lead not found'}, to=f"user_{current_user.id}")

@socketio.on('hide_request')
@time_socket_event
def handle_hide_request(data):
	if not current_user.is_authenticated:
		return
	query_id = data['query_id']
	request = Query.get_by_id(query_id)
	if request:
		request._hide(app_obj=current_app, socketio_obj=socketio)
	else:
		socketio.emit('error', {'message': 'Query not found'}, to=f"user_{current_user.id}")

@socketio.on('unhide_request')
@time_socket_event
def handle_unhide_request(data):
	if not current_user.is_authenticated:
		return
	query_id = data['query_id']
	request = Query.get_by_id(query_id)
	if request:
		request._unhide(app_obj=current_app, socketio_obj=socketio)
	else:
		socketio.emit('error', {'message': 'Query not found'}, to=f"user_{current_user.id}")

@socketio.on('hide_source')
@time_socket_event
def handle_hide_source(data):
	if not current_user.is_authenticated:
		return
	source_id = data['source_id']
	lead_source = LeadSource.get_by_id(source_id)
	if lead_source:
		print(f'Hiding source {source_id}')
		lead_source._hide(app_obj=current_app, socketio_obj=socketio)
	else:
		socketio.emit('error', {'message': 'Lead source not found'}, to=f"user_{current_user.id}")

@socketio.on('hide_lead')
@time_socket_event
def handle_hide_lead(data):
	if not current_user.is_authenticated:
		return
	lead_id = data['lead_id']
	print(f'Hiding lead {lead_id}')
	lead = Lead().get_by_id(lead_id)
	if lead:
		lead._hide(app_obj=current_app, socketio_obj=socketio)
	else:
		socketio.emit('error', {'message': 'Lead not found'}, to=f"user_{current_user.id}")

@socketio.on('unhide_lead')
@time_socket_event
def handle_unhide_lead(data):
	if not current_user.is_authenticated:
		return
	lead_id = data['lead_id']
	lead = Lead().get_by_id(lead_id)
	if lead:
		lead._unhide(app_obj=current_app, socketio_obj=socketio)
		lead.save()
		socketio.emit('leads_updated', {'leads': [lead.to_dict()]}, to=f"user_{lead.user_id}")

@socketio.on('unhide_source')
@time_socket_event
def handle_unhide_source(data):
	if not current_user.is_authenticated:
		return
	source_id = data['source_id']
	lead_source = LeadSource.get_by_id(source_id)
	if lead_source:
		lead_source._unhide(app_obj=current_app, socketio_obj=socketio)

		socketio.emit('sources_updated', {'sources': [lead_source.to_dict()]}, to=f"user_{lead_source.user_id}")


@socketio.on('create_lead_source')
@time_socket_event
def handle_create_lead_source(data):
	if not current_user.is_authenticated:
		return
	url = data['url']
	new_lead_source = LeadSource.check_and_add(
		url=url,
		user_id=current_user.id,
		query_id=None
	)
	if new_lead_source:
		socketio.emit('sources_updated', {'sources': [new_lead_source.to_dict()]}, to=f'user_{new_lead_source.user_id}')

@socketio.on('create_lead')
@time_socket_event
def handle_create_lead(data):
	if not current_user.is_authenticated:
		return
	url = data['url']
	new_lead = Lead.check_and_add(
		url=url,
		user_id=current_user.id,
		query_id=None,
		source_id=None
	)
	if new_lead:
		socketio.emit('leads_updated', {'leads': [new_lead.to_dict()]}, to=f'user_{new_lead.user_id}')


@socketio.on('update_email')
@time_socket_event
def handle_update_email(data):
	if not current_user.is_authenticated:
		return
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
@time_socket_event
def handle_update_user_settings(data):
	if not current_user.is_authenticated:
		return
	if current_user and current_user.is_authenticated:
		user = User.get_by_id(current_user.id)
		if user:
			user.user_description = data.get('user_description', user.user_description)
			user.industry = data.get('industry', user.industry)
			user.model_preference = data.get('model_preference', user.model_preference)

			db.session.commit()
			emit('update_user_settings_response', {'success': True}, to=f"user_{user.id}")
	else:
		emit('update_user_settings_response', {'success': False}, to=f"user_{current_user.id}")

# @socketio.on('retrain_model')
# @time_socket_event
# def handle_retrain_model():
# 	if not current_user.is_authenticated:
# 		return

# 	user_id = current_user.id
# 	print(f'Retraining model for {user_id}')
# 	queue_retrain_models_task(user_id)
# 	queue_update_qualities_task(user_id)


@socketio.on('get_query_data')
@time_socket_event
def handle_get_query_data(data):
	if not current_user.is_authenticated:
		return
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
@time_socket_event
def handle_get_source_data(data):
	if not current_user.is_authenticated:
		return
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
@time_socket_event
def handle_get_lead_data(data):
	if not current_user.is_authenticated:
		return
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
def handle_check_email_availability(data):
	if not current_user.is_authenticated:
		return
	email = data['email']
	email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
	is_valid = re.match(email_regex, email) is not None

	is_available = is_valid and User.get_by_email(email) is None
	emit('email_check_response', {'available': is_available, 'valid': is_valid}, to=f"user_{current_user.id}")


@socketio.on('rewrite_query')
@login_required
def handle_rewrite_query(data):
		user = current_user
		query_text = data['query']
		example_leads = data['exampleLeads']
		location = data.get('location', None)


		query_data = {
				'user_query': query_text,
				'user': user,
				'example_leads': example_leads,
				'location': location
		}

		new_query = rewrite_query(query_data, socketio_obj=socketio, app_obj=current_app)

		socketio.emit('new_rewritten_query', {'new_query': new_query}, to=f"user_{user.id}")

@socketio.on('get_all_journeys')
@time_socket_event
def handle_get_all_journeys(data):
		if not current_user.is_authenticated or not current_user.is_admin:
				return

		logged_in_only = data.get('logged_in_only', False)

		query = Journey.query.order_by(Journey.created_at.desc())

		if logged_in_only:
				query = query.filter(Journey.user_id.isnot(None))

		journeys = query.all()
		journey_data = [journey.to_dict() for journey in journeys]
		socketio.emit('all_journeys_response', {'status': 'success', 'records': journey_data}, to=f"user_{current_user.id}")

@socketio.on('start_chat')
@login_required
def handle_start_chat():
		new_chat = Chat(user_id=current_user.id)
		db.session.add(new_chat)
		db.session.commit()
		socketio.emit('chat_started', {'chat_id': new_chat.id}, to=f"user_{current_user.id}")
		socketio.emit('new_chat_for_admin', new_chat.to_dict(), room='admin_room')

@socketio.on('send_message')
@login_required
def handle_send_message(data):
		chat_id = data['chat_id']
		content = data['message']
		is_admin = data.get('is_admin', False)
		chat = Chat.query.get(chat_id)
		### Skips initial bot messages
		send_message_back = False
		if chat.resolved:
			chat.resolved = False
			db.session.commit()

			send_email(
				"matt@ai-leads.xyz", 'New Chat', 'new_chat'
			)

		### If admin has only sent 1 message in chat, respond to user
		if chat.messages.count() == 1 and chat.messages[0].is_admin:
			send_message_back = True

		new_message = Message(chat_id=chat_id, user_id=current_user.id, content=content, is_admin=is_admin)
		db.session.add(new_message)
		db.session.commit()
		socketio.emit('message_received', {'chat_id': chat_id, 'message': new_message.to_dict()}, to=f"user_{current_user.id}")
		socketio.emit('message_received', {'chat_id': chat_id, 'message': new_message.to_dict()}, to="admin_room")

		if send_message_back and not is_admin:
			pst_time = datetime.now(pytz.timezone('US/Pacific'))
			current_hour = pst_time.hour
			if 23 <= current_hour or current_hour < 6:
				new_content = "The admins are (probably) asleep and will be back to you in the morning."
			else:
				new_content = "The admins have been contacted and will be with you shortly."
			new_message_back = Message(chat_id=chat_id, user_id=current_user.id, content=new_content, is_admin=is_admin)
			db.session.add(new_message_back)
			db.session.commit()
			socketio.emit('message_received', {'chat_id': chat_id, 'message': new_message_back.to_dict()}, to=f"user_{current_user.id}")
			socketio.emit('message_received', {'chat_id': chat_id, 'message': new_message_back.to_dict()}, to="admin_room")

@socketio.on('send_admin_message')
@login_required
def handle_send_admin_message(data):
		if not current_user.is_admin:
			return
		chat_id = data['chat_id']
		content = data['message']
		chat = Chat.query.get(chat_id)
		if chat.resolved:
			chat.resolved = False
			db.session.commit()

		### If its been > 1 hour since the last message in the chat,
		### send an email to the user
		last_message = chat.messages[-1]
		time_diff = datetime.now(pytz.utc) - last_message.created_at
		if time_diff.total_seconds() > 3600:
			send_email(
				chat.user.email, 'New Support Chat Response', 'new_chat_response'
			)

		new_message = Message(chat_id=chat_id, user_id=current_user.id, content=content, is_admin=True)
		db.session.add(new_message)
		db.session.commit()
		socketio.emit('message_received', {'chat_id': chat_id, 'message': new_message.to_dict()}, to="admin_room")
		socketio.emit('message_received', {'chat_id': chat_id, 'message': new_message.to_dict()}, to=f"user_{chat.user_id}")

@socketio.on('get_chat_messages')
@login_required
def handle_get_chat_messages(data):
		chat_id = data['chat_id']
		chat = Chat.query.get(chat_id)
		if chat and (chat.user_id == current_user.id or current_user.is_admin):
				messages = [message.to_dict() for message in chat.messages]
				socketio.emit('chat_messages', {'chat_id': chat_id, 'messages': messages}, to=f"user_{current_user.id}")

@socketio.on('check_unresolved_chat')
@login_required
def handle_check_unresolved_chat():
		unresolved_chat = Chat.query.filter_by(user_id=current_user.id, resolved=False).first()
		if unresolved_chat:
				socketio.emit('unresolved_chat', {'chat_id': unresolved_chat.id}, to=f"user_{current_user.id}")

@socketio.on('get_unresolved_chats')
@login_required
def handle_get_unresolved_chats():
		if current_user.is_admin:
				unresolved_chats = Chat.query.filter_by(resolved=False).all()
				chat_data = [chat.to_dict() for chat in unresolved_chats]
				socketio.emit('unresolved_chats', {'chats': chat_data}, to=f'user_{current_user.id}')

@socketio.on('join_admin_room')
@login_required
def handle_join_admin_room():
		if current_user.is_admin:
				join_room('admin_room')
				# Optionally send existing unresolved chats upon joining
				unresolved_chats = Chat.query.filter_by(resolved=False).all()
				chat_data = [chat.to_dict() for chat in unresolved_chats]
				emit('unresolved_chats', {'chats': chat_data}, room='admin_room')

@socketio.on('resolve_chat')
@login_required
def handle_resolve_chat(data):
		if not current_user.is_admin:
				return
		chat_id = data.get('chat_id')
		chat = Chat.query.get(chat_id)
		if chat:
				chat.resolved = True
				db.session.commit()
				user_room = f"user_{chat.user_id}"
				admin_room = 'admin_room'
				
				# Notify the user and all admins that the chat has been resolved
				emit('chat_resolved', {'chat_id': chat_id}, room=user_room)
				emit('chat_resolved', {'chat_id': chat_id}, room=admin_room)