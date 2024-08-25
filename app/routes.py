import traceback
import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, g
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import socketio, mail
from app.models import User, Lead, Query, LeadSource, Job, JobTypes, CreditLedger, Journey
from flask_socketio import emit
from app.models.credit_ledger import CreditLedgerType
from app.tasks import queue_check_lead_source_task, queue_check_lead_task, queue_search_request
import json
from flask import Blueprint, current_app
from app import db
import redis
import os
import stripe

bp = Blueprint('main', __name__, static_url_path='/static')

def read_txt_file(file_path):
	with open(file_path, 'r') as file:
		return file.read()

def dir_last_updated(folder):
	return str(max(os.path.getmtime(os.path.join(root_path, f))
				for root_path, dirs, files in os.walk(folder)
				for f in files))

@bp.context_processor
def inject_is_mobile():
	return {
		'is_mobile': getattr(g, 'is_mobile', False),
		'last_updated': dir_last_updated('app'),
		'FLASK_ENV': current_app.config['FLASK_ENV']
	}

import logging

logger = logging.getLogger('BDB-2EB')

@bp.route('/favicon.ico')
def favicon():
	return '', 204

@bp.route('/_ah/health')
def health_check():
	return 'OK', 200

@bp.route('/health/redis')
def redis_health():
	try:
		r = redis.from_url(current_app.config['REDIS_URL'])
		r.ping()
		return jsonify({"status": "healthy", "message": "Redis connection successful"}), 200
	except redis.ConnectionError:
		return jsonify({"status": "unhealthy", "message": "Redis connection failed"}), 500


from flask import jsonify, current_app
from sqlalchemy import text
from app import db

@bp.route('/health/db')
def db_health():
	try:
		# Execute a simple query
		with db.engine.connect() as connection:
			result = connection.execute(text("SELECT 1"))
			if result and result.scalar() == 1:
				return jsonify({"status": "healthy", "message": "Database connection successful"}), 200
			else:
				return jsonify({"status": "unhealthy", "message": "Unexpected database response"}), 500
	except Exception as e:
		return jsonify({"status": "unhealthy", "message": f"Database connection failed: {str(e)}"}), 500

@bp.route('/')
def index():
	if current_user.is_authenticated:
		lead_sources_checking = LeadSource.query.filter_by(user_id=current_user.id, checking=True, hidden=False).count()
		leads_checking = Lead.query.filter_by(user_id=current_user.id, checking=True, hidden=False).count()
		queries_running = Query.query.filter_by(user_id=current_user.id, finished=False, hidden=False).count()

		if lead_sources_checking > 0:
			flash(f'{lead_sources_checking} Lead Sources are being checked')

		if leads_checking > 0:
			flash(f'{leads_checking} Leads are being checked')

		if queries_running > 0:
			flash(f'{queries_running} Queries are running')

	return render_template('home_v3.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		email = request.form.get('email')
		password = request.form.get('password')
		print(f'Attempt to login with email: {email}')

		if not email or not email.strip() or not password or not password.strip():
			print('Email and password are required')
			flash('Email and password are required')
			return render_template('login.html', email=email)

		user = User.get_by_email(email)
		if not user:
			print('User not found')
			flash('User not found')
			return render_template('login.html', email=email)
		if user and user.password:
			if check_password_hash(user.password, password):
				print('User logged in successfully')
				flash('Welcome!')
				login_user(user)
			else:
				print('Invalid credentials')
				flash('Invalid credentials')
				return render_template('login.html', email=email)
			return redirect(url_for('main.index'))
		print('User not found')
		return render_template('login.html', email=email)
	return render_template('login.html', title='Login')

@bp.route('/register', methods=['GET', 'POST'])
def register():

	if request.method == 'POST':
		email = request.form.get('email')
		password = request.form.get('password')
		password2 = request.form.get('password2')

		if password != password2:
			flash('Passwords do not match')
			print('Passwords do not match')
			return render_template('register.html', email=email)

		if not email or not email.strip() or not password or not password.strip():
			flash('Email and password are required')
			print('Email and password are required')
			return render_template('register.html', email=email)

		# Check if user already exists
		email = email.lower()
		print(f'logging in {email}')
		existing_user = User.get_by_email(email)
		if existing_user:
			flash('Email already exists')
			print(f'Email already exists - {existing_user.email}')
			return render_template('register.html', email=email)

		hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
		new_user = User(email=email, password=hashed_password)
		new_user.save()

		login_user(new_user)

		# Send Welcome Email with Verification Link
		token = generate_confirmation_token(new_user.email)
		confirm_url = url_for('main.confirm_email', token=token, _external=True)
		send_email(new_user.email, 'Welcome to aiLeads!', 'welcome_email', name=new_user.username, confirm_url=confirm_url)

		# Redirect to setup preferences page
		return redirect(url_for('main.setup_preferences')) # New route after registration
	if current_user.is_authenticated:
		flash('You are already logged in!')
		return redirect(url_for('main.index'))
	return render_template('register.html', title='Register')

@bp.route('/setup_preferences')
@login_required
def setup_preferences():
	return render_template('setup_preferences.html')

@bp.route('/settings')
@login_required
def settings():
	return render_template('settings.html', title='Settings')

@bp.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('main.login'))



