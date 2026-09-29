from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from config.logger import logger as log
from config import get_project_client_config
from model.ChatBody import ChatBody
from util.yield_util import generate_yield_json, res_tool
from tools.branch_company_info_tool import branch_company_info_tool
from tools.business_management_tool import business_management_tool
from tools.performance_report_tool import performance_report_tool
from tools.sandbox_tool import sandbox_tool
from config.prompt import (
    get_branch_company_prompt,
    get_sandbox_prompt,
    get_business_management_prompt,
    get_performance_report_prompt,
    get_workflow_prompt,
)
import requests
import json
from config import get_configuration
from util.redis_util import add_message_to_redis, get_history_messages
import asyncio


def extract_cards(content):
    """Read tool result cards without repairing or interpreting model text."""
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except (ValueError, TypeError):
            return []
    if isinstance(content, list):
        return [card for item in content for card in extract_cards(item)]
    if (
        isinstance(content, dict)
        and isinstance(content.get("card_id"), str)
        and "consumer_data_card" in content
    ):
        return [content]
    return []


def build_agent_graph(chat_body: ChatBody):
    handler_question = chat_body.question
    endpoint = get_configuration("api", "operations").get("detection_analysis_url")
    if endpoint:
        try:
            response = requests.post(
                endpoint,
                json={"question": chat_body.question},
                headers={"Authorization": chat_body.agent_extends.get("token", "")},
                timeout=8,
            )
            response.raise_for_status()
            candidate = response.json().get("data")
            if isinstance(candidate, str):
                handler_question = candidate
        except (requests.RequestException, ValueError):
            log.warning("Entity preprocessing unavailable")
    log.info("Application event")
    model = ChatOpenAI(
        base_url=get_project_client_config(chat_body.product_id, "base_url"),
        model=get_project_client_config(chat_body.product_id, "model"),
        api_key=get_project_client_config(chat_body.product_id, "api_key"),
        temperature=0,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        streaming=True,
        timeout=20,
        max_retries=1,
    )
    branch_company_agent = create_agent(
        model=model,
        tools=[branch_company_info_tool],
        middleware=[ToolCallLimitMiddleware(run_limit=4, exit_behavior="error")],
        system_prompt=get_branch_company_prompt(),
    )
    sandbox_agent = create_agent(
        model=model,
        tools=[sandbox_tool],
        middleware=[ToolCallLimitMiddleware(run_limit=4, exit_behavior="error")],
        system_prompt=get_sandbox_prompt(),
    )
    business_management_agent = create_agent(
        model=model,
        tools=[business_management_tool],
        middleware=[ToolCallLimitMiddleware(run_limit=4, exit_behavior="error")],
        system_prompt=get_business_management_prompt(),
    )
    performance_report_agent = create_agent(
        model=model,
        tools=[performance_report_tool],
        middleware=[ToolCallLimitMiddleware(run_limit=4, exit_behavior="error")],
        system_prompt=get_performance_report_prompt(),
    )

    @tool
    async def branch_company_event(request: str, config: RunnableConfig) -> str:
        """Branch company event. Route only matching requests to this specialist."""
        result = await branch_company_agent.ainvoke(
            {"messages": [HumanMessage(content=request)]}, config=config
        )
        return result["messages"][-1].content

    @tool
    async def business_management_event(request: str, config: RunnableConfig) -> str:
        """Business management event. Route only matching requests to this specialist."""
        result = await business_management_agent.ainvoke(
            {"messages": [HumanMessage(content=request)]}, config=config
        )
        return result["messages"][-1].content

    @tool
    async def sandbox_event(request: str, config: RunnableConfig) -> str:
        """Sandbox event. Route only matching requests to this specialist."""
        result = await sandbox_agent.ainvoke(
            {"messages": [HumanMessage(content=request)]}, config=config
        )
        return result["messages"][-1].content

    @tool
    async def performance_report_event(request: str, config: RunnableConfig) -> str:
        """Performance report event. Route only matching requests to this specialist."""
        result = await performance_report_agent.ainvoke(
            {"messages": [HumanMessage(content=request)]}, config=config
        )
        return result["messages"][-1].content

    app = create_agent(
        model=model,
        tools=[
            branch_company_event,
            business_management_event,
            sandbox_event,
            performance_report_event,
        ],
        middleware=[ToolCallLimitMiddleware(run_limit=4, exit_behavior="error")],
        system_prompt=get_workflow_prompt(),
    )
    history_messages = get_history_messages(
        f"{chat_body.product_id}:{chat_body.user_id}:{chat_body.conversation_id}"
    )
    if history_messages:
        log.info("Application event")
        message = {"messages": history_messages + [HumanMessage(content=handler_question)]}
    else:
        message = {"messages": [HumanMessage(content=handler_question)]}
        history_messages = ""
    return (app, message, str(history_messages))


async def agent_conversation(chat_body: ChatBody):
    app, message, _ = await asyncio.to_thread(build_agent_graph, chat_body)
    config = {
        "configurable": {
            "thread_id": chat_body.session_key,
            "agent_extends": {"token": chat_body.token},
        },
        "recursion_limit": 20,
    }
    final_answer = ""
    cards = []
    yield "stream start"
    wrappers = {
        "branch_company_event",
        "business_management_event",
        "sandbox_event",
        "performance_report_event",
    }
    async for event in app.astream_events(message, config=config, version="v2"):
        kind, name = event["event"], event.get("name", "")
        if kind == "on_chat_model_stream" and len(event.get("parent_ids", [])) <= 2:
            content = event["data"]["chunk"].content
            if isinstance(content, str) and content:
                final_answer += content
                yield generate_yield_json("text", chat_body.request_id, "", "", content)
        elif kind == "on_tool_start" and name not in wrappers:
            yield generate_yield_json(
                "plugin", chat_body.request_id, res_tool.get(name, name), "", "Running tool"
            )
        elif kind == "on_tool_end" and name not in wrappers:
            output = event["data"].get("output")
            for card in extract_cards(getattr(output, "content", output)):
                if card not in cards:
                    cards.append(card)
    for card in cards:
        yield generate_yield_json(
            "card", chat_body.request_id, card["card_id"], "", card["consumer_data_card"]
        )
    await asyncio.to_thread(
        add_message_to_redis, chat_body.session_key, chat_body.question, final_answer
    )
    yield "stream end"


async def agent_conversation_no_stream(chat_body: ChatBody):
    app, message, _ = await asyncio.to_thread(build_agent_graph, chat_body)
    config = {
        "configurable": {
            "thread_id": chat_body.session_key,
            "agent_extends": {"token": chat_body.token},
        },
        "recursion_limit": 20,
    }
    response = await app.ainvoke(message, config=config)
    answer = response["messages"][-1].content
    await asyncio.to_thread(add_message_to_redis, chat_body.session_key, chat_body.question, answer)
    return answer
