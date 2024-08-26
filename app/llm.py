import random
import requests
from local_settings import OPENAI_API_KEY, SERP_API_KEY, GROQ_API_KEY
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Optional, List
from bs4 import BeautifulSoup
from langchain.prompts import PromptTemplate
from app.utils import _tidy_url
from app.models import Lead, LeadSource, CreditLedgerType

import logging

logger = logging.getLogger('BDB-2EB')

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
]

class RewrittenQuery(BaseModel):
	original_query: str = Field("", description="The original query that the user entered")
	rewritten_query: str = Field("", description="The rewritten query that the model generated")

class Url(BaseModel):
	url: str = Field("", description="A relevant URL")

class CollectionOutput(BaseModel):
	"""
	Used to parse lead source
		- URL is requested, text from page is parsed
	"""
	name: str = Field("", description="The name of the source company or organization")
	description: str = Field("", description="A brief description of this page of the source material")
	leads: Optional[List[Url]] = Field(
		[],
		description="A list of URLs pointing to leads. These sites are directly applicable to the user's query and may contain contact information."
	)
	lead_sources: Optional[List[Url]] = Field(
		[],
		description="A list of URLs pointing to lead sources. These are not directly applicable to the user's query but may contain links to relevant sites."
	)
	invalid_link: Optional[bool] = Field(
		None,
		description="The link provided by the user is invalid. Do not use this value, it will be set by the system if necessary."
	)
	not_enough_credits: Optional[bool] = Field(
		False,
		description="User is out of credits. Do not use this value, it will be set by the system if necessary."
	)
	is_lead: Optional[bool] = Field(None, description="Mark this value as true if this source should also be marked as a lead")


class ValidationOutput(BaseModel):
	"""
	Used to parsed a lead's website
	"""
	name: str = Field("", description="The name of the company or organization")
	description: str = Field("", description="A brief description of the company or organization and how they are relevant to the user's query")
	email_address: Optional[str] = Field(None, description="A valid contact email address found on the website for users to contact the company. This is the best outcome.")
	next_link: Optional[str] = Field(None, description="A link to a page that might have an email address (e.g. a contact page)")
	contact_page: Optional[str] = Field(None, description="A link to a contact page with a contact form")
	no_email_found: Optional[bool] = Field(None, description="No relevant email address found")
	relevant_to_user: Optional[bool] = Field(None, description="Mark this value as true if this lead is relevant to the user's query")
	invalid_link: Optional[bool] = Field(None, description="The link provided by the user is invalid. Do not use this value, it will be set by the system if necessary.")
	not_enough_credits: Optional[bool] = Field(
		None,
		description="User is out of credits. Do not use this value, it will be set by the system if necessary."
	)
	leads: Optional[List[Url]] = Field(
		[],
		description="A list of URLs pointing to leads found on the web. These sites are directly applicable to the user's query and may contain contact information for the organization."
	)
	lead_sources: Optional[List[Url]] = Field(
		[],
		description="A list of URLs that point to sites may contain leads. These sites may not be directly applicable to the user's query but may contain links to relevant sites."
	)


rewriting_parser = PydanticOutputParser(pydantic_object=RewrittenQuery)
collection_parser = PydanticOutputParser(pydantic_object=CollectionOutput)
validation_parser = PydanticOutputParser(pydantic_object=ValidationOutput)

class PromptTemplate():
	def __init__(self, template_text):
		self.template = template_text

	def render(self, **kwargs):
		if isinstance(self.template, list):
			return [t.format(**kwargs) for t in self.template]
		else:
			return self.template.format(**kwargs)

query_reformatting_prompt = PromptTemplate([
	"""You are a GPT trained to rewrite user's search queries. The user will provide you with their basic search query and a description of what they're looking for. Your job is to rewrite the query in a way that is more likely to return relevant results.""",
	"""This is the output format. Do not deviate from it. Do not include any text outside of this output format.
{format_instruction}
"""
])

