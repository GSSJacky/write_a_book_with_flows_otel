from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
# Remove: from langchain_openai import ChatOpenAI # No longer needed here
# from langchain_google_genai import ChatGoogleGenerativeAI # Not needed here if passed from main

from write_a_book_with_flows.types import BookOutline


@CrewBase
class OutlineCrew:
    """Book Outline Crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    # REMOVE the class-level llm definition:
    # # llm = ChatOpenAI(model="chatgpt-4o-latest")
    # # llm = ChatOpenAI(model="gpt-4o")

    # The llm will be passed during instantiation from main.py and available as self.llm
    def __init__(self, llm):  # ✅ 只加这一段！
        print("[DEBUG] OutlineCrew received LLM:", llm)
        self.llm = llm


    @agent
    def researcher(self) -> Agent:
        search_tool = SerperDevTool()
        return Agent(
            config=self.agents_config["researcher"],
            tools=[search_tool],
            llm=self.llm,  # This will now use the gemini_llm passed to the crew
            verbose=True,
        )

    @agent
    def outliner(self) -> Agent:
        return Agent(
            config=self.agents_config["outliner"],
            llm=self.llm,  # This will now use the gemini_llm passed to the crew
            verbose=True,
        )

    @task
    def research_topic(self) -> Task:
        return Task(
            config=self.tasks_config["research_topic"],
            # agent=self.researcher() # Agent is typically assigned by the Crew if not specified here
        )

    @task
    def generate_outline(self) -> Task:
        return Task(
            config=self.tasks_config["generate_outline"],
            output_pydantic=BookOutline,
            #prompt="Generate a detailed book outline based on the research. Please write the output entirely in Japanese."
            # agent=self.outliner() # Agent is typically assigned by the Crew
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Book Outline Crew"""
        return Crew(
            agents=[self.researcher(), self.outliner()], # Explicitly pass instantiated agents
            tasks=[self.research_topic(), self.generate_outline()], # Explicitly pass instantiated tasks
            process=Process.sequential,
            verbose=True,
            # The llm for the agents is already set,
            # but if Crew itself needed an LLM for a manager agent (not used here),
            # it would also use self.llm if one was passed to the CrewBase constructor
        )