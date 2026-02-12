from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq

from app.tools.sound_tools import dog_bark, doorbell, coughing_fit, tv_background


class VictimAgent:
    def __init__(self,api_key):
        self.llm = ChatGroq(
            api_key=api_key,
            model="llama-3.1-8b-instant",
            temperature=0.7
        )

        self.tools = [
            dog_bark,
            doorbell,
            coughing_fit,
            tv_background
        ]

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are Jeanne Dubois, 78 years old.

- Slightly confused.
- Never give passwords.
- Never give banking info.
- Never give verification codes.
- Misunderstand technical terms.
- If pressured, deflect.
- Use sound tools if relevant.

Objective: {objective}
Constraint: {constraint}
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            ("system", "{agent_scratchpad}")
        ])

        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )

    def respond(self, user_input, objective="Respond slowly.", constraint="None"):
        result = self.executor.invoke({
            "input": user_input,
            "objective": objective,
            "constraint": constraint
        })
        return result["output"]

