from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
# Remove: from langchain_openai import ChatOpenAI # No longer needed here

from write_a_book_with_flows.types import Chapter


@CrewBase
class WriteBookChapterCrew:
    """Write Book Chapter Crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    # REMOVE the class-level llm definition:
    # llm = ChatOpenAI(model="gpt-4o")

    # The llm will be passed during instantiation from main.py and available as self.llm
    def __init__(self, llm):  # ✅ 只加这一段！
        self.llm = llm

    @agent
    def researcher(self) -> Agent:
        search_tool = SerperDevTool()
        return Agent(
            config=self.agents_config["researcher"],
            tools=[search_tool],
            llm=self.llm,  # This will now use the gemini_llm passed to the crew
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config["writer"],
            llm=self.llm,  # This will now use the gemini_llm passed to the crew
        )

    @task
    def research_chapter(self) -> Task:
        return Task(
            config=self.tasks_config["research_chapter"],
            # agent=self.researcher()
        )

    @task
    def write_chapter(self) -> Task:
        return Task(
            config=self.tasks_config["write_chapter"],
            output_pydantic=Chapter,
            #prompt="Write a full book chapter based on the provided chapter title and outline. Please write the chapter entirely in Japanese."
            # agent=self.writer()
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Write Book Chapter Crew"""
        return Crew(
            agents=[self.researcher(), self.writer()], # Explicitly pass instantiated agents
            tasks=[self.research_chapter(), self.write_chapter()], # Explicitly pass instantiated tasks
            process=Process.sequential,
            verbose=True,
        )