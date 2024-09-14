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
from app.llm import _llm, _get_default_input_data, PromptTemplate

import logging

logger = logging.getLogger('BDB-2EB')

FEW_SHOT_GOOD_EXAMPLES = """
<few_shot_examples>

<good_examples>
- For a customer selling 3d modeling services:
	- "companies using rapid prototyping"
	- "industrial design firms for electronics"
	- "smart home device developers"
- For a customer selling eco-friendly cleaning products and services:
	- "organic restaurants with sustainability focus"
	- "zero-waste cafes and juice bars"
	- "eco-conscious fashion boutiques"
- For a customer selling personalized nutrition and fitness coaching:
	- "tech companies with employee wellness programs"
	- "startups with health-focused benefits"
	- "corporate wellness for executives and parents"
- For a customer selling educational technology solutions:
	- "schools adopting new classroom technologies"
	- "universities using VR for STEM"
	- "institutions with immersive learning tech"
- For a customer selling artisanal spirits and cocktail mixers:
	- "high-end cocktail subscription services"
	- "gourmet catering companies"
	- "boutique hotels with unique cocktail menus"
</good_examples>

<notes>
- Use the good and bad examples to score but only consider the good examples when generating your own query.
- Do not return bad examples in your output.
- If the user's query is already good, you should return it as is.
- If the user's query is bad, you should rewrite it to be better.
- If the user's query is good, you should return it as is.
- If the user's query is bad, you should rewrite it to be better.
</notes>

</few_shot_examples>
"""

FEW_SHOT_EXAMPLES = """
<few_shot_examples>

<good_examples>
- For a customer selling 3d modeling services:
	- "companies using rapid prototyping"
	- "industrial design firms for electronics"
	- "smart home device developers"
- For a customer selling eco-friendly cleaning products and services:
	- "organic restaurants with sustainability focus"
	- "zero-waste cafes and juice bars"
	- "eco-conscious fashion boutiques"
- For a customer selling personalized nutrition and fitness coaching:
	- "tech companies with employee wellness programs"
	- "startups with health-focused benefits"
	- "corporate wellness for executives and parents"
- For a customer selling educational technology solutions:
	- "schools adopting new classroom technologies"
	- "universities using VR for STEM"
	- "institutions with immersive learning tech"
- For a customer selling artisanal spirits and cocktail mixers:
	- "high-end cocktail subscription services"
	- "gourmet catering companies"
	- "boutique hotels with unique cocktail menus"
</good_examples>

<bad_examples>
- For a customer selling 3d modeling services:
	- "companies seeking 3d modeling services"
	- "businesses who need 3d modeling services"
	- "customers looking for 3d modeling services"
- For a customer selling eco-friendly cleaning products and services:
	- "businesses seeking eco-friendly cleaning products"
	- "users looking for eco-friendly cleaning products"
	- "companies seeking eco-friendly cleaning services"
</bad_examples>

<notes>
- Use the good and bad examples to score but only consider the good examples when generating your own query.
- Do not return bad examples in your output.
- If the user's query is already good, you should return it as is.
- If the user's query is bad, you should rewrite it to be better.
- If the user's query is good, you should return it as is.
- If the user's query is bad, you should rewrite it to be better.
</notes>

</few_shot_examples>
"""


query_generation_prompt = PromptTemplate([
	"""You are a GPT trained to rewrite user's B2B lead generation search queries. The user will provide you with their boring search query and a description of what they're looking for. The user may also provide examples of good leads. Your job is to generate a new queries that will return more leads like the examples. You will return a list of {n} queries.""",
	"""These queries are for B2B lead generation, not competitive research. The user is a business owner or sales representitive looking to sell a product and they want to find new customers. We are using the query you return to search the internet and find potential leads for this customer. """
	"""Your priority is to come up with a creative new type of customer for this users product. You cannot directly search for people looking to buy the product so you'll need to be indirect in how you identify them."""
	"""Searches like Businesses looking for XYZ Services are bad. You must be more creative than this. Users may submit these queries and its your job to rewrite them to be more creative and effective. You need to search for a specific type of customer for this users product."""
	"""Below, the user has provided their current query, a description of their product and a description of their ideal customer. Your job is to come up with a new query that will return customers for their product. The search should return businesses that might be interested in purchasing the product the user's business is selling."""
	"""The user has the following query: {query_text}""",
	"""This user describes their product as: {user_industry}""",
	"""The user describes their ideal customer as: {user_description}.""",
	"""The user has included the following location: {location}""",
	"""The user has provided the following examples of good leads. Its very important that you rewrite their query to find more leads like these: \n{example_leads_text}""",
	"""Write a query that will return customers for the users product.""",
	FEW_SHOT_EXAMPLES,
	"""Bad queries will result in a bad user experience. Do not return bad queries. If a user gives you a bad query, rewrite it to be better. If you return a bad query, the user will stop using our product and we will lose money. Please be careful and only return high quality queries.""",
	"""This is the output format. Do not deviate from it. Do not include any text outside of this output format. \n\n {format_instruction}"""
])