source_lead_collection_prompt = PromptTemplate([
	"""You are a GPT trained to collect leads from a source of leads. The user provided the contents of a page potentially containing leads.""",
	"""Filter the content and return the metadata relevant to the user.""",
	"""
## Description of Leads and Lead Sources

Metadata includes page content and URLs. Relevant links include leads and lead sources.
	- A lead is a company or organization that may be interested in the user's services.
	- A lead source is a website that is likely to contain leads.

Only URLs are relevant. The following are not relevant:
	- Email address
	- Phone numbers
	- Skype, AOL or other usernames
	- Twitter, Facebook, Instagram or other social media profiles
	- Maps or directions

Internal links within a site are valid. We will handle transforming them into a full URL.""",
	"""This user describes their product as "{user_industry}".

The user describes their ideal customer as:
{user_description}

Previously the user has liked leads like the following:
{previous_leads}""",
	"""You need to provide:
- Name: The name of the source company or organization
- Description: A brief description of the source material
- Leads: Links that are directly applicable to the user's query and may contain contact information
	- Links to websites that may be interested in the user's services
	- For example, company websites or contact pages
	- Provide a max of one lead per organization
	- If the page contains multiple links to an organization, pick the most relevant one
	- These are de-duplicated by domain so make sure to only include one link per domain
	- Do not include links that aren't the main domain of the organization
- Lead Sources: Not directly applicable to the user's query but may contain links to relevant sites
	- Links to websites that may contain links to sites that may be interested in the user's services
	- For example, blogs, forums, or directories
	- Provide a max of one lead per organization
	- If the page contains multiple links to an organization, pick the most relevant one
	- These are not de-duplicated by domain so include all relevant links
	""",
	"""This is the output format. Do not deviate from it. Do not include any text outside of this output format.
{format_instruction}
"""
])

lead_validation_prompt = PromptTemplate([
	"""You are a GPT trained to extract contact info from websites. The user will provide you with the text render on a website and your job is to help them find the contact information for the organization.""",
	"""This user describes their product as "{user_industry}".
The query they searched in this particular instance is "{user_query}".

The user describes their ideal customer as:
{user_description}""",
	"""If you see an email address visible, output the email address in the "email_address" field.
If you see a contact page that might have an email address, output the link to the contact page in the "contact_page" field.
If you do not see anything relevant, use the "no_email_found" field.
If the link provided does not work, use the "invalid_link" field.""",

	"""This is the output format. Do not deviate from it. Do not include any text outside of this output format.
{format_instruction}
"""])


MODEL_PRICING = {
	"gpt-3.5-turbo-0125": {"input": 0.5 / 1e6, "output": 1.5 / 1e6 },
	"gpt-4-0125-preview": {"input": 10 / 1e6 , "output": 30 / 1e6 },
	"gpt-4o": {"input": 5 / 1e6 , "output": 15 / 1e6 },
	"gpt-4o-mini": {"input": 0.15 / 1e6 , "output": 0.600 / 1e6 },
	"gpt-4-turbo": {"input": 10 / 1e6 , "output": 30 / 1e6 },
	"gpt-4-1106-preview": {"input": 10 / 1e6 , "output": 30 / 1e6 },
	"gpt-4-1106-vision-preview": {"input": 10 / 1e6 , "output": 30 / 1e6 },
	"claude-3-opus-20240229": {"input": 15 / 1e6, "output": 75 / 1e6 },
	"claude-3-sonnet-20240229": {"input": 3 / 1e6, "output": 15 / 1e6 },
	"claude-3-5-sonnet-20240620": {"input": 3 / 1e6, "output": 15 / 1e6 },
	"claude-3-haiku-20240307": {"input": 0.25 / 1e6, "output": 1.25 / 1e6},
	"replicate/meta/meta-llama-3.1-405b-instruct": {"input": 9.5 / 1e6, "output": 9.5 / 1e6},
	"groq/llama-3.1-70b-versatile": {"input": 0.59 / 1e6, "output": 0.79 / 1e6},
	"groq/mixtral-8x7b-32768": {"input": 0.24 / 1e6, "output": 0.24 / 1e6},
}


