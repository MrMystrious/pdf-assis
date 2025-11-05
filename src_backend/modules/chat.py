from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from typing import TypedDict,Annotated,List,Tuple
import os

class State(TypedDict):
    messages : Annotated[list,add_messages]

class Chat:
    def __init__(self,model="qwen2.5:7b",temp=0.7,sys=None,use_components=False):
        self.llm =  ChatOllama(model=model,temperature=temp)
        self.sys_text = sys
        self._build_graph = StateGraph(State)
        self.graph =None
        self.use_components = use_components
        self.state = {
            "messages": [
                {
                    "role": "system",
                    "content": sys or "You are an intelligent PDF assistant designed to help users understand, analyze, and summarize documents.Your primary goals are:1. **Question Answering** – Accurately answer user questions based on the content extracted from the PDF.  - Always rely on the provided document context.  - If the answer cannot be found in the document, respond with: “The document does not contain enough information to answer that question.” followed by answer from your own knowedge - When relevant, quote or paraphrase short snippets from the PDF to support your answer.2. **Summarization** – Provide concise and meaningful summaries.    - When asked to summarize, produce a structured overview highlighting key points, sections, and insights.    - For long PDFs, summarize section-wise or chapter-wise if the headings are available.3. **Context Understanding** – If multiple PDF chunks or pages are given, consider all of them while answering. Maintain coherence across sections.4. **Response Format** –     - Be clear, factual, and concise.     - Use markdown for readability (headings, bullet points, etc.).    - Avoid hallucination or adding information not supported by the PDF.  Behavior rules:- You never guess; if unsure, state that clearly.- You can handle both general summaries and detailed analytical questions.- When the user asks “What is this document about?”, generate a high-level summary capturing its main intent and topics.Your personality: professional, explanatory, and focused on precision. Always remember to answer question precisely also only expand the your answer if the user asks in his query the query of the user starts in between <query></query>"

                }
            ]
        }

    def chat_node(self,state:State):
        user_msgs = state["messages"]
        response = self.llm.invoke(user_msgs)
        return {"messages":[response]}
    
    def build_graph(self,nodes:List[Tuple[str,callable]]):
        if not nodes:
            raise ValueError("Nodes can not be empty")
        for node_txt,node in nodes:
            self._build_graph.add_node(node_txt,node)
        self._build_graph.add_edge(START,nodes[0][0])
        
        for i in range(1,len(nodes)):
            self._build_graph.add_edge(nodes[i-1][0],nodes[i][0])
        self._build_graph.add_edge(nodes[-1][0],END)
        self.graph = self._build_graph.compile()
    
    def getResult(self, user_input: str):
        if not user_input.strip():
            yield "[Empty input]"
            return

        self.state["messages"].append({
            "role": "user",
            "content": user_input
        })

        res = []
        last_output = ""

        try:
            if not self.use_components:
                for chunk in self.llm.stream(self.state["messages"]):
                    if hasattr(chunk, "content") and chunk.content:
                        res.append(chunk.content)
                        yield chunk.content
                    elif isinstance(chunk, dict) and "content" in chunk:
                        res.append(chunk["content"])
                        yield chunk["content"]

            else:
                for chunk in self.llm.stream(self.state):
                    if "chat" not in chunk:
                        continue

                    messages = chunk.get("chat", {}).get("messages", [])
                    if not messages:
                        continue

                    last_msg = messages[-1]
                    if hasattr(last_msg, "content") and last_msg.content:
                        delta = last_msg.content[len(last_output):]
                        last_output = last_msg.content
                        res.append(delta)
                        yield delta
                    elif isinstance(last_msg, dict) and last_msg.get("content"):
                        delta = last_msg["content"][len(last_output):]
                        last_output = last_msg["content"]
                        res.append(delta)
                        yield delta

        except Exception as e:
            yield f"[Error while streaming response: {str(e)}]"

        self.state["messages"].append({
            "role": "assistant",
            "content": "".join(res)
        })

    
    """ def getResult(self, user_input: str):
        if not user_input.strip():
            yield "[Empty input]"
            return

        conv_his = self.state["messages"][:]
        conv_his.append({"role": "user", "content": user_input})
        res = []
        curr_state = {"messages": conv_his}
        last_output = ""
        try:
            if not self.use_components:
                for chunk in self.llm.stream(conv_his):
                    if hasattr(chunk, "content") and chunk.content:
                        res.append(chunk.content)
                        yield chunk.content
                    elif isinstance(chunk, dict) and "content" in chunk:
                        res.append(chunk["content"])
                        yield chunk["content"]
            else:
                for chunk in self.llm.stream(curr_state):
                    if "chat" not in chunk:
                        continue
                    # Each chunk is an incremental update (state)
                    messages = chunk.get("chat", []).get('messages','')
                # print(messages)
                    if not messages:
                        continue

                    last_msg = messages[-1]

                    if hasattr(last_msg, "content") and last_msg.content:
                        delta = last_msg.content[len(last_output):]
                        last_output = last_msg.content
                        res.append(delta)
                        yield delta  
                    elif isinstance(last_msg, dict) and last_msg.get("content"):
                        delta = last_msg["content"][len(last_output):]
                        last_output = last_msg["content"]
                        res.append(delta)
                        yield delta 

        except Exception as e:
            yield f"[Error while streaming response: {str(e)}]"

        curr_state["messages"].append({
            "role": "assistant",
            "content": "".join(res)
        })
        self.state = curr_state
        #print(curr_state)
 """
        

        
""" chat = Chat(sys="you are assistant")
chat.build_graph([('chat',chat.chat_node)])

for ch in chat.getResult("Hello..."):
    print(ch,end='',flush=True)
print()
for ch in chat.getResult("How are you..."):
    print(ch,end='',flush=True)
print()
for ch in chat.getResult("What is the previous question which i have asked before?"):
    print(ch,end='',flush=True) """