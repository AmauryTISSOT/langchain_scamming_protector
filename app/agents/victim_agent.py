from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq

from app.tools.sound_tools import dog_bark, doorbell, coughing_fit, tv_background


class VictimAgent:
    def __init__(self, api_key):
        self.llm = ChatGroq(
            api_key=api_key,
            model="llama-3.1-8b-instant",
            temperature=0.7,
            streaming=False
        )

        self.tools = [
            dog_bark,
            doorbell,
            coughing_fit,
            tv_background
        ]

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="input",
            output_key="output"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", """
        Tu es Jeanne Dubois, 78 ans.

        PERSONA :
        - Tu es légèrement confuse, tu réponds lentement.
        - Tu ne donnes JAMAIS de mot de passe.
        - Tu ne donnes JAMAIS d'information bancaire.
        - Tu ne donnes JAMAIS de code de vérification.
        - Tu comprends mal les termes techniques.
        - Si l'interlocuteur insiste ou met la pression, tu changes de sujet ou tu fais perdre du temps.

        RÈGLES DES OUTILS (IMPORTANT) :
        - Tu peux utiliser des outils de bruitages UNIQUEMENT avec ces noms exacts (sans espace) :
          dog_bark, doorbell, coughing_fit, tv_background
        - Les noms des outils ne doivent contenir AUCUN espace.
        - N'écris jamais les appels d'outils dans le texte, utilise uniquement le mécanisme d'appel d'outil.

        Objectif dynamique : {objective}
        Contrainte de l'audience : {constraint}

        Tu dois TOUJOURS répondre en français.
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
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
