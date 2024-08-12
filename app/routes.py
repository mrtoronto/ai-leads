import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import socketio
from app.models import User, Lead, Query, LeadSource, Job, JobTypes, CreditLedger
from flask_socketio import emit
from app.tasks import queue_check_lead_source_task, queue_check_lead_task, queue_search_request
import json
from flask import Blueprint, current_app
from app import db
import redis

bp = Blueprint('main', __name__)

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
			return render_template('login.html')

		user = User.get_by_email(email)
		if not user:
			print('User not found')
			flash('User not found')
			return redirect(url_for('main.login'))
		if user and user.password:
			if check_password_hash(user.password, password):
				print('User logged in successfully')
				flash('Welcome!')
				login_user(user)
			else:
				print('Invalid credentials')
				flash('Invalid credentials')
				return redirect(url_for('main.login'))
			return redirect(url_for('main.index'))
		print('User not found')
		return redirect(url_for('main.login'))
	return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		username = request.form.get('username')
		email = request.form.get('email')
		password = request.form.get('password')
		if username is None or email is None or password is None:
			flash('All fields are required')
			print('All fields are required')
			return render_template('register.html')

		# Check if user already exists
		print(f'logging in {username}')
		existing_user = User.get_by_username(username)
		if existing_user:
			flash('Username already exists')
			print(f'Username already exists - {existing_user.username}')
			return render_template('register.html')

		hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
		new_user = User(email=email, username=username, password=hashed_password)
		new_user.save()

		login_user(new_user)

		return redirect(url_for('main.index'))
	return render_template('register.html')

@bp.route('/settings')
@login_required
def settings():
	return render_template('settings.html')

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
	return jsonify({"message": "Search queued!"}), 200


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
	return render_template('view_query.html', query=query)

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
	return render_template('view_source.html', source=source)

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
	return render_template('view_lead.html', lead=lead)


@bp.route('/faqs')
def faqs():
	return render_template('faqs.html')


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

@bp.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_user_settings(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.credits = int(request.form['credits'])
        user.is_admin = 'is_admin' in request.form
        db.session.commit()
        flash('User settings updated successfully.')
        return redirect(url_for('main.admin_users'))

    return render_template('admin_user_settings.html', user=user)
