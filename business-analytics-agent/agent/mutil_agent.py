from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from config.logger import logger as log
from config import get_project_client_config
from model.ChatBody import ChatBody
from util.yield_util import generate_yield_json, res_tool
from tools.branch_company_info_tool import branch_company_info_tool
from tools.business_management_tool import business_management_tool
from tools.performance_report_tool import performance_report_tool
from tools.sandbox_tool import sandbox_tool
from config.prompt import *
import requests
import json
from config import get_configuration
from util.redis_util import add_message_to_redis, get_history_messages
import asyncio
from starlette.requests import ClientDisconnect
card_data = {}

def process_tool_message(content: str, request_id: str, user_id: str):
    global card_data
    if card_data.get(request_id) is None:
        card_data[request_id] = []
    if not content or 'Successfully transferred' in content:
        return
    if 'consumer_data_card' in content:
        card_content_list = []
        try:
            card_content_list = json.loads(content.replace("'", '"'))
        except:
            try:
                card_content_list = json.loads(content)
            except:
                log.info('Application event')
                return
        try:
            if card_content_list:
                for tool_content in card_content_list:
                    if 'consumer_data_card' in tool_content:
                        card = json.dumps(tool_content, ensure_ascii=False)
                        if card not in card_data[request_id]:
                            card_data[request_id].append(card)
                    else:
                        log.info('Application event')
        except:
            log.info('Application event')
            return
    else:
        try:
            tool_content = json.loads(content)
            log.info('Application event')
        except:
            log.info('Application event')

def build_agent_graph(chat_body: ChatBody):
    handler_question = chat_body.question
    endpoint = get_configuration('api', 'operations').get('detection_analysis_url')
    if endpoint:
        try:
            response = requests.post(endpoint, json={"question": chat_body.question}, headers={"Authorization": chat_body.agent_extends.get("token", "")}, timeout=8)
            response.raise_for_status()
            candidate = response.json().get("data")
            if isinstance(candidate, str):
                handler_question = candidate
        except (requests.RequestException, ValueError):
            log.warning("Entity preprocessing unavailable")
    log.info('Application event')
    model = ChatOpenAI(base_url=get_project_client_config(chat_body.product_id, 'base_url'), model=get_project_client_config(chat_body.product_id, 'model'), api_key=get_project_client_config(chat_body.product_id, 'api_key'), temperature=0, extra_body={'chat_template_kwargs': {'enable_thinking': False}}, streaming=True)
    branch_company_agent = create_agent(model=model, tools=[branch_company_info_tool], system_prompt=get_branch_company_prompt())
    sandbox_agent = create_agent(model=model, tools=[sandbox_tool], system_prompt=get_sandbox_prompt())
    business_management_agent = create_agent(model=model, tools=[business_management_tool], system_prompt=get_business_management_prompt())
    performance_report_agent = create_agent(model=model, tools=[performance_report_tool], system_prompt=get_performance_report_prompt())

    @tool
    async def branch_company_event(request: str, config: RunnableConfig) -> str:
        """Branch company event. Route only matching requests to this specialist."""
        result = await branch_company_agent.ainvoke({'messages': [HumanMessage(content=request)]}, config=config)
        return result['messages'][-1].content

    @tool
    async def business_management_event(request: str, config: RunnableConfig) -> str:
        """Business management event. Route only matching requests to this specialist."""
        result = await business_management_agent.ainvoke({'messages': [HumanMessage(content=request)]}, config=config)
        return result['messages'][-1].content

    @tool
    async def sandbox_event(request: str, config: RunnableConfig) -> str:
        """Sandbox event. Route only matching requests to this specialist."""
        result = await sandbox_agent.ainvoke({'messages': [HumanMessage(content=request)]}, config=config)
        return result['messages'][-1].content

    @tool
    async def performance_report_event(request: str, config: RunnableConfig) -> str:
        """Performance report event. Route only matching requests to this specialist."""
        result = await performance_report_agent.ainvoke({'messages': [HumanMessage(content=request)]}, config=config)
        return result['messages'][-1].content
    app = create_agent(model=model, tools=[branch_company_event, business_management_event, sandbox_event, performance_report_event], system_prompt=get_workflow_prompt())
    history_messages = get_history_messages(f"{chat_body.product_id}:{chat_body.user_id}:{chat_body.conversation_id}")
    if history_messages and chat_body.stream:
        log.info('Application event')
        message = {'messages': history_messages + [HumanMessage(content=handler_question)]}
    else:
        message = {'messages': HumanMessage(content=handler_question)}
        history_messages = ''
    return (app, message, str(history_messages))

