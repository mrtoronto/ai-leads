# import time
# from app import worker_socketio, create_minimal_app, db
# import random
# import fasttext
# import os
# from sklearn.model_selection import train_test_split
# import numpy as np
# from datetime import datetime
# import pytz

# from app.utils import upload_blob, download_blob, download_blob_if_exists

# from app.models.lead import Lead
# from app.models.lead_source import LeadSource
# from app.models.user_models import UserModels, ModelTypes
# from app.models.query import Query
# from app.models.user import User
# from worker import _make_min_app

# import logging

# logger = logging.getLogger('BDB-2EB')

# def train_and_evaluate(train_file, test_file, params):
# 	try:
# 		model = fasttext.train_supervised(train_file, verbose=0, **params)
# 		result = model.test(test_file)
# 		return result[1]  # f1-score
# 	except Exception as e:
# 		return 0

# def get_random_hyperparameters():
# 	return {
# 		'lr': 10 ** random.uniform(-3, 0),  # log uniform between 0.001 and 1.0
# 		'epoch': random.randint(5, 50),
# 		'wordNgrams': random.randint(1, 5),
# 		'bucket': random.choice([100000, 200000, 500000, 1000000, 2000000]),
# 		'dim': random.choice([10, 20, 50, 100, 200]),
# 		'loss': random.choice(['ns', 'hs', 'softmax']),
# 		't': random.uniform(0.0001, 0.5),
# 		'minn': random.randint(0, 3),
# 		'maxn': random.randint(3, 6),
# 	}

# def random_search(data_file, n_iter=50):
# 	with open(data_file, 'r') as f:
# 		data = f.readlines()

# 	train_data, test_data = train_test_split(data, test_size=0.2, random_state=42)

# 	with open('temp_train.txt', 'w') as f:
# 		f.writelines(train_data)
# 	with open('temp_test.txt', 'w') as f:
# 		f.writelines(test_data)

# 	best_score = 0
# 	best_params = None

# 	for _ in range(n_iter):
# 		params = get_random_hyperparameters()
# 		score = train_and_evaluate('temp_train.txt', 'temp_test.txt', params)

# 		if score > best_score:
# 			best_score = score
# 			best_params = params

# 	return best_params, best_score

# class FastTextModel:
# 	def __init__(self, user_id, model_type):
# 		self.user_id = user_id
# 		self.model_path = f"data/models/{model_type}/user_{user_id}_model.bin"
# 		self.best_params = None

# 		download_blob_if_exists(
# 			"ailead-app-data",
# 			self.model_path,
# 			self.model_path
# 		)

# 	def make_lead_input_text(self, user, lead):
# 		tmp_url = lead.url.replace("https://", "").replace("http://", "").replace("www.", "")
# 		tmp_url = " ".join(tmp_url.split('/', 1))
# 		return f"{lead.name} {lead.description} {tmp_url}"

# 	def make_source_input_text(self, user, source):
# 		tmp_url = source.url.replace("https://", "").replace("http://", "").replace("www.", "")
# 		tmp_url = " ".join(tmp_url.split('/', 1))

# 		if source.name and source.name.strip():
# 			tmp_url = source.url.replace("https://", "").replace("http://", "").replace("www.", "")
# 			return f"{source.name} {source.description} {tmp_url}"


# 	def train_grid_search(self, data_path):

# 		if self.best_params is None:
# 			self.best_params, best_score = random_search(data_path)
# 			logger.info(f"Best F1 Score: {best_score}")
# 			logger.info(f"Best Parameters: {self.best_params}")

# 		# Train the model
# 		model = fasttext.train_supervised(data_path, verbose=0, **self.best_params)

# 		# Save the model
# 		model.save_model(self.model_path)

# 		upload_blob(
# 			"ailead-app-data",
# 			self.model_path,
# 			self.model_path
# 		)

# 		# Clean up temporary file
# 		os.remove(data_path)

# 	def predict_lead(self, user, lead):
# 		if not os.path.exists(self.model_path):
# 			return None

# 		model = fasttext.load_model(self.model_path)
# 		input_text = self.make_lead_input_text(user, lead)
# 		if input_text:
# 			prediction = model.predict(input_text)
# 			# Return the probability of the "good" class
# 			return prediction[1][0] if prediction[0][0] == "__label__good" else 1 - prediction[1][0]
# 		else:
# 			return 0