query_validation_prompt = PromptTemplate([
	"""You are a GPT trained to figure out if a user's B2B lead generation search query is good. The user will provide you with their search query and a description of what they're looking for. Your job is to check if the query is good or bad. A good query is one that will return customers for the users product. A bad query is one that will not return customers for the users product. You will return a score between 1 and 100 rating the query. A score of 1 is bad and 100 is good."""
	"""These queries are for B2B lead generation, not competitive research. The user is a business owner or sales representitive looking to sell a product and they want to find new customers. We are using the query you return to search the internet and find potential leads for this customer. """
	"""Below, the user has provided their current query, a description of their product and a description of their ideal customer. Your job is to figure out if their query is good or bad and rate it."""
	"""The user has the following query: {query_text}""",
	"""This user describes their product as: {user_industry}""",
	"""The user describes their ideal customer as: {user_description}.""",
	"""The user has included the following location: {location}""",
	FEW_SHOT_EXAMPLES,
	"""This is the output format. Do not deviate from it. Do not include any text outside of this output format. \n\n {format_instruction}"""
])


class GeneratedQuery(BaseModel):
	rewritten_queries: List[str] = Field("", description="The rewritten query that the model generated")

class QueryValidation(BaseModel):
	query_score: int = Field(False, description="Quality of the query between 1 and 100. 1 is bad and 100 is good.")

generated_query_parser = PydanticOutputParser(pydantic_object=GeneratedQuery)
query_validation_parser = PydanticOutputParser(pydantic_object=QueryValidation)

def rewrite_query(data, socketio_obj=None, app_obj=None):
	query_text = data['user_query']
	user = data['user']
	location = data['location']
	example_leads = data['example_leads']

	print(f'Rewriting query: {query_text}')
	if user.credits < 1:
		return query_text

	if example_leads:
		example_leads_text = '\n'.join([url for url in example_leads])
	else:
		example_leads_text = ''

	data = _get_default_input_data(user, query_text, None)

	data.update({
		'location': location,
		'example_leads_text': example_leads_text,
		'query_text': query_text,
		'n': 1
	})

	output, tokens_used_usd = _llm(data, query_generation_prompt, generated_query_parser, model_name='gpt-4o', temp=1)
	if output and output.rewritten_queries and output.rewritten_queries[0] and output.rewritten_queries[0].strip():
		user.move_credits(
			amount=tokens_used_usd * -1000 * 2,
			cost_usd=tokens_used_usd,
			trxn_type=CreditLedgerType.CHECK_QUERY,
			socketio_obj=socketio_obj,
			app_obj=app_obj
		)

		return output.rewritten_queries[0].strip()
	else:
		return query_text


def validate_query(data, socketio_obj=None, app_obj=None):
	query_text = data['user_query']
	user = data['user']
	location = data['location']
	example_leads = data['example_leads']

	print(f'Validating query: {query_text}')
	if user.credits < 1:
		return query_text

	if example_leads:
		example_leads_text = '\n'.join([url for url in example_leads])
	else:
		example_leads_text = ''

	data = _get_default_input_data(user, query_text, None)

	data.update({
		'location': location,
		'example_leads_text': example_leads_text,
		'query_text': query_text,
	})

	output, tokens_used_usd = _llm(data, query_validation_prompt, query_validation_parser, model_name='gpt-4o', temp=1)

	user.move_credits(
		amount=tokens_used_usd * -1000 * 2,
		cost_usd=tokens_used_usd,
		trxn_type=CreditLedgerType.VALIDATE_QUERY,
		socketio_obj=socketio_obj,
		app_obj=app_obj
	)

	print(f"Output: {output}")
	
	if output and output.query_score > 20:
		return True
	else:
		return False

def generate_queries(data, socketio_obj=None, app_obj=None):
	query_text = data['user_query']
	user = data['user']
	location = data['location']
	example_leads = data['example_leads']

	print(f'Validating query: {query_text}')
	if user.credits < 1:
		return query_text

	if example_leads:
		example_leads_text = '\n'.join([url for url in example_leads])
	else:
		example_leads_text = ''

	data = _get_default_input_data(user, query_text, None)

	data.update({
		'location': location,
		'example_leads_text': example_leads_text,
		'query_text': query_text,
		'n': 5
	})

	output, tokens_used_usd = _llm(data, query_generation_prompt, generated_query_parser, model_name='gpt-4o', temp=1)

	user.move_credits(
		amount=tokens_used_usd * -1000 * 2,
		cost_usd=tokens_used_usd,
		trxn_type=CreditLedgerType.VALIDATE_QUERY,
		socketio_obj=socketio_obj,
		app_obj=app_obj
	)

	print(f"Output: {output}")
	
	if output and output.rewritten_queries:
		return output.rewritten_queries
	else:
		return []