def _llm(user_input, template, parser, parse_output=True, user=None, query=None, previous_leads=[], model_name='gpt-4o-mini'):

	if not model_name:
		model_name='gpt-4o-mini'

	if user:
		description = user.user_description
		industry = user.industry
	else:
		description = "This user has not provided a description. Assume they are looking for organizations like their query describes."
		industry = "General"

	if not previous_leads:
		previous_leads = "No leads have been liked yet."

	if query:
		user_query = query.reformatted_query
	else:
		user_query = "No query provided."

	system_prompt = template.render(
		format_instruction=parser.get_format_instructions(),
		user_description=description,
		user_industry=industry,
		user_query=user_query,
		previous_leads=previous_leads
	)

	headers = {
		'Content-Type': 'application/json',
	}

	if 'groq' in model_name:
		url = "https://api.groq.com/openai/v1/chat/completions"
		headers['Authorization'] = f'Bearer {GROQ_API_KEY}'
		input_model_name = model_name.replace('groq/', '')
	else:
		url = "https://api.openai.com/v1/chat/completions"
		headers['Authorization'] = f'Bearer {OPENAI_API_KEY}'
		input_model_name = model_name

	if isinstance(system_prompt, str):

		messages = [{
			"role": "system",
			"content": system_prompt
		}]
	elif isinstance(system_prompt, list):
		messages = [
			{
				"role": "system",
				"content": prompt
			} for prompt in system_prompt
		]
	else:
		raise ValueError("system_prompt must be a string or list")

	messages += [{
		"role": "user",
		"content": user_input
	}]

	data = {
		'model': input_model_name,
		'messages': messages,
		'max_tokens': 1000,
		'temperature': 0.1
	}

	response = requests.post(url, headers=headers, json=data)
	if response.status_code == 200:
		response_json = response.json()
		prompt_tokens = response_json.get('usage', {}).get('prompt_tokens', 0)
		completion_tokens = response_json.get('usage', {}).get('completion_tokens', 0)
		tokens_used_usd = (MODEL_PRICING[model_name]["input"] * (prompt_tokens)) + (MODEL_PRICING[model_name]["output"] * (completion_tokens))
		print(f'######### Tokens used: {tokens_used_usd:.2f} USD')
		if parse_output:
			try:
				return parser.parse(response_json['choices'][0]['message']['content']), tokens_used_usd
			except:
				print(f'Error parsing response: {response.json()}')
				return None, 0
		else:
			return response.json()['choices'][0]['message']['content'], tokens_used_usd
	else:
		print(f'LLM Error: {response.status_code} - {response.json()}')
		return None, 0


def get_visible_links(link):
	headers = {
		'User-Agent': random.choice(user_agents)
	}
	session = requests.Session()
	try:
		resp = session.get(link, headers=headers, timeout=10, allow_redirects=True)
		resp.raise_for_status()  # Raises an HTTPError for bad responses
	except requests.exceptions.RequestException as e:
		return None, None

	if resp.status_code != 200:
		return None, None
	html = resp.text

	if not html:
		return None, None

	soup = BeautifulSoup(html, 'html.parser')

	# Remove all script and style elements
	for script_or_style in soup(['script', 'style']):
		script_or_style.decompose()

	# Extract text and links
	visible_text_with_links = []
	raw_text = []
	links = []

	for element in soup.descendants:
		if isinstance(element, str):
			text = element.strip()
			if text:
				raw_text.append(text)
		elif element.name == 'a' and 'href' in element.attrs:
			link_text = element.get_text(separator=' ', strip=True)
			link_url = element.get('href')
			placeholder_link_text = f"[PLACEHOLDER_LINK_{len(links)}]"
			raw_text.append(placeholder_link_text)
			links.append((link_url, link_text, len(raw_text) - 1, placeholder_link_text))

	raw_text = ' '.join(raw_text).split()

	for link_obj in links:
		link_url, link_text, pos, placeholder_text = link_obj
		if not link_url:
			continue
		if link_url.startswith('tel:') or link_url.startswith('mailto:'):
			continue
		start = max(0, pos - 20)
		end = min(len(raw_text), pos + 21)

		if link_url[0] == '/':
			link_url = _tidy_url(link, link_url)

		context = ' '.join(raw_text[start:pos]) + f" {link_text} " + ' '.join(raw_text[pos+1:end])
		visible_text_with_links.append({
			"url": link_url,
			"url_id": placeholder_text,
			"context": context
		})

	# visible_text_with_links = '\n\n'.join(visible_text_with_links)

	# Get OpenGraph image
	og_image = soup.find('meta', property='og:image')
	og_image_url = og_image.get('content') if og_image and og_image.get('content') else None

	return str(visible_text_with_links), og_image_url

def get_visible_text_and_links(link):
	headers = {
		'User-Agent': random.choice(user_agents)
	}
	session = requests.Session()
	try:
		resp = session.get(link, headers=headers, timeout=10, allow_redirects=True)
		resp.raise_for_status()  # Raises an HTTPError for bad responses
	except requests.exceptions.RequestException as e:
		return None, None

	if resp.status_code != 200:
		return None, None
	html = resp.text

	if not html:
		return None, None

	soup = BeautifulSoup(html, 'html.parser')
	rendered_text = []

	# Remove all script and style elements
	for script_or_style in soup(['script', 'style']):
		script_or_style.decompose()

	# Extract text and links
	for element in soup.descendants:
		if isinstance(element, str):
			text = element.strip()
			if text:
				rendered_text.append(text)
		elif element.name == 'a' and 'href' in element.attrs:
			link_text = element.get_text(separator=' ', strip=True)
			link_url = element.get('href')
			rendered_text.append(f"{link_text} ({link_url})")

	# Get OpenGraph image
	og_image = soup.find('meta', property='og:image')
	if og_image and og_image.get('content'):
		og_image_url = og_image.get('content')
	else:
		og_image_url = None

	rendered_text = ' '.join(rendered_text)
	rendered_text = rendered_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
	return rendered_text, og_image_url