# 	def predict_source(self, user, source):
# 		if not os.path.exists(self.model_path):
# 			return None

# 		model = fasttext.load_model(self.model_path)
# 		input_text = self.make_source_input_text(user, source)
# 		if input_text:
# 			prediction = model.predict(input_text)
# 			# Return the probability of the "good" class
# 			return prediction[1][0] if prediction[0][0] == "__label__good" else 1 - prediction[1][0]
# 		else:
# 			return 0


# # def retrain_models_task(user_id):
# # 	min_app = _make_min_app()
# # 	if not min_app:
# # 		logger.error("Failed to create app context")
# # 		return
# # 	with min_app.app_context():
# # 		start_time = time.time()
# # 		user = User.get_by_id(user_id)
# # 		if not user:
# # 			logger.error(f"User with id {user_id} not found")
# # 			return

# # 		liked_leads = Lead.get_liked_leads(user_id)
# # 		hidden_leads = Lead.get_hidden_leads(user_id)
# # 		hidden_sources = LeadSource.get_hidden_sources(user_id)

# # 		logger.info(f'Training model on {len(liked_leads)} liked leads and {len(hidden_leads)} hidden leads')

# # 		lead_model = FastTextModel(user_id, ModelTypes.LEAD)
# # 		Lead.train_leads_model(user, liked_leads, hidden_leads, lead_model)

# # 		source_model = FastTextModel(user_id, ModelTypes.LEAD_SOURCE)
# # 		LeadSource.train_sources_model(user, liked_leads, hidden_leads, hidden_sources, source_model)

# # 		lead_user_model = UserModels(
# # 			user_id=user_id,
# # 			model_type=ModelTypes.LEAD,
# # 			positive_examples=len(liked_leads),
# # 			negative_examples=len(hidden_leads),
# # 			created_at=datetime.now(pytz.utc)
# # 		)

# # 		db.session.add(lead_user_model)
# # 		db.session.commit()

# # 		source_user_model = UserModels(
# # 			user_id=user_id,
# # 			model_type=ModelTypes.LEAD_SOURCE,
# # 			positive_examples=len(liked_leads),
# # 			negative_examples=len(hidden_leads),
# # 			created_at=datetime.now(pytz.utc)
# # 		)

# # 		db.session.add(source_user_model)
# # 		db.session.commit()


# # 		logger.info(f'Models trained in {time.time() - start_time} seconds')

# # def update_qualities(data):
# # 	user_id = data.get('user_id')
# # 	source_ids = data.get('source_ids')
# # 	lead_ids = data.get('lead_ids')
# # 	if not user_id:
# # 		logger.error("No user_id provided")
# # 		return

# # 	min_app = _make_min_app()
# # 	if not min_app:
# # 		logger.error("Failed to create app context")
# # 		return
# # 	with min_app.app_context():

# # 		user = User.get_by_id(user_id)
# # 		if not user:
# # 			logger.error(f"User with id {user_id} not found")
# # 			return

# # 		if source_ids or lead_ids:
# # 			if source_ids:

# # 				source_model = FastTextModel(user_id, ModelTypes.LEAD_SOURCE)
# # 				updated_sources, failed_source_updates, trained_at = LeadSource.batch_update_quality_scores(user_id, user, source_model, source_ids=source_ids)

# # 				worker_socketio.emit('model_retrained', {'trained_at': trained_at }, to=f'user_{user_id}')

# # 			if lead_ids:
# # 				lead_model = FastTextModel(user_id, ModelTypes.LEAD)
# # 				updated_leads, failed_lead_updates, trained_at = Lead.batch_update_quality_scores(user_id, user, lead_model, lead_ids=lead_ids)

# # 				worker_socketio.emit('model_retrained', {'trained_at': trained_at }, to=f'user_{user_id}')
# # 		else:
# # 			source_model = FastTextModel(user_id, ModelTypes.LEAD_SOURCE)
# # 			updated_sources, failed_source_updates, trained_at = LeadSource.batch_update_quality_scores(user_id, user, source_model)

# # 			lead_model = FastTextModel(user_id, ModelTypes.LEAD)
# # 			updated_leads, failed_lead_updates, trained_at = Lead.batch_update_quality_scores(user_id, user, lead_model)

# # 			worker_socketio.emit('model_retrained', {'trained_at': trained_at }, to=f'user_{user_id}')
