from app import worker_socketio, create_minimal_app
from app.models import LeadSource, Lead, ModelTypes, User, CreditLedgerType, Job, JobTypes
from rq import get_current_job
from app.llm import _llm_validate_lead, collect_leads_from_url
from app.models.query import Query
from app.utils import _tidy_url, _useful_url_check
from flask_socketio import emit
from app import db
from worker import _make_min_app
from worker.process_search import search_request_task
# from app.tasks import queue_search_request

from sqlalchemy.orm import scoped_session, sessionmaker
import logging

logger = logging.getLogger('BDB-2EB')

def check_lead_task(lead_id):
    job = get_current_job()
    min_app = _make_min_app()
    if not min_app:
        logger.error("Failed to create app context")
        return
    with min_app.app_context():
        Session = scoped_session(sessionmaker(bind=db.engine))
        session = Session()
        try:
            lead = session.query(Lead).get(lead_id)
            if not lead:
                return

            lead_query = session.query(Query).get(lead.query_id)
            lead_source = session.query(LeadSource).get(lead.source_id) if lead.source_id else None
            lead_user = session.query(User).get(lead.user_id)

            lead_job_obj = session.query(Job).filter_by(lead_id=lead_id, started=False).order_by(Job.id.desc()).first()
            if lead_job_obj:
                lead_job_obj._started(job.id if job else None)
            else:
                lead_job_obj = Job(
                    lead_id=lead_id,
                    _type=JobTypes.LEAD_CHECK
                )
                session.add(lead_job_obj)
                session.commit()

                lead_job_obj._started(job.id if job else None)

            if (lead.checked and lead.valid):
                lead._finished(
                    socketio_obj=worker_socketio,
                    app_obj=min_app,
                    session=session
                )
                session.commit()
                return

            if (
                (lead.hidden) or \
                (lead.query_obj and (lead.query_obj.hidden or lead.query_obj.over_budget))
            ):
                lead._finished(
                    checked=False,
                    socketio_obj=worker_socketio,
                    app_obj=min_app,
                    session=session
                )
                session.commit()
                return

            if not lead.checking:
                lead.checking = True
                worker_socketio.emit('leads_updated', {'leads': [lead.to_dict()]}, to=f'user_{lead.user_id}')

            total_tokens_used_usd = 0

            first_validation_output, opengraph_img_url, tokens_used_usd = _llm_validate_lead(
                link=lead.url,
                query=lead.query_obj,
                user=lead_user
            )
            total_tokens_used_usd += tokens_used_usd
            final_validation_output = first_validation_output

            if not first_validation_output:
                lead._finished(
                    socketio_obj=worker_socketio,
                    app_obj=min_app,
                    session=session
                )
                lead.save(session=session)
                worker_socketio.emit('leads_updated', {'leads': [lead.to_dict()]}, to=f'user_{lead.user_id}')
                session.commit()
                return

            if (first_validation_output.next_link or first_validation_output.contact_page) and not first_validation_output.email_address:
                loop_idx = 0
                validation_output = first_validation_output
                while (validation_output.next_link or validation_output.contact_page) and not (validation_output.email_address):
                    next_link = (validation_output.next_link or validation_output.contact_page or "")

                    if next_link.startswith('/') and lead.url:
                        base_url = lead.url.split('/')
                        base_url = '/'.join(base_url[:3])
                        next_link = base_url + next_link

                    validation_output, opengraph_img_url, tokens_used_usd = _llm_validate_lead(
                        link=next_link,
                        user=lead_user,
                        query=lead.query_obj,
                    )

                    total_tokens_used_usd += tokens_used_usd
                    if validation_output:

                        if validation_output.not_enough_credits or final_validation_output.not_enough_credits:
                            lead.checking = False
                            lead.save(session=session)
                            worker_socketio.emit('leads_updated', {'leads': [lead.to_dict()]}, to=f'user_{lead.user_id}')
                            session.commit()
                            return

                        if not final_validation_output:
                            final_validation_output = validation_output
                        if validation_output.contact_page and not final_validation_output.contact_page:
                            final_validation_output.contact_page = validation_output.contact_page

                        if validation_output.email_address and not final_validation_output.email_address:
                            final_validation_output.email_address = validation_output.email_address

                        if validation_output.name and not final_validation_output.name:
                            final_validation_output.name = validation_output.name

                        if validation_output.description and not final_validation_output.description:
                            final_validation_output.description = validation_output.description

                        if not final_validation_output.leads:
                            final_validation_output.leads = validation_output.leads

                        if not final_validation_output.relevant_to_user:
                            final_validation_output.relevant_to_user = validation_output.relevant_to_user

                        if validation_output.leads:
                            if final_validation_output.leads:
                                final_validation_output.leads += validation_output.leads
                            else:
                                final_validation_output.leads = validation_output.leads

                        if not final_validation_output.lead_sources:
                            final_validation_output.lead_sources = validation_output.lead_sources

                        if validation_output.lead_sources:
                            if final_validation_output.lead_sources:
                                final_validation_output.lead_sources += validation_output.lead_sources
                            else:
                                final_validation_output.lead_sources = validation_output.lead_sources

                    if not validation_output or loop_idx > 3:
                        break
                    loop_idx += 1

            if not final_validation_output:
                logger.error("No validation output")
                lead._finished(
                    socketio_obj=worker_socketio,
                    app_obj=min_app,
                    session=session
                )
                lead.save(session=session)
                worker_socketio.emit('leads_updated', {'leads': [lead.to_dict()]}, to=f'user_{lead.user_id}')
                session.commit()
                return

            if final_validation_output.not_enough_credits:
                lead.checking = False
                lead.save(session=session)
                worker_socketio.emit('leads_updated', {'leads': [lead.to_dict()]}, to=f'user_{lead.user_id}')
                session.commit()
                return

            lead.name = final_validation_output.name or lead.name
            lead.relevant = final_validation_output.relevant_to_user or lead.relevant
            lead.image_url = opengraph_img_url or lead.image_url
            lead.description = final_validation_output.description or lead.description
            lead.contact_info = final_validation_output.email_address or lead.contact_info
            lead.valid = bool(final_validation_output.email_address or final_validation_output.contact_page or final_validation_output.next_link or final_validation_output.no_email_found)
            lead.contact_page = _tidy_url(lead.url, final_validation_output.contact_page or final_validation_output.next_link) if (final_validation_output.contact_page or final_validation_output.next_link) else ""
            lead.checked = True
            lead.checking = False
            lead.save(session=session)

            if final_validation_output.lead_sources:
                for new_lead_source in final_validation_output.lead_sources:
                    if new_lead_source and new_lead_source.url and _useful_url_check(new_lead_source.url):
                        new_source = LeadSource.check_and_add(
                            url=new_lead_source.url,
                            user_id=lead.user_id,
                            query_id=lead.query_id,
                            session=session
                        )
                        if new_source:
                            worker_socketio.emit('sources_updated', {'sources': [new_source.to_dict()]}, to=f'user_{lead.user_id}')

            ### If lead check had leads in to,
            ### Add lead as a source and save new leads to that source
            if final_validation_output.leads:
                new_source = LeadSource.check_and_add(
                    url=lead.url,
                    user_id=lead.user_id,
                    query_id=lead.query_id,
                    checked=True,
                    valid=True,
                    name=lead.name,
                    description=lead.description,
                    image_url=lead.image_url,
                    session=session
                )
                if new_source:
                    worker_socketio.emit('sources_updated', {'sources': [new_source.to_dict()]}, to=f'user_{lead.user_id}')

                for new_lead in final_validation_output.leads:
                    if new_lead and new_lead.url and _useful_url_check(new_lead.url):
                        new_lead_obj = Lead.check_and_add(
                            url=new_lead.url,
                            user_id=lead.user_id,
                            query_id=lead.query_id,
                            source_id=new_source.id if new_source else lead.source_id,
                            session=session
                        )
                        if new_lead_obj:
                            worker_socketio.emit('leads_updated', {'leads': [new_lead_obj.to_dict()]}, to=f'user_{lead.user_id}')

            lead._finished(
                socketio_obj=worker_socketio,
                app_obj=min_app,
                session=session
            )
            session.commit()

            if 'mini' in (lead_user.model_preference or 'gpt-4o-mini'):
                mult = min_app.config['PRICING_MULTIPLIERS']['check_lead_mini']
            else:
                mult = min_app.config['PRICING_MULTIPLIERS']['check_lead']

            if total_tokens_used_usd:
                # Fetch the latest data
                latest_lead = session.query(Lead).with_for_update().get(lead.id)
                latest_query = session.query(Query).with_for_update().get(lead.query_id)
                latest_user = session.query(User).with_for_update().get(lead.user_id)
                
                latest_user.move_credits(
                    amount=total_tokens_used_usd * -1000 * mult,
                    cost_usd=total_tokens_used_usd,
                    trxn_type=CreditLedgerType.CHECK_LEAD,
                    socketio_obj=worker_socketio,
                    app_obj=min_app,
                    session=session
                )

                if latest_lead.lead_source:
                    latest_source = session.query(LeadSource).with_for_update().get(latest_lead.source_id)
                    if latest_source.total_cost_credits:
                        latest_source.total_cost_credits += total_tokens_used_usd * mult * 1000
                    else:
                        latest_source.total_cost_credits = total_tokens_used_usd * mult * 1000

                if latest_query.total_cost_credits:
                    latest_query.total_cost_credits += total_tokens_used_usd * mult * 1000
                else:
                    latest_query.total_cost_credits = total_tokens_used_usd * mult * 1000
                if latest_lead.total_cost_credits:
                    latest_lead.total_cost_credits += total_tokens_used_usd * mult * 1000
                else:
                    latest_lead.total_cost_credits = total_tokens_used_usd * mult * 1000
                if latest_lead.unique_cost_credits:
                    latest_lead.unique_cost_credits += total_tokens_used_usd * mult * 1000
                else:
                    latest_lead.unique_cost_credits = total_tokens_used_usd * mult * 1000

                if latest_query.budget and latest_query.total_cost_credits > latest_query.budget:
                    latest_query.over_budget = True

                session.commit()

            with session.begin():
                latest_query = session.merge(latest_query)
                worker_socketio.emit('queries_updated', {'queries': [latest_query.to_dict(cost=True, example_leads=True)]}, to=f'user_{latest_query.user_id}')

            worker_socketio.emit('leads_updated', {'leads': [lead.to_dict()]}, to=f'user_{lead.user_id}')

            if lead.example_lead:
                ### Check if the request has more example leads
                parent_query = lead.query_obj
                if parent_query:
                    ### Get all example leads for the query
                    example_leads = parent_query.leads.filter_by(example_lead=True).all()

                    if all([l.checked for l in example_leads]):
                        min_app.config['high_priority_queue'].enqueue(search_request_task, lead.query_obj.id)

                        new_job = Job(
                            query_id=lead.query_obj.id,
                            _type=JobTypes.QUERY_CHECK,
                        )
                        new_job.save(session=session)
        finally:
            Session.remove()