async def agent_conversation(chat_body: ChatBody):
    user_id = chat_body.user_id
    log.info('Application event')
    app, message, history_messages = await asyncio.to_thread(build_agent_graph, chat_body)
    final_answer = ''
    config = {'configurable': {'thread_id': chat_body.conversation_id, 'agent_extends': chat_body.agent_extends}}
    yield 'stream start'
    try:
        WRAPPER_TOOLS = {'branch_company_event', 'business_management_event', 'sandbox_event', 'performance_report_event'}
        async for event in app.astream_events(message, config=config, version='v2'):
            kind = event['event']
            name = event.get('name', '')
            if kind == 'on_chat_model_stream' and len(event.get('parent_ids', [])) <= 2:
                chunk = event['data']['chunk']
                if chunk.content:
                    final_answer += chunk.content
                    yield generate_yield_json('text', chat_body.request_id, '', '', chunk.content)
            elif kind == 'on_tool_start' and name not in WRAPPER_TOOLS and ('transfer_to' not in name):
                yield generate_yield_json('plugin', chat_body.request_id, res_tool.get(name, name), '', res_tool.get(name, name))
            elif kind == 'on_tool_end' and name not in WRAPPER_TOOLS and ('transfer_to' not in name):
                tool_output = event['data'].get('output')
                content = getattr(tool_output, 'content', None) or str(tool_output)
                process_tool_message(str(content), chat_body.request_id, user_id)
    except (asyncio.CancelledError, ClientDisconnect):
        log.info('Application event')
        if final_answer:
            final_answer += '...'
        else:
            final_answer = '本次内容输出已终止，点击重试再次提问。'
        log.info('Application event')
        log.info('Application event')
    except Exception as e:
        log.info('Application event')
        log.info('Application event')
        final_answer = f'【点击再试一下！】\n有时候大模型会“打个盹”或者超时，分析内容可能暂时没法及时响应^-^。点击下方再试试~'
    try:
        if card_data and card_data.get(chat_body.request_id):
            cards = []
            card_id = None
            for card in card_data.get(chat_body.request_id):
                load_card = json.loads(card)
                if load_card.get('consumer_data_card'):
                    card_id = load_card.get('card_id')
                    cards.append(load_card.get('consumer_data_card'))
            if len(cards) >= 1:
                content = generate_yield_json('card', chat_body.request_id, card_id, '', cards)
                yield content
            else:
                pass
            card_data.pop(chat_body.request_id, None)
        else:
            pass
    except Exception as e:
        log.info('Application event')
    finally:
        card_data.pop(chat_body.request_id, None)
        yield generate_yield_json('text', chat_body.request_id, '', '', ' ')
        yield 'stream end'
    add_message_to_redis(f"{chat_body.product_id}:{chat_body.user_id}:{chat_body.conversation_id}", chat_body.question, final_answer)
    final_answer = final_answer.replace('\n', '')
    log.info('Application event')

def agent_conversation_no_stream(chat_body: ChatBody):
    app, message, history_messages = build_agent_graph(chat_body)
    config = {'configurable': {'thread_id': chat_body.conversation_id, 'agent_extends': chat_body.agent_extends}}
    response = app.invoke(message, config=config)
    final_answer = response['messages'][-1].content
    final_answer = final_answer.replace('\n', '')
    log.info('Application event')
    return response['messages'][-1].content
