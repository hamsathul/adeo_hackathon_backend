from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
import logging
import json
from datetime import datetime
from app.core.serpsearch.serpapi import SerperClient

logger = logging.getLogger(__name__)

class ResearchAnalyzer:
   def __init__(self, query: str = None):
       self.query = query
       self.serper_client = SerperClient()
       self.setup_llms()

   def setup_llms(self):
       self.openai = ChatOpenAI(
           model="gpt-3.5-turbo",
       )
       self.gemini = ChatGoogleGenerativeAI(
           model="gemini-pro",
           temperature=0.3
       )

   async def analyze(self) -> dict:
       try:
           # Get search results from Serper
           search_results = await self.serper_client.search(
               query=self.query,
               search_type='search'
           )
           
           analysis_prompt = f"""
           Analyze these search results about {self.query}:
           {json.dumps(search_results)}
           
           Return a JSON with:
           {{
               "topic": "{self.query}",
               "summary": "2-3 sentence overview",
               "key_points": ["main findings"],
               "trends": ["current trends"],
               "sources": ["relevant sources with URLs"]
           }}
           """
           
           analysis = await self.openai.ainvoke(analysis_prompt)
           
           return {
               "analysis": json.loads(analysis.content),
               "raw_search": search_results,
               "metadata": {
                   "timestamp": datetime.utcnow().isoformat(),
                   "query": self.query
               }
           }

       except Exception as e:
           logger.error(f"Analysis failed: {str(e)}")
           raise