from typing import Any
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langchain.messages import HumanMessage, AIMessage
from util.card_util import set_request_id, pop_cards
from langchain.tools import tool, ToolRuntime
from tools.choose_fund_tool import choose_fund_tool
from tools.query_fund_info_tool import query_fund_info_tool
from tools.query_manager_info import query_manager_info_tool
from tools.choose_manager_tool import choose_manager_tool
from tools.compare_fund_tool import compare_funds_tool
from tools.query_company_tool import query_company_info_tool
from tools.choose_company_tool import choose_company_tool
from config.prompt import *
import json
import re
from util.redis_util import add_message_to_redis, get_history_messages
from config.logger import logger as log
from config import get_project_client_config
from model.ChatBody import ChatBody
from util.yield_util import generate_yield_json, res_tool
from agent.entity_recognizer import recognize_and_query_entities
from model.exceptions import EntityConflictError, TokenInvalidError
from langchain.agents.middleware import ToolCallLimitMiddleware
_model_cache: dict[str, ChatDeepSeek] = {}
_agent_cache: dict[str, Any] = {}

def _get_cached_model(product_id: str, streaming: bool=True) -> ChatDeepSeek:
    cache_key = f'{product_id}_streaming_{streaming}'
    if cache_key not in _model_cache:
        _model_cache[cache_key] = ChatDeepSeek(base_url=get_project_client_config(product_id, 'base_url'), model=get_project_client_config(product_id, 'model'), api_key=get_project_client_config(product_id, 'api_key'), max_retries=5, temperature=0, streaming=streaming, model_kwargs={'parallel_tool_calls': True}, extra_body={'thinking': {'type': 'disabled', 'budget_tokens': 2048}})
    return _model_cache[cache_key]

