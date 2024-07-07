
from langchain.chains import LLMChain
from search import yagpt_request, refactor_sim_search_res
from typing import Any, Dict, Iterator, List, Mapping, Optional
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import GenerationChunk
from langchain.tools import BaseTool
from langchain.prompts import StringPromptTemplate
from langchain.schema import AgentAction, AgentFinish, OutputParserException
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from typing import List, Union
import re


# Класс позволяющий загружать свои модели в оболочку langchain
# По умолчанию в langchain доступны оболочки для моделей openai, мы используем yandexGPT
class CustomLLM(LLM):
    def _call(
            self,
            prompt: str,
            role: str = 'Ты - ассистент, который помогает разработчикам с документацией',
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> str:
        return yagpt_request(prompt, role)

    def _stream(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> Iterator[GenerationChunk]:
        for char in prompt[: self.n]:
            chunk = GenerationChunk(text=char)
            if run_manager:
                run_manager.on_llm_new_token(chunk.text, chunk=chunk)

            yield chunk

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": "CustomChatModel",
        }

    @property
    def _llm_type(self) -> str:
        return "custom"


llm = CustomLLM()


# подгрузка сценариев при которых вызывается конкретный агент
when_need_use_ask = open(r'agents/RuSrore_agent_discription/when_need_use_ask.txt', 'r').readline()
when_need_use_fix_code = open(r'agents/RuSrore_agent_discription/when_need_use_fix_code.txt', 'r').readline()
when_need_use_rag = open(r'agents/RuSrore_agent_discription/when_need_use_rag.txt', 'r').readline()
when_need_use_simplify = open(r'agents/RuSrore_agent_discription/when_need_use_simplify.txt', 'r').readline()
when_need_use_spliter = open(r'agents/RuSrore_agent_discription/when_need_use_spliter.txt', 'r').readline()

# подгрузка промптов с которыми вызывается конкретный агент
when_need_use_ask_prompt = open(r'agents/RuStore_agent_prompt/AddAckerPrompt.txt', 'r').readline()
when_need_use_fix_code_prompt = open(r'agents/RuStore_agent_prompt/FixCodePrompt.txt', 'r').readline()
when_need_use_rag_prompt = open(r'agents/RuStore_agent_prompt/RagFuncPrompt.txt', 'r').readline()
when_need_use_simplify_prompt = open(r'agents/RuStore_agent_prompt/SimplifyPrompt.txt', 'r').readline()
when_need_use_spliter_prompt = open(r'agents/RuStore_agent_prompt/SplitToSimplePrompt.txt', 'r').readline()


# обработка выхода конктреного агента
class RagFuncTool(BaseTool):
    name = "RAG system"
    context = when_need_use_rag_prompt
    description = when_need_use_rag

    def _run(self, query: str, context=context):
        return refactor_sim_search_res(query)


class SplitToSimpleTool(BaseTool):
    name = "Split system"
    context = when_need_use_spliter_prompt
    description = when_need_use_spliter

    def _run(self, query: str, context=context):
        return yagpt_request(query, context)


class AddAckerTool(BaseTool):
    name = "Ask system"
    context = when_need_use_ask_prompt
    description = when_need_use_ask

    def _run(self, query: str, context=context):
        return yagpt_request(query, context)


class SimplifyTool(BaseTool):
    name = "Simple query system"
    context = when_need_use_simplify_prompt
    description = when_need_use_simplify

    def _run(self, query: str, context=context):
        return yagpt_request(query, context)


class FixCodeTool(BaseTool):
    name = "Fix Code system"
    context = when_need_use_fix_code_prompt
    description = when_need_use_fix_code

    def _run(self, query: str, context=context):
        return yagpt_request(query, context)


RagFunc = RagFuncTool()
SplitToSimple = SplitToSimpleTool()
AddAcker = AddAckerTool()
Simplify = SimplifyTool()
FixCode = FixCodeTool()

tools = [
    Tool(name="Search_RAG", func=RagFunc._run, description=when_need_use_rag),
    Tool(name="Spliter", func=SplitToSimple._run, description=when_need_use_spliter),
    # Tool(name='Ask_add', func=AddAcker._run, description=when_need_use_ask),
    Tool(name='simplifier', func=Simplify._run, description=when_need_use_simplify),
    Tool(name='code_fixer', func=FixCode._run, description=when_need_use_fix_code)
]

template = """
Ты являешься ботом, которые помогает отвечать на вопросы по документации. Ответь на следующие вопросы как можно лучше. Если не знаешь, то не нужно ничего придумывать.
У тебя есть доступ к следующим инструментам:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Начинай! Не забудьте говорить вежливо, чётко и ясно, когда будете давать свой окончательный ответ.

Question: {input}
{agent_scratchpad}"""


class CustomPromptTemplate(StringPromptTemplate):
    template: str
    tools: List[Tool]

    def format(self, **kwargs) -> str:
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        return self.template.format(**kwargs)


prompt = CustomPromptTemplate(
    template=template,
    tools=tools,
    input_variables=["input", "intermediate_steps"]
)


# Ответ агентов четко структурирован, что позволяет без проблем разбирать его на части
# И относительно этого происходит вызов следующего агента или выдача ответа пользователю
class CustomOutputParser(AgentOutputParser):

    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            return AgentFinish(
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise OutputParserException(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)


output_parser = CustomOutputParser()
llm_chain = LLMChain(llm=llm, prompt=prompt)

tool_names = [tool.name for tool in tools]
agent = LLMSingleActionAgent(
    llm_chain=llm_chain,
    output_parser=output_parser,
    stop=["\nObservation:"],
    allowed_tools=tool_names
)

agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)


def get_agents_res(query):
    return agent_executor.run(query)