@bp.route('/submit_request', methods=['POST'])
@login_required
def submit_request():
	data = request.get_json() or {}
	query = data.get('query')
	if not query:
		return jsonify({"error": "Query is required"}), 400

	if current_user.credits < 1:
		socketio.emit('credit_error', {'message': 'Not enough credits to run a search.'}, to=f'user_{current_user.id}')
		return jsonify({"error": "You do not have enough credits to run this search."}), 400

	new_request = Query(
		user_id=current_user.id,
		user_query=query
	)
	new_request.save()

	queue_search_request(new_request.id)
	return jsonify({"message": "Search queued!", "guid": new_request.guid}), 200


@bp.route('/query/<guid>')
@login_required
def view_query(guid):
	query = Query.get_by_guid(guid)
	if not query:
		flash('Query not found.')
		return redirect(url_for('main.index'))
	elif query.user_id != current_user.id:
		flash('You are not authorized to view this query.')
		return redirect(url_for('main.index'))
	return render_template('view_query.html', query=query, title=f'Query: {query.user_query[:50] + "..." if len(query.user_query) > 50 else query.user_query}')

@bp.route('/source/<guid>')
@login_required
def view_source(guid):
	source = LeadSource.get_by_guid(guid)
	if not source:
		flash('Source not found.')
		return redirect(url_for('main.index'))
	elif source.user_id != current_user.id:
		flash('You are not authorized to view this source.')
		return redirect(url_for('main.index'))
	return render_template('view_source.html', source=source, title=f'Source: {source.name[:50] + "..." if len(source.name) > 50 else source.name}')

@bp.route('/lead/<guid>')
@login_required
def view_lead(guid):
	lead = Lead.get_by_guid(guid)
	if not lead:
		flash('Lead not found.')
		return redirect(url_for('main.index'))
	elif lead.user_id != current_user.id:
		flash('You are not authorized to view this lead.')
		return redirect(url_for('main.index'))
	return render_template('view_lead.html', lead=lead, title=f'Lead: {lead.name[:50] + "..." if len(lead.name) > 50 else lead.name}')


@bp.route('/faqs')
def faqs():
	return render_template('faqs.html', title='FAQs')


@bp.route('/admin')
@login_required
def admin_panel():
	if not current_user.is_admin:
		flash('You do not have permission to access the admin panel.')
		return redirect(url_for('main.index'))
	return render_template('admin_panel.html')

@bp.route('/admin/credit_ledger')
@login_required
def admin_credit_ledger():
	if not current_user.is_admin:
		flash('You do not have permission to access this page.')
		return redirect(url_for('main.index'))
	entries = CreditLedger.query.order_by(CreditLedger.created_at.desc()).all()
	return render_template('admin_credit_ledger.html', entries=entries)

@bp.route('/admin/users')
@login_required
def admin_users():
	if not current_user.is_admin:
		flash('You do not have permission to access this page.')
		return redirect(url_for('main.index'))
	users = User.query.all()
	return render_template('admin_users.html', users=users)

@bp.route('/admin/journeys')
@login_required
def admin_journeys():
	if not current_user.is_admin:
		flash('You do not have permission to access this page.')
		return redirect(url_for('main.index'))
	journeys = Journey.query.all()
	return render_template('admin_journeys.html', journeys=journeys)

