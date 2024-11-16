from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from langchain_google_genai import ChatGoogleGenerativeAI
from functools import lru_cache

@CrewBase
class GoogleSearchCrew():
    def __init__(self, query: str = None, n_results: int = 5):
        self.query = query
        self.n_results = n_results
        self._search_cache = {}

    def geminiLlm(self):
        return ChatGoogleGenerativeAI(model="gemini-1.5-pro")

    def step_callback(self, agent_output, agent_name):
        print(f"{agent_name}: {agent_output}")

    @lru_cache(maxsize=100)
    def cached_search(self, search_query: str) -> dict:
        """Cache search results to reduce API calls"""
        if search_query in self._search_cache:
            return self._search_cache[search_query]
        
        try:
            tool = SerperDevTool(n_results=self.n_results)
            results = tool._run(search_query)  # Changed from search to _run
            self._search_cache[search_query] = results
            return results
        except Exception as e:
            print(f"Search error: {str(e)}")
            return {"error": str(e)}

    class CachedSerperTool(SerperDevTool):
        def __init__(self, search_func, n_results: int = 5):
            super().__init__(n_results=n_results)
            self._search_func = search_func

        def _run(self, search_query: str) -> str:
            return self._search_func(search_query=search_query)

    @agent
    def researcher(self) -> Agent:
        return Agent(
            role="Research Specialist",
            goal=f"Gather comprehensive information about {self.query} including latest news, trends, and developments",
            backstory="You're an expert researcher with a talent for finding the most relevant and up-to-date information online. You excel at discovering current trends and recent developments.",
            verbose=True,
            tools=[self.CachedSerperTool(
                search_func=self.cached_search,
                n_results=self.n_results
            )],
            llm=self.geminiLlm(),
            step_callback=lambda step: self.step_callback(step, "Research Agent")
        )

    @agent
    def analyzer(self) -> Agent:
        return Agent(
            role="Data Analyzer",
            goal="Analyze research findings and organize them into a structured JSON format",
            backstory="You're a data analyst skilled in organizing information into clear, structured formats. You excel at identifying key themes, trends, and creating concise summaries.",
            verbose=True,
            llm=self.geminiLlm(),
            step_callback=lambda step: self.step_callback(step, "Analysis Agent")
        )

    @task
    def research_task(self) -> Task:
        # Perform initial search and cache results
        initial_results = self.cached_search(search_query=self.query)
        
        return Task(
            description=f"""
            Research the following topic thoroughly: {self.query}
            
            Focus on:
            1. Latest developments and news
            2. Current trends
            3. Key information and facts
            4. Recent articles and sources
            5. Related topics and keywords
            
            Use the cached search results to avoid duplicate API calls.
            Collect as much relevant information as possible for analysis.
            """,
            agent=self.researcher(),
            expected_output="Comprehensive research findings including latest news, trends, and key information"
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            description=f"""
            Analyze the research findings about {self.query} and organize them into a JSON format with the following structure:

            {{
                "topic": "{self.query}",
                "description": "Brief overview of the topic (2-3 sentences)",
                "keywords": ["list", "of", "relevant", "keywords"],
                "latest_news": [
                    {{
                        "title": "Article title",
                        "source": "Source name",
                        "date": "Publication date",
                        "url": "Article URL",
                        "summary": "Brief summary"
                    }}
                    // Total 5 articles maximum
                ],
                "trends": [
                    {{
                        "trend_name": "Name of trend",
                        "description": "Brief description of the trend"
                    }}
                ]
            }}

            Use only the information already gathered in the research phase.
            Do not make new search requests.
            Ensure all information is factual and properly formatted.
            """,
            agent=self.analyzer(),
            expected_output="JSON formatted analysis of the topic including description, keywords, news, and trends"
        )

    @crew
    def crew(self) -> Crew:
        """Creates the research and analysis crew"""
        return Crew(
            agents=[self.researcher(), self.analyzer()],
            tasks=[self.research_task(), self.analysis_task()],
            process=Process.sequential,
            verbose=True,
        )