def search_serpapi(query):
	params = {
		'q': query,
		'hl': 'en',
		'gl': 'us',
		'google_domain': 'google.com',
		'api_key': SERP_API_KEY
	}
	response = requests.get('https://serpapi.com/search', params=params)
	if response.status_code == 200:
		return response.json()
	else:
		return None

def search_and_validate_leads(new_query, previous_leads, app_obj=None, socketio_obj=None, search_mult=10):
	"""
	Runs a search query and checks each source found in the query for leads and other lead sources
	"""

	if new_query.user.credits < 1:
		return [], "Insufficient credits", 0
	search_results = search_serpapi(new_query.reformatted_query)

	# print(search_results)
	if not search_results:
		return [], "Failed to search SERP API", 0

	leads = []
	total_tokens_used = 0
	for result in search_results.get('organic_results', []):
		url = result.get('link')

		collected_leads, image_url, tokens_used_usd = collect_leads_from_url(
			url=url,
			user=new_query.user,
			previous_leads=previous_leads,
			app_obj=app_obj,
			socketio_obj=socketio_obj
		)

		logger.info(collected_leads)

		total_tokens_used += tokens_used_usd

		if collected_leads and collected_leads.not_enough_credits:
			return [], "Insufficient credits", total_tokens_used

		if not collected_leads or (not collected_leads.leads and not collected_leads.lead_sources):
			continue

		new_source_obj = LeadSource.check_and_add(
			url,
			new_query.user_id,
			new_query.id,
			image_url=image_url
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
				if new_lead_obj and socketio_obj and app_obj:
					with app_obj.app_context():
						socketio_obj.emit('leads_updated', {'leads': [new_lead_obj.to_dict()]}, to=f'user_{new_query.user_id}')

		if collected_leads.lead_sources:
			for lead_source in collected_leads.lead_sources:
				new_source_obj = LeadSource.check_and_add(
					url=lead_source.url,
					user_id=new_query.user_id,
					query_id=new_query.id
				)
				if new_source_obj and socketio_obj and app_obj:
					with app_obj.app_context():
						socketio_obj.emit('sources_updated', {'sources': [new_source_obj.to_dict()]}, to=f'user_{new_query.user_id}')

	return True, "", total_tokens_used





def _llm_validate_lead(link, user, query):
	"""
	Checks if a lead is valid and relevant
	"""

	print(f'Validating lead from link: {link}')
	if user.credits < 1:
		return ValidationOutput(
			not_enough_credits=True
		), None, 0

	visible_text, opengraph_img_url = get_visible_text_and_links(link)
	opengraph_img_url = _tidy_url(link, opengraph_img_url)
	if visible_text:
		output, tokens_used_usd = _llm(
			visible_text,
			lead_validation_prompt,
			validation_parser,
			user,
			query=query,
			model_name=(user.model_preference or 'gpt-4o-mini')
		)
		if not output:
			output = ValidationOutput(
				invalid_lead=True,
			)
		return output, opengraph_img_url, tokens_used_usd
	else:
		return ValidationOutput(
			invalid_link=True
		), opengraph_img_url, 0

def collect_leads_from_url(url, user, previous_leads, url_collection_mult=3, app_obj=None, socketio_obj=None):
	print(f'Collecting leads from URL: {url}')
	if user.credits < 1:
		return CollectionOutput(
			not_enough_credits=True
		), None, 0

	visible_text, opengraph_img_url = get_visible_links(url)
	if visible_text:
		output, tokens_used_usd = _llm(
			user_input=visible_text,
			template=source_lead_collection_prompt,
			parser=collection_parser,
			user=user,
			previous_leads=previous_leads,
			model_name=(user.model_preference or 'gpt-4o-mini')
		)
		return output, opengraph_img_url, tokens_used_usd
	else:
		return CollectionOutput(
			invalid_link=True
		), opengraph_img_url, 0

def rewrite_query(user_query, user, rewrite_query_mult=10, socketio_obj=None):
	print(f'Rewriting query: {user_query}')
	if user.credits < 1:
		return None
	output, tokens_used_usd = _llm(user_query, query_reformatting_prompt, rewriting_parser, user)
	user.move_credits(
		tokens_used_usd * -1000 * rewrite_query_mult,
		CreditLedgerType.CHECK_QUERY,
		socketio_obj=socketio_obj
	)
	return output
