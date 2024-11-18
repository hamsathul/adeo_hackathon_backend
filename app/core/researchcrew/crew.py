from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from crewai_tools import SerperDevTool

@CrewBase
class AIResearchCrew:
   def __init__(self, query: str = None):
       self.query = query

   def openAILlm(self):
       return ChatOpenAI(model="gpt-4o-mini", max_tokens=2000)

   def groqLlm(self):
       return ChatGroq(model_name="mixtral-8x7b-32768")

   def geminiLlm(self):
       return ChatGoogleGenerativeAI(model="gemini-pro", max_tokens=2000)

   def falconLlm(self):
       return ChatOpenAI(
           model="tiiuae/falcon-mamba-7b-instruct",
           api_key="api71-api-be2f9c56-9f9d-4b63-833a-eafb1be26eee",
           base_url="https://api.ai71.ai/v1/",
           max_tokens=1000,
           streaming=True
       )

   @agent
   def researcher(self) -> Agent:
       return Agent(
           role="Researcher",
           goal="Quick analysis",
           backstory="Expert analyst",
           tools=[SerperDevTool(n_results=5)],
           llm=self.falconLlm(),
           max_iterations=1
       )

   @task 
   def research_task(self) -> Task:
       return Task(
           description=f"Analyze: {self.query} (250 words max)",
           agent=self.researcher(),
           expected_output="Key findings"
       )

   @crew
   def get_crew(self) -> Crew:
       return Crew(
           agents=[self.researcher()],
           tasks=[self.research_task()],
           process=Process.sequential
       )

   def run(self):
       return self.get_crew().kickoff()