@bp.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_user_settings(user_id):
	if not current_user.is_admin:
		flash('You do not have permission to access this page.')
		return redirect(url_for('main.index'))

	user = User.query.get_or_404(user_id)

	if request.method == 'POST':
		user.email = request.form['email']
		user.credits = int(request.form['credits'])
		user.is_admin = 'is_admin' in request.form
		db.session.commit()
		flash('User settings updated successfully.')
		return redirect(url_for('main.admin_users'))

	return render_template('admin_user_settings.html', user=user)


from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

def generate_confirmation_token(email):
	serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
	return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
	serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
	try:
		email = serializer.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'], max_age=expiration)
	except SignatureExpired:
		return False
	return email

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
	try:
		email = confirm_token(token)
	except:
		flash('The password reset link is invalid or has expired.', 'danger')
		return redirect(url_for('main.password_reset_request'))

	if request.method == 'POST':
		password = request.form['password']
		user = User.get_by_email(email)
		if user:
			user.password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
			user.save()
			flash('Your password has been updated!', 'success')
			return redirect(url_for('main.login'))
		else:
			flash('An error occurred, please try again later.', 'danger')
			return render_template('reset_password.html', token=token)
	return render_template('reset_password.html', token=token)

@bp.route('/send_verification_email', methods=['GET', 'POST'])
@login_required
def send_verification_email():
	if current_user.email_verified:
		return jsonify(message='Your email address has already been verified.'), 200
	else:
		token = generate_confirmation_token(current_user.email)
		confirm_url = url_for('main.confirm_email', token=token, _external=True)
		send_email(current_user.email, 'Confirm Your Email', 'confirm_email', confirm_url=confirm_url)
		return jsonify(message='Verification email sent successfully'), 200

@bp.route('/password_reset_request', methods=['GET', 'POST'])
def password_reset_request():
	if request.method == 'POST':
		email = request.form.get('email') or request.json.get('email')
		user = User.get_by_email(email)
		if user:
			token = generate_confirmation_token(user.email)
			reset_url = url_for('main.reset_password', token=token, _external=True)
			send_email(user.email, 'Reset Your Password', 'reset_password_email', reset_url=reset_url)
			return jsonify(message='Password reset email sent successfully'), 200
		else:
			flash('This email is not registered in our system.', 'danger')
			return render_template('password_reset_request.html')
	return render_template('password_reset_request.html')

@bp.route('/confirm_email/<token>')
def confirm_email(token):
	try:
		email = confirm_token(token)
	except:
		flash('The confirmation link is invalid or has expired.', 'danger')
		return redirect(url_for('main.index'))

	user = User.get_by_email(email)
	if user and not user.email_verified:
		user.email_verified = True
		user.save()
		flash('Your email address has been confirmed.', 'success')
	else:
		flash('This email address is already confirmed.', 'info')
	return redirect(url_for('main.index'))




def send_email(to, subject, template, **kwargs):
	msg = Message(
		subject,
		recipients=[to],
		html=render_template('email/' + template + '.html', **kwargs),
		sender=current_app.config['MAIL_DEFAULT_SENDER'],
		reply_to=current_app.config['MAIL_DEFAULT_SENDER']
	)
	try:
		mail.send(msg)
		logger.info(f'Email sent to {to}')
	except Exception as e:
		logger.error(f'Failed to send email to {to}: {e}')

		# Log stack trace
		import traceback
		logger.error(traceback.format_exc())



@bp.app_errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

@bp.app_errorhandler(500)
def internal_server_error(e):
	logger.error(
		f'Internal Server Error (error page displayed): {e}\n'
		f'File: {e.__traceback__.tb_frame.f_code.co_filename}\n'
		f'Line: {e.__traceback__.tb_lineno}\n'
		f'Stack Trace: {traceback.format_exc()}\n'
		f'Request Path: {request.path}\n'
		f'Method: {request.method}\n'
		f'User Agent: {request.user_agent}\n'
		f'IP Address: {request.remote_addr}'
	)
	return render_template('500.html', error=str(e)), 500