async def build_agent_graph(chat_body: ChatBody):
    handler_question = f'{chat_body.question}\n提示：当前user_code(用户账号)为{chat_body.user_id}; 请用中文'
    try:
        entities_with_codes = await recognize_and_query_entities(chat_body, chat_body.question)
        if entities_with_codes:
            log.info('Application event')
            handler_question = f'{chat_body.question}\n提示：{entities_with_codes}。当前user_code(用户账号)为{chat_body.user_id}'
            log.info('Application event')
        else:
            log.info('Application event')
    except EntityConflictError as e:
        log.error('Application event')
        raise e
    except TokenInvalidError as e:
        log.error('Application event')
        raise e
    except Exception as e:
        log.error('Application event')
    model = _get_cached_model(chat_body.product_id, streaming=True)
    fund_tools = [query_fund_info_tool, choose_fund_tool, compare_funds_tool]
    mng_tools = [query_manager_info_tool, choose_manager_tool]
    org_tools = [query_company_info_tool, choose_company_tool]
    fund_agent_key = f'fund_agent_{chat_body.product_id}'
    if fund_agent_key not in _agent_cache:
        _agent_cache[fund_agent_key] = create_agent(model=model, tools=fund_tools, middleware=[ToolCallLimitMiddleware(thread_limit=6, run_limit=3, exit_behavior='continue')], system_prompt=get_fund_agent_prompt())
    mng_agent_key = f'mng_agent_{chat_body.product_id}'
    if mng_agent_key not in _agent_cache:
        _agent_cache[mng_agent_key] = create_agent(model=model, tools=mng_tools, middleware=[ToolCallLimitMiddleware(thread_limit=6, run_limit=3, exit_behavior='continue')], system_prompt=get_mng_agent_prompt())
    org_agent_key = f'org_agent_{chat_body.product_id}'
    if org_agent_key not in _agent_cache:
        _agent_cache[org_agent_key] = create_agent(model=model, tools=org_tools, middleware=[ToolCallLimitMiddleware(thread_limit=6, run_limit=3, exit_behavior='continue')], system_prompt=get_company_agent_prompt())
    fund_agent = _agent_cache[fund_agent_key]
    mng_agent = _agent_cache[mng_agent_key]
    org_agent = _agent_cache[org_agent_key]

    @tool
    async def fund_event(request: str, runtime: ToolRuntime) -> str:
        """Fund event. Route only matching requests to this specialist."""
        original_user_message = next((message for message in runtime.state['messages'] if message.type == 'human'))
        prompt = f'You are assisting with the following user inquiry:\n\n{original_user_message.text}\n\nYou are tasked with the following sub-request:\n\n{request}'
        result = await fund_agent.ainvoke({'messages': [{'role': 'user', 'content': prompt}]})
        last_msg = result['messages'][-1]
        final_message = last_msg.text or last_msg.additional_kwargs.get('reasoning_content', '')
        return f'[内部执行结果-BEGIN]\n{final_message}\n[内部执行结果-END]'

    @tool
    async def mng_event(request: str, runtime: ToolRuntime) -> str:
        """Mng event. Route only matching requests to this specialist."""
        original_user_message = next((message for message in runtime.state['messages'] if message.type == 'human'))
        prompt = f'You are assisting with the following user inquiry:\n\n{original_user_message.text}\n\nYou are tasked with the following sub-request:\n\n{request}'
        result = await mng_agent.ainvoke({'messages': [{'role': 'user', 'content': prompt}]})
        last_msg = result['messages'][-1]
        final_message = last_msg.text or last_msg.additional_kwargs.get('reasoning_content', '')
        return f'[内部执行结果-BEGIN]\n{final_message}\n[内部执行结果-END]'

    @tool
    async def org_event(request: str, runtime: ToolRuntime) -> str:
        """Org event. Route only matching requests to this specialist."""
        original_user_message = next((message for message in runtime.state['messages'] if message.type == 'human'))
        prompt = f'You are assisting with the following user inquiry:\n\n{original_user_message.text}\n\nYou are tasked with the following sub-request:\n\n{request}'
        result = await org_agent.ainvoke({'messages': [{'role': 'user', 'content': prompt}]})
        last_msg = result['messages'][-1]
        final_message = last_msg.text or last_msg.additional_kwargs.get('reasoning_content', '')
        return f'[内部执行结果-BEGIN]\n{final_message}\n[内部执行结果-END]'
    supervisor_agent = create_agent(model, tools=[fund_event, mng_event, org_event], middleware=[ToolCallLimitMiddleware(thread_limit=8, run_limit=3, exit_behavior='continue')], system_prompt=get_workflow_prompt())
    app = supervisor_agent
    try:
        history_messages = await get_history_messages(f"{chat_body.product_id}:{chat_body.user_id}:{chat_body.conversation_id}")
        if history_messages:
            log.info('Application event')
            initial_message = HumanMessage(content=history_messages + ',' + 'human:' + handler_question)
        else:
            initial_message = HumanMessage(content=handler_question)
    except Exception as e:
        log.error('Application event')
        initial_message = HumanMessage(content=handler_question)
        history_messages = []
    message = {'messages': [initial_message]}
    return (app, message, history_messages)

