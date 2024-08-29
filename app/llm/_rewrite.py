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


query_reformatting_prompt = PromptTemplate([
	"""You are a GPT trained to rewrite user's B2B lead generation search queries. The user will provide you with their basic search query and a description of what they're looking for. The user may also provide examples of good leads. Your job is to rewrite the query to return more relevant search results.""",
	"""These queries are for B2B lead generation, not competitive research. The user is a business owner or sales representitive looking to sell a product and they want to find new customers. We are using the query you return to search the internet and find potential leads for this customer. """
	"""Below, the user has provided a query, a description of their product and a description of their ideal customer. Your job is to update their query to return more links like their ideal customer. The search should return businesses that might be interested in purchasing the product the user's business is selling."""
	"""The user has provided the following query: {query_text}""",
	"""This user describes their product as: {user_industry}""",
	"""The user describes their ideal customer as: {user_description}.""",
	"""The user has included the following location: {location}""",
	"""The user has provided the following examples of good leads. Its very important that you rewrite their query to find more leads like these: \n{example_leads_text}""",
	"""Write a query that will return customers for the users product.""",
	"""This is the output format. Do not deviate from it. Do not include any text outside of this output format. \n\n {format_instruction}"""
])

class RewrittenQuery(BaseModel):
	rewritten_query: str = Field("", description="The rewritten query that the model generated")

rewriting_parser = PydanticOutputParser(pydantic_object=RewrittenQuery)

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
	})

	output, tokens_used_usd = _llm(data, query_reformatting_prompt, rewriting_parser, model_name='gpt-4o')
	if output:
		user.move_credits(
			amount=tokens_used_usd * -1000 * 5,
			cost_usd=tokens_used_usd,
			trxn_type=CreditLedgerType.CHECK_QUERY,
			socketio_obj=socketio_obj,
			app_obj=app_obj
		)

		return output.rewritten_query
	else:
		return query_text