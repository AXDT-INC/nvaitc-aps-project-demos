# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from fasthtml.common import *
from starlette.responses import RedirectResponse
from starlette.websockets import WebSocketState
from chat_agent import get_agent, get_checkpoint
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from openai import BadRequestError
from dataclasses import dataclass
from datetime import datetime
import textwrap
import shortuuid
import asyncio
import sqlite3
import json
import markdown


# Site Map
# / entry page, redirects to /{uuid} with a fresh uuid
# /{uuid} shows the chat history of chat {uuid}, the uuid is used as thread_id for langgraph
#
# datamodel
# (user) 1-n> (chats) 0-n> (cards / stored in LangGraph db)

# model that will be used for generation of next answer
selected_model = "meta/llama-3.1-405b-instruct"
# list of supported models the user can choose from
models = {
    "meta/llama-3.1-405b-instruct": "NVIDIA NIMs Llama 3.1 405B",
    "meta/llama-3.1-70b-instruct": "NVIDIA NIMs Llama 3.1 70B",
    "meta/llama-3.2-3b-instruct": "NVIDIA NIMs Llama 3.2 3B",
    "deepseek-ai/deepseek-v3.1": "DeepSeek V3.1",
    "qwen/qwen3-next-80b-a3b-instruct": "Qwen3 Next 80B A3B Instruct",
}

# persistent storage of chat sessions
db = database("data/curiosity.db")
chats = db.t.chats
if chats not in db.t:
    chats.create(id=str, title=str, updated=datetime, pk="id")
ChatDTO = chats.dataclass()


# Patch ChatDTO class with ft renderer and ID initialization
@patch
def __ft__(self: ChatDTO):  # type: ignore
    return Li(
        A(
            textwrap.shorten(self.title, width=60, placeholder="..."),
            id=self.id,
            href=f"/chat/{self.id}",
        ),
        dir="ltr",
    )


# FIXME: this patch does not work, requires fixing
@patch
def __post_init__(self: ChatDTO):  # type: ignore
    self.id = shortuuid.uuid()


# default chat for new chats
new_chatDTO = ChatDTO()
new_chatDTO.id = shortuuid.uuid()


@dataclass
class ChatCard:
    question: str
    content: str
    model_id: str = None
    busy: bool = False
    sources: List = None
    images: List = None
    id: str = ""

    def __post_init__(self):
        self.id = shortuuid.uuid()

    def __ft__(self):
        html_content = markdown.markdown(self.content) if not self.busy else ""
        content_div_id = f"content-{self.id}"
        html_json = json.dumps(html_content) if html_content else '""'
        content_elements = (
            Progress()
            if self.busy
            else (
                Div(
                    id=content_div_id,
                    cls="markdown-content",
                    **{"data-html": html_json} if html_content else {}
                ),
                Script(f"""
                    (function() {{
                        function renderMarkdown() {{
                            var div = document.getElementById('{content_div_id}');
                            if (div && div.dataset.html) {{
                                try {{
                                    var html = JSON.parse(div.dataset.html);
                                    div.innerHTML = html;
                                }} catch(e) {{
                                    console.error('Error rendering markdown:', e);
                                }}
                            }}
                        }}
                        // Try immediately
                        renderMarkdown();
                        // Also try after a short delay for dynamically inserted content
                        setTimeout(renderMarkdown, 100);
                    }})();
                """)
            )
        )
        return Card(
            content_elements,
            (
                Grid(*[A(Img(src=image), href=image) for image in self.images])
                if self.images and len(self.images) > 0
                else None
            ),
            id=self.id,
            header=Div(
                Strong(self.question), Small(self.model_id, cls="pico-color-grey-200")
            ),
            footer=(
                None
                if self.sources == None
                else Grid(
                    *[
                        Div(A(search_result["title"], href=search_result["url"]))
                        for search_result in self.sources
                    ]
                )
            ),
        )


# FastHTML includes the "HTMX" and "Surreal" libraries in headers, unless you pass `default_hdrs=False`.
app, rt = fast_app(
    live=True,  # type: ignore
    default_hdrs=False,  # Disable default headers to manually load HTMX
    hdrs=(
        Script(src="https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js"),
        Script(src="https://unpkg.com/htmx.org@1.9.10/dist/ext/ws.js"),
        picolink,
        Link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.colors.min.css",
            type="text/css",
        ),
        Meta(name="color-scheme", content="light dark"),
        MarkdownJS(),
    ),
)


def navigation():
    navigation = Nav(
        Ul(Li(Hgroup(H3("Explorer AI: Curiosity-Driven Agents"), P("Search powered by Tavily | Running on NVIDIA NIMs")))),
        Ul(
            Li(
                Button(
                    "New chat",
                    cls="secondary",
                    onclick=f"window.location.href='/chat/{new_chatDTO.id}'",
                )
            ),
            Li(model_selector()),
            Li(question_list()),
            Li(clear_chathistory()),
        ),
    )
    return navigation

def has_no_answers(chat_id: str):
    # This function checks if there are no answers in the answer_list
    answer_div = answer_list(chat_id)
    return len(answer_div.children) == 0 if hasattr(answer_div, 'children') else True

def question(chat_id: str):
    # Check if there are no answers
    show_p = has_no_answers(chat_id)
    # Define the P component
    p_component = P("Explorer AI: Curiosity-Driven Agents is a project focused on creating interactive agents using large language models (LLMs) within a ReAct architecture. It allows users to interact with models running on NVIDIA NIMs like Llama 3.1 while incorporating search tools to enhance response generation. The project emphasizes modularity, enabling seamless swapping between LLMs and tool-augmented interactions, all within a web-based interface powered by technologies like LangGraph and FastHTML. Its goal is to experiment with agent-based AI systems, offering a dynamic platform for exploring AI-driven conversational agents.", id="p-component") if show_p else None
    question_div = Div(
        Search(
            Group(
                Input(
                    id="new-question",
                    name="question",
                    autofocus=True,
                    placeholder="Ask your question here...",
                    autocomplete="off",
                ),
                Button("Answer", id="answer-btn", cls="hidden-default", onclick="hidePComponent()"),
            ),
            hx_post=f"/chat/{chat_id}",
            target_id="answer-list",
            hx_swap="afterbegin",
            id="search-group",
        ),
        P("\n"), p_component,
    )

    script = Script("""
      function hidePComponent() {
        var pComponent = document.getElementById('p-component');
        if (pComponent) {
          pComponent.style.display = 'none';
        }
      }
    """)

    return Div(question_div, script)

@app.get("/clear_chathistory")
async def clear_chathistory():
    # Connect to the database
    conn = sqlite3.connect("data/curiosity.db")
    cursor = conn.cursor()

    # SQL command to delete all records from the chats table
    delete_query = "DELETE FROM chats"

    # Execute the delete command
    cursor.execute(delete_query)

    # Commit the changes
    conn.commit()

    # Close the connection
    conn.close()

    return RedirectResponse(url=f"/chat/{new_chatDTO.id}")

def clear_chathistory():
    return Button(
                    "Clear all history",
                    cls="secondary",
                    onclick="window.location.href='/clear_chathistory';",
                )


def question_list():
    return Details(
        Summary("Your last 25 chats"),
        Ul(*chats(order_by="updated DESC", limit=25), dir="rtl"),
        id="question-list",
        cls="dropdown",
        hx_swap_oob="true",
    )


def answer_list(chat_id: str):
    # restore message histroy for current thread
    checkpoint = get_checkpoint(chat_id)
    if checkpoint != None:
        top = None
        content = None
        model_id = None
        sources = None
        images = None
        old_messages = []
        for msg in checkpoint["channel_values"]["messages"]:
            if isinstance(msg, HumanMessage):
                if top != None and content != None:
                    old_messages.append(
                        ChatCard(
                            question=top,
                            content=content,
                            model_id=model_id,
                            sources=sources,
                            images=images,
                        )
                    )
                    top, content, model_id, sources, images = (
                        None,
                        None,
                        None,
                        None,
                        None,
                    )
                top = msg.content
            elif isinstance(msg, AIMessage):
                if "tool_calls" in msg.additional_kwargs:
                    # this is an AIMessage with tool calls. skip
                    continue
                else:
                    content = msg.content
                    model_id = msg.response_metadata["model_name"]
            elif isinstance(msg, ToolMessage) and "results" in msg.artifact:
                sources = msg.artifact["results"]
                images = msg.artifact["images"]
        if top != None and content != None:
            old_messages.append(
                ChatCard(
                    question=top,
                    content=content,
                    model_id=model_id,
                    sources=sources,
                    images=images,
                )
            )
        old_messages.reverse()
        answer_list = Div(*old_messages, id="answer-list")
    else:
        # no previous interaction, so show empty list
        answer_list = Div(id="answer-list")
    return answer_list


def model_selector():
    return Details(
        Summary("Model"),
        Ul(
            *[
                Li(
                    Label(
                        title,
                        Input(
                            name="model",
                            type="radio",
                            value=key,
                            **{"checked": key == selected_model},
                            hx_target="#model",
                            hx_swap="outerHTML",
                            hx_get="/model",
                        ),
                    ),
                    dir="ltr",
                )
                for key, title in models.items()
            ],
            dir="rtl",
        ),
        id="model",
        cls="dropdown",
    )


@rt("/model")
async def get(model: str):
    global selected_model
    if model in models.keys():
        selected_model = model
    return model_selector()


@rt("/")
async def get():
    return RedirectResponse(url=f"/chat/{new_chatDTO.id}")


@rt("/chat/{id}")
async def get(id: str):
    try:
        if id == new_chatDTO.id:
            chat = new_chatDTO
        else:
            chat = chats[id]
    except NotFoundError:
        # TODO need to rewrite URL if id != new_ChatDTO.id
        chat = new_chatDTO

    body = Body(
        Header(navigation()),
        Main(question(chat.id), cls="page-dropdown"),
        Footer(answer_list(chat.id)),
        #Script(src="/static/minimal-theme-switcher.js"),
        cls="container",
        hx_ext="ws",
        ws_connect="/ws_connect",
        
    )

    # Define the CSS for vertical centering
    css_style = Style("""
    .container {
        display: flex;
        flex-direction: column;
        justify-content: center; /* Centers vertically */
        min-height: 100vh; /* Minimum height of full viewport */
        box-sizing: border-box;
    }
    .markdown-content {
        line-height: 1.6;
    }
    .markdown-content h1, .markdown-content h2, .markdown-content h3 {
        margin-top: 1em;
        margin-bottom: 0.5em;
    }
    .markdown-content ul, .markdown-content ol {
        margin-left: 1.5em;
        margin-bottom: 1em;
    }
    .markdown-content p {
        margin-bottom: 1em;
    }
    .markdown-content strong {
        font-weight: bold;
    }
    """)
    return Title("Explore!"), css_style, body


# WebSocket connection bookkeeping
ws_connections = {}


async def on_connect(send):
    ws_connections[send.args[0].client] = send
    print(f"WS    connect: {send.args[0].client}, total open: {len(ws_connections)}")


async def on_disconnect(send):
    global ws_connections
    ws_connections = {
        key: value
        for key, value in ws_connections.items()
        if send.args[0].client_state == WebSocketState.CONNECTED
    }
    print(f"WS disconnect: {send.args[0].client}, total open: {len(ws_connections)}")


@app.ws("/ws_connect", conn=on_connect, disconn=on_disconnect)
async def ws(msg: str, send):
    pass


async def update_chat(model: str, card: Card, chat: Any, cleared_inpput, busy_button):
    inputs = {"messages": [("user", card.question)]}    # question is set as the inputs
    config = {"configurable": {"thread_id": chat.id}}   # configuring the chat history
    try:
        result = get_agent(model).invoke(inputs, config)
        print(f"{model} returned result.")
        
        # Print raw Tavily output for all ToolMessages
        for msg in result["messages"]:
            if isinstance(msg, ToolMessage) and "results" in msg.artifact:
                print("\n" + "="*80)
                print("TAVILY RAW OUTPUT:")
                print("="*80)
                print(json.dumps(msg.artifact, indent=2, ensure_ascii=False))
                print("="*80 + "\n")
        
        if (len(result["messages"]) >= 2) and (
            isinstance(result["messages"][-2], ToolMessage)
        ):
            tmsg = result["messages"][-2]
            card.sources = tmsg.artifact["results"]
            card.images = tmsg.artifact["images"]
        card.content = result["messages"][-1].content
        print(card.content)
        chats.upsert(chat) # Updating or inserting chat object (depending if id already exists)
        success = True
    except BadRequestError as e:
        # e = "some error"
        print(f"Exception while calling LLM: {e}")
        card.content = (
            f"Sorry, due to some technical issue no response could be generated: \n{e}"
        )
        success = False
    except Exception as e:
        print(f"Unhandled exception while calling LLM: {e}")
        card.content = (
            f"Sorry, an unexpected error occurred while contacting the model.\n{e}"
        )
        success = False

    card.model_id = model
    card.busy = False
    cleared_inpput.disabled = False
    busy_button.disabled = False
    for send in ws_connections.values():
        try:
            await send(card)
            await send(cleared_inpput)
            await send(busy_button)
            if success:
                await send(question_list())
        except Exception as e:
            print(f"Error sending WebSocket update: {e}")
            import traceback
            traceback.print_exc()
    return success

chat_success = False

@threaded
def generate_chat(model: str, card: Card, chat: Any, cleared_inpput, busy_button):
    try:
        chat.title = card.question if chat.title == None else chat.title
        chat.updated = datetime.now()
        success = asyncio.run(update_chat(model, card, chat, cleared_inpput, busy_button))
        if success:
            chat_success = True
            global new_chatDTO
            if chat is new_chatDTO:
                new_chatDTO = ChatDTO()
                new_chatDTO.id = shortuuid.uuid()
    except Exception as e:
        print(f"Error in generate_chat thread: {e}")
        import traceback
        traceback.print_exc()
        # Update card with error message
        card.busy = False
        card.content = f"Unexpected error occurred: {str(e)}"
        card.model_id = model
        cleared_inpput.disabled = False
        busy_button.disabled = False
        # Try to send error via WebSocket using asyncio.run
        async def send_error_updates():
            try:
                for send in ws_connections.values():
                    await send(card)
                    await send(cleared_inpput)
                    await send(busy_button)
            except Exception as ws_error:
                print(f"Error sending error message via WebSocket: {ws_error}")
        try:
            asyncio.run(send_error_updates())
        except Exception as run_error:
            print(f"Error running async error update: {run_error}")


@rt("/chat/{id}")
async def post(question: str, id: str):
    try:
        if id == new_chatDTO.id:
            chat = new_chatDTO
        else:
            chat = chats[id]
    except NotFoundError:
        # TODO need to rewrite URL if id != new_ChatDTO.id
        chat = new_chatDTO

    card = ChatCard(question=question, content="", busy=True)
    cleared_inpput = Input(
        id="new-question",
        name="question",
        autofocus=True,
        placeholder="Ask your question here...",
        autocomplete="off",
        disabled=True,
        hx_swap_oob="true",
    )
    busy_button = Button(
        "Answer",
        id="answer-btn",
        cls="hidden-default",
        disabled=True,
        hx_swap_oob="true",
    )

    # Validate model and API key before starting thread
    try:
        # This will raise RuntimeError if NVIDIA_API_KEY is not set
        get_agent(selected_model)
    except RuntimeError as e:
        # API key missing or other configuration error
        card.busy = False
        card.content = f"Configuration Error: {str(e)}\n\nPlease ensure you have a .env file with NVIDIA_API_KEY set."
        cleared_inpput.disabled = False
        busy_button.disabled = False
        return card, cleared_inpput, busy_button
    except Exception as e:
        # Other error during agent initialization
        card.busy = False
        card.content = f"Error initializing agent: {str(e)}"
        cleared_inpput.disabled = False
        busy_button.disabled = False
        return card, cleared_inpput, busy_button

    # call response generation in seperate Thread
    try:
        generate_chat(selected_model, card, chat, cleared_inpput, busy_button)
    except Exception as e:
        # Error starting the thread
        print(f"Error starting chat generation thread: {e}")
        import traceback
        traceback.print_exc()
        card.busy = False
        card.content = f"Error starting chat generation: {str(e)}"
        cleared_inpput.disabled = False
        busy_button.disabled = False
        return card, cleared_inpput, busy_button

    return card, cleared_inpput, busy_button


def main():
    print("preparing html server")
    serve()


if __name__ == "__main__":
    main()