async def agent_conversation(chat_body: ChatBody):
    try:
        app, message, _ = await build_agent_graph(chat_body)
        log.info('Application event')
        final_answer = ''
        is_answering = False
        is_first_answer = True
        tool_call_count: dict[str, int] = {}
        yield 'stream start'
        set_request_id(chat_body.request_id)
        try:
            yield (await generate_yield_json('plugin', chat_body.request_id, '开始分析用户问题', '', ''))
            async for event in app.astream_events(message, version='v2'):
                kind = event['event']
                if kind == 'on_chat_model_stream' and len(event.get('parent_ids', [])) <= 2:
                    chunk = event['data']['chunk']
                    reasoning_content = chunk.additional_kwargs.get('reasoning_content', '')
                    if reasoning_content and (not is_answering):
                        reasoning_content = re.sub('[a-zA-Z]', '', reasoning_content)
                        yield (await generate_yield_json('thinking', chat_body.request_id, '', '', reasoning_content))
                    chunk_content = chunk.content
                    if chunk_content:
                        if is_first_answer:
                            is_first_answer = False
                            yield (await generate_yield_json('plugin', chat_body.request_id, '开始输出最终答案', '', ''))
                        final_answer += chunk_content
                        is_answering = True
                        yield (await generate_yield_json('text', chat_body.request_id, '', '', chunk_content))
                elif kind == 'on_tool_start' and event['name'] not in ['fund_event', 'customer_event', 'mng_event', 'org_event']:
                    tool_name = event['name']
                    tool_args = event['data']['input']
                    log.info('Application event')
                    if tool_name == 'query_fund_info_tool':
                        feature = tool_args.get('feature', '')
                        counter_key = f'{tool_name}_{feature}'
                        tool_call_count[counter_key] = tool_call_count.get(counter_key, 0) + 1
                        count = tool_call_count[counter_key]
                        if feature == '基本信息':
                            yield (await generate_yield_json('plugin', chat_body.request_id, f'第{count}次获取基金基本信息', '', ''))
                        elif feature == '业绩信息':
                            yield (await generate_yield_json('plugin', chat_body.request_id, f'第{count}次获取基金业绩信息', '', ''))
                        elif feature == '持仓信息':
                            yield (await generate_yield_json('plugin', chat_body.request_id, f'第{count}次获取基金持仓信息', '', ''))
                    else:
                        tool_call_count[tool_name] = tool_call_count.get(tool_name, 0) + 1
                        count = tool_call_count[tool_name]
                        yield (await generate_yield_json('plugin', chat_body.request_id, f'第{count}次{res_tool[tool_name]}', '', ''))
        except TokenInvalidError as e:
            log.error('Application event')
            raise e
        except Exception as e:
            log.error('Application event')
            raise e
        finally:
            card_strings = pop_cards(chat_body.request_id)
        if card_strings:
            cards = []
            for card_str in card_strings:
                try:
                    card_json = json.loads(card_str)
                    if 'consumer_data_card' in card_json:
                        cards.append(card_json)
                except Exception as e:
                    log.error('Application event')
            if len(cards) >= 1:
                for card in cards:
                    content = await generate_yield_json('card', chat_body.request_id, card['card_id'], '', card['consumer_data_card'])
                    yield content
        yield 'stream end'
        final_answer = final_answer.replace('\n', '')
        log.info('Application event')
        await add_message_to_redis(f"{chat_body.product_id}:{chat_body.user_id}:{chat_body.conversation_id}", chat_body.question, final_answer)
    except EntityConflictError as e:
        log.error('Application event')
        error_message = str(e)
        response_content = await generate_yield_json('text', chat_body.request_id, '', '', error_message)
        yield response_content
        await add_message_to_redis(f"{chat_body.product_id}:{chat_body.user_id}:{chat_body.conversation_id}", chat_body.question, error_message)
        return
    except TokenInvalidError as e:
        log.error('Application event')
        error_msg = f'{{"code": "10000013", "msg": "{str(e)}"}}'
        yield (await generate_yield_json('text', chat_body.request_id, '', '', error_msg))
        yield 'stream end'
        return
    except Exception as e:
        log.error('Application event')
        yield (await generate_yield_json('text', chat_body.request_id, '', '', '服务开小差了，请稍后再试'))
        yield 'stream end'
        return

async def agent_conversation_no_stream(chat_body: ChatBody):
    try:
        app, message, _ = await build_agent_graph(chat_body)
        final_state = await app.ainvoke(message)
        messages = final_state['messages']
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and (not msg.tool_calls):
                final_answer = msg.content
                break
        else:
            final_answer = messages[-1].content if messages else '暂无法获取到信息，请联系我的开发团队处理'
        final_answer_clean = final_answer.replace('\n', '')
        log.info('Application event')
        await add_message_to_redis(f"{chat_body.product_id}:{chat_body.user_id}:{chat_body.conversation_id}", chat_body.question, final_answer_clean)
        return final_answer_clean
    except EntityConflictError as e:
        log.error('Application event')
        error_message = str(e)
        await add_message_to_redis(f"{chat_body.product_id}:{chat_body.user_id}:{chat_body.conversation_id}", chat_body.question, error_message)
        return error_message