@bp.app_errorhandler(Exception)
def handle_exception(e):
	logger.error(
		f'An error occurred (error page displayed): {e}\n'
		f'File: {e.__traceback__.tb_frame.f_code.co_filename}\n'
		f'Line: {e.__traceback__.tb_lineno}\n'
		f'Stack Trace: {traceback.format_exc()}\n'
		f'Request Path: {request.path}\n'
		f'Method: {request.method}\n'
		f'User Agent: {request.user_agent}\n'
		f'IP Address: {request.remote_addr}'
	)
	return render_template('500.html', error=str(e)), 500


@bp.route('/contact', methods=['GET', 'POST'])
def contact():
	if request.method == 'POST':
		name = request.form['name']
		email = request.form['email']
		subject = request.form['subject']
		message = request.form['message']

		send_email(
			current_app.config['MAIL_DEFAULT_SENDER'],
			f"New Contact Form Submission: {subject}",
			'contact_email',
			name=name,
			email=email,
			message=message
		)

		flash('Your message has been sent successfully.', 'success')
		return redirect(url_for('main.contact'))

	return render_template('contact.html', title='Contact Us')



@bp.route('/privacy_policy')
def privacy_policy():
	privacy_policy_text = read_txt_file('app/static/privacy_policy.txt')
	return render_template('privacy_policy.html', title='Privacy Policy', content=privacy_policy_text)

@bp.route('/terms_of_service')
def terms_of_service():
	tos_text = read_txt_file('app/static/terms_of_service.txt')
	return render_template('tos.html', title='Terms of Service', content=tos_text)

@bp.route('/store')
def store():
	return render_template('store.html', title='Store')


@bp.route('/send-email')
def send_email_route():
	send_email(
		to='matt.toronto97@gmail.com',
		subject='Welcome to aiLeads',
		template='welcome_email',
		name="Recipient Name",  # Pass any required variables as keyword arguments
		current_year=2024
	)
	return 'Email sent successfully!'


@bp.route('/save_preferences', methods=['POST'])
@login_required
def save_preferences():
	if current_user.is_authenticated:
		data = request.get_json()
		if data:
			industry = data.get('industry')
			org_size = data.get('orgSize')
			description = data.get('description')

			current_user.industry = industry
			current_user.preferred_org_size = org_size
			current_user.user_description = description
			db.session.commit()

			return jsonify({"status": "success"}), 200
	return jsonify({"status": "error"}), 400


@bp.route('/leads')
@login_required
def leads():
	return render_template('view_leads.html', title="Your Leads")


@bp.route('/jobs')
@login_required
def jobs():
	return render_template('view_jobs.html', title="In-Progress")


@bp.route('/queries')
@login_required
def queries():
	return render_template('view_queries.html', title="Your Queries")



@bp.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
	try:
		data = request.json or {}
		credit_amount = data.get('creditAmount')
		price = data.get('price')

		if not credit_amount or not price:
			return jsonify(error='Credit amount and price are required'), 400

		session = stripe.checkout.Session.create(
			payment_method_types=['card'],
			line_items=[{
				'price_data': {
					'currency': 'usd',
					'product_data': {
						'name': f'{credit_amount} credits',
					},
					'unit_amount': price * 100,
				},
				'quantity': 1,
			}],
			mode='payment',
			success_url=url_for('main.payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
			cancel_url=url_for('main.payment_cancelled', _external=True),
		)

		return jsonify(id=session.id)
	except Exception as e:
		logger.error(f'Error creating checkout session: {e}')
		return jsonify(error=str(e)), 403

@bp.route('/payment/success')
def payment_success():
	session_id = request.args.get('session_id')
	if session_id:
		checkout_session = stripe.checkout.Session.retrieve(session_id)
		determined_amount_credits = checkout_session.amount_total * 10

		if determined_amount_credits == 1000:
			determined_amount_credits = determined_amount_credits * 2
			current_user.claimed_signup_bonus = True
			db.session.commit()

		current_user.move_credits(
			amount=determined_amount_credits,
			trxn_type=CreditLedgerType.PAID,
			app_obj=current_app,
			socketio_obj=socketio
		)
		db.session.commit()

		flash(f'Payment successful! <b>{determined_amount_credits}</b> credits have been added to your account.', 'success')
	else:
		flash('Payment could not be processed. Please try again.', 'danger')

	return redirect(url_for('main.store'))

@bp.route('/payment/cancelled')
def payment_cancelled():
	flash('Payment cancelled. No credits were added to your account.', 'warning')
	return redirect(url_for('main.store'))
