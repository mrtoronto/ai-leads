
def get_standard_url(url):
	if not url.startswith('http'):
		url = 'https://' + url
	if 'http:' in url:
		url = url.replace('http:', 'https:')

	if 'www.' not in url and '://' in url:
		protocol, rest = url.split('://', 1)
		url = f'{protocol}://www.{rest}'
	elif 'www.' not in url:
		url = f'https://www.{url}'

	if url[-1] == '/':
		url = url[:-1]

	url = url.split('?')[0]

	return url


def get_base_url(url):
	url = get_standard_url(url)
	base_url = url.split('/')
	base_url = '/'.join(base_url[:3])
	### Add www. if it's missing, assume https is present
	return base_url


def _tidy_url(example_url, to_be_fixed):
	"""
	Fixes URLs like '/contact' to 'https://example.com/contact'

	"""

	if not to_be_fixed:
		return ''
	if to_be_fixed.startswith('/'):
		base_url = example_url.split('/')
		base_url = '/'.join(base_url[:3])
		output = base_url + to_be_fixed
	else:
		output = to_be_fixed

	if not output.startswith('http'):
		output = 'https://' + output

	return output


def _useful_url_check(url):

	if not _real_url_check(url):
		return False

	if 'facebook.com' in url:
		return False
	if 'twitter.com' in url:
		return False
	if 'instagram.com' in url:
		return False
	if 'linkedin.com' in url:
		return False
	if 'youtube.com' in url:
		return False
	if 'maps.google.com' in url:
		return False
	if 'goo.gl/maps' in url:
		return False

	return True

def _real_url_check(url):
	if url == 'https://www.':
		return False
	if url == 'http://www.':
		return False
	if url == 'http://www':
		return False
	if url == 'https://www':
		return False
	if url == 'https://www.www':
		return False
	else:
		return True


from google.cloud import storage
from google.oauth2 import service_account
def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""

    credentials = service_account.Credentials.from_service_account_file('google_creds.json')
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        f"File {source_file_name} uploaded to {destination_blob_name}."
    )


def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""

    credentials = service_account.Credentials.from_service_account_file('google_creds.json')
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    blob.download_to_filename(destination_file_name)

    print(
        f"Blob {source_blob_name} downloaded to {destination_file_name}."
    )


def download_blob_if_exists(bucket_name, source_blob_name, destination_file_name):
	"""Downloads a blob from the bucket."""

	credentials = service_account.Credentials.from_service_account_file('google_creds.json')
	storage_client = storage.Client(credentials=credentials)
	bucket = storage_client.bucket(bucket_name)
	blob = bucket.blob(source_blob_name)

	if blob.exists():
		blob.download_to_filename(destination_file_name)
		print(
			f"Blob {source_blob_name} downloaded to {destination_file_name}."
		)
	else:
		print(
			f"Blob {source_blob_name} does not exist."
		)


import random
import hashlib
from local_settings import SALT
import logging

logger = logging.getLogger('BDB2-2EB')

def get_request_hash(ip_address, user_agent, user_hash):
	if not user_hash:
		try:
			hasher = hashlib.sha256()

			# Generate a random number
			random_number = random.randint(0, int(1e7))

			# Combine IP address, User-Agent, random number, and SALT
			hash_input = f"{ip_address}{user_agent}{random_number}{SALT}"
			hasher.update(hash_input.encode('utf-8'))
			user_hash = hasher.hexdigest()
		except Exception as e:
			logger.error(f'Error generating user hash: {e}')
			user_hash = None

	return user_hash
