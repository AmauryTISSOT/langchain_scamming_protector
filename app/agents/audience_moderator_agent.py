from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

MOD_SYSTEM = """
...
Format STRICT (JSON, sans texte autour):
{{
  "choices": [
    {{"title":"...", "effect":"..."}},
    {{"title":"...", "effect":"..."}},
    {{"title":"...", "effect":"..."}}
  ]
}}
"""


class AudienceModeratorAgent:
    def __init__(self, api_key: str):
        self.llm = ChatGroq(
            api_key=api_key,
            model="llama-3.1-8b-instant",
            temperature=0.4,
            streaming=False
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", MOD_SYSTEM),
            ("human", "Contexte actuel: {context}\nPropositions audience:\n{raw_ideas}\n")
        ])
        self.chain = self.prompt | self.llm

    def pick_three(self, context: str, ideas: list[str]):
        raw_ideas = "\n".join([f"- {x}" for x in ideas])
        resp = self.chain.invoke({"context": context, "raw_ideas": raw_ideas})
        return resp.content
