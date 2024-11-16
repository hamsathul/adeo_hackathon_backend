# app/core/crewai/crew.py
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from .tools.research import SearchAndContents, FindSimilar, GetContents
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI


@CrewBase
class AIResearchCrew:
    """AI Research crew for analyzing topics"""
    
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    
    def __init__(self, query: str = None):
        self.query = query

    def openAILlm(self):
        return ChatOpenAI(model="gpt-4o-mini")
    def groqLlm(self):
         return ChatGroq(model_name="llama3-groq-70b-8192-tool-use-preview")
    def geminiLlm(self):
        return ChatGoogleGenerativeAI(model="gemini-pro")
    def falconLlm(self):
        AI71_API_KEY = "api71-api-be2f9c56-9f9d-4b63-833a-eafb1be26eee"
        AI71_BASE_URL = "https://api.ai71.ai/v1/"        
        return ChatOpenAI(
		model="tiiuae/falcon-180B-chat",
		api_key=AI71_API_KEY,
		base_url=AI71_BASE_URL,
		streaming=True,
		)
        
    def step_callback(self, agent_output, agent_name):
        print(f"{agent_name}: {agent_output}")
        
    @agent
    def researcher(self) -> Agent:
        return Agent(
            role=self.agents_config["researcher"]["role"],
            goal=self.agents_config["researcher"]["goal"],
            backstory=self.agents_config["researcher"]["backstory"],
            tools=[SearchAndContents(), FindSimilar(), GetContents()],
            verbose=True,
            llm=self.openAILlm(),
            step_callback=lambda step: self.step_callback(step, "Research Agent")
        )
        
    @task
    def research_task(self) -> Task:
        return Task(
            description=f"Research and analyze the following topic: {self.query}. Focus on gathering comprehensive information and identifying key developments.",
            agent=self.researcher(),
            expected_output="Detailed research findings with key insights and relevant information",
            context=[
                {
                    "role": "user",
                    "content": f"Research query: {self.query}",
                    "description": f"Analyze topic: {self.query}",
                    "expected_output": "Comprehensive analysis of the topic"
                }
            ]
        )
        
    @crew
    def get_crew(self) -> Crew:
        """Creates the AI Research crew"""
        return Crew(
            agents=[self.researcher()],
            tasks=[self.research_task()],
            process=Process.sequential,
            verbose=2
        )