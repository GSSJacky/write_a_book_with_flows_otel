import os
import asyncio
from typing import List
import re # For more robust stripping

from dotenv import load_dotenv
from traceloop.sdk import Traceloop
from opentelemetry.semconv.resource import ResourceAttributes

from crewai import LLM

from pydantic import BaseModel
from crewai.crews.crew_output import CrewOutput 

from crewai.flow.flow import Flow, listen, start

from write_a_book_with_flows.crews.write_book_chapter_crew.write_book_chapter_crew import (
    WriteBookChapterCrew,
)
from write_a_book_with_flows.types import Chapter, ChapterOutline, BookOutline
from write_a_book_with_flows.crews.outline_book_crew.outline_crew import OutlineCrew



load_dotenv()
Traceloop.init(app_name="crewai_writebook_with_flows", disable_batch=True)
#Traceloop.init(app_name="crewai_writebook_with_flows",
#    resource_attributes={
#        ResourceAttributes.SERVICE_NAME: "crewai_writebook_with_gemini"
#    },
#    disable_batch=True
#)

gemini_llm = None
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")

    gemini_llm = LLM(
        model="gemini/gemini-2.0-flash", # Ensure this is a valid and available model
        api_key=gemini_api_key,
        temperature=0.75,
        provider="google"
    )

    print("Gemini LLM Initialized Successfully.")
except Exception as e:
    print(f"Error initializing Gemini LLM: {e}")
    print("Please ensure your GEMINI_API_KEY is set correctly in .env and you have 'pip install langchain-google-genai'.")
    exit()


def _strip_markdown_json(s: str) -> str:
    """
    Strips markdown JSON fences (```json ... ``` or just ``` ... ```) from a string.
    """
    # Remove ```json prefix and ``` suffix
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", s, re.DOTALL)
    if match:
        return match.group(1).strip()
    # If no fences found, return the original string, stripped of whitespace
    return s.strip()


class BookState(BaseModel):
    id: str = "1"
    title: str = "The Current State of AI in 2025"
    book: List[Chapter] = []
    book_outline: List[ChapterOutline] = []
    topic: str = (
        "Exploring the latest trends in AI across different industries as of 2025"
    )
    goal: str = """
        The goal of this book is to provide a comprehensive overview of the current state of artificial intelligence including OpenAI, Gemini, Watsonx, Deepseek etc.. in May 2025.
        It will delve into the latest trends impacting various industries, analyze significant advancements,
        and discuss potential future developments. The book aims to inform readers about cutting-edge AI technologies
        and prepare them for upcoming innovations in the field.
    """


class BookFlow(Flow[BookState]):
    initial_state = BookState

    @start()
    def generate_book_outline(self):
        print("📘 Kickoff the Book Outline Crew with Gemini LLM")
        outline_crew_instance = OutlineCrew(llm=gemini_llm)
        output = outline_crew_instance.crew().kickoff(inputs={"topic": self.state.topic, "goal": self.state.goal})
        
        print(f"🔍 Raw CrewOutput object from OutlineCrew: {output}")
        print(f"🔍 Type of CrewOutput object: {type(output)}")
        if isinstance(output, CrewOutput):
            # Log attributes of CrewOutput to understand its structure
            print(f"  CrewOutput dir(): {dir(output)}")
            if hasattr(output, 'raw'):
                 print(f"  CrewOutput.raw: {output.raw}")
                 print(f"  Type of CrewOutput.raw: {type(output.raw)}")
            else:
                print("  CrewOutput does not have .raw attribute")


        self.state.book_outline = []
        
        try:
            parsed_book_outline = None
            if isinstance(output, CrewOutput):
                print("✅ Output is CrewOutput. Processing...")
                # Attempt to access attributes directly if CrewOutput populates them from Pydantic model
                if hasattr(output, 'chapters') and isinstance(getattr(output, 'chapters'), list):
                    try:
                        chapters_data = []
                        valid_items = True
                        for item in getattr(output, 'chapters'):
                            if isinstance(item, ChapterOutline):
                                chapters_data.append(item)
                            elif isinstance(item, dict): 
                                chapters_data.append(ChapterOutline(**item))
                            else:
                                print(f"⚠️ Unexpected item type in CrewOutput.chapters: {type(item)}. Item: {str(item)[:100]}")
                                valid_items = False
                                break
                        if valid_items:
                            parsed_book_outline = BookOutline(chapters=chapters_data)
                            print("✅ Successfully created BookOutline from CrewOutput direct 'chapters' attribute.")
                        else:
                            print("⚠️ Could not form valid BookOutline from CrewOutput.chapters due to item types.")
                    except Exception as e_direct_attr:
                        print(f"⚠️ Error creating BookOutline from CrewOutput direct 'chapters' attribute: {e_direct_attr}")
                
                if parsed_book_outline is None and hasattr(output, 'raw') and output.raw is not None:
                    print("💡 Direct attribute access for BookOutline failed or was skipped. Trying to parse CrewOutput.raw.")
                    if isinstance(output.raw, str):
                        raw_json_string = output.raw
                        cleaned_json_string = _strip_markdown_json(raw_json_string)
                        try:
                            parsed_book_outline = BookOutline.model_validate_json(cleaned_json_string)
                            print("✅ Successfully parsed CrewOutput.raw (string) into BookOutline.")
                        except Exception as e_raw_str:
                            print(f"⚠️ Error parsing CrewOutput.raw (string) as JSON for BookOutline: {e_raw_str}")
                            print(f"   Original raw string: {str(raw_json_string)[:500]}...")
                            print(f"   Cleaned string content for BookOutline: {str(cleaned_json_string)[:500]}...")
                    elif isinstance(output.raw, dict):
                        try:
                            parsed_book_outline = BookOutline(**output.raw)
                            print("✅ Successfully parsed CrewOutput.raw (dict) into BookOutline.")
                        except Exception as e_raw_dict:
                            print(f"⚠️ Error parsing CrewOutput.raw (dict) into BookOutline: {e_raw_dict}")
                    else:
                        print(f"⚠️ CrewOutput.raw is not a string or dict. Type: {type(output.raw)}. Content: {str(output.raw)[:500]}...")
                elif parsed_book_outline is None and not (hasattr(output, 'chapters') and isinstance(getattr(output, 'chapters'), list)): # Condition to avoid double printing if direct attr was already tried
                     print(f"⚠️ CrewOutput has no usable direct attributes for BookOutline and .raw is None or missing. Cannot parse. CrewOutput content: {vars(output) if not callable(output) and hasattr(output, '__dict__') else str(output)}")

            elif isinstance(output, BookOutline): 
                parsed_book_outline = output
                print("✅ Output was directly a BookOutline Pydantic model.")
            elif isinstance(output, dict): 
                try:
                    parsed_book_outline = BookOutline(**output)
                    print("✅ Output was a dictionary, successfully parsed into BookOutline.")
                except Exception as e_dict:
                    print(f"⚠️ Error parsing dict into BookOutline: {e_dict}")
            elif isinstance(output, str): 
                cleaned_json_string = _strip_markdown_json(output)
                try:
                    parsed_book_outline = BookOutline.model_validate_json(cleaned_json_string)
                    print("✅ Output was a string, successfully parsed as JSON into BookOutline.")
                except Exception as e_str:
                    print(f"⚠️ Error parsing string as JSON for BookOutline: {e_str}")
                    print(f"   Original string: {str(output)[:500]}...")
                    print(f"   Cleaned string content for BookOutline: {str(cleaned_json_string)[:500]}...")
            else:
                print(f"⚠️ Warning: OutlineCrew kickoff returned an unrecognized type: {type(output)}. Cannot parse.")

            if parsed_book_outline and hasattr(parsed_book_outline, 'chapters') and isinstance(parsed_book_outline.chapters, list):
                final_chapters = []
                for item in parsed_book_outline.chapters:
                    if isinstance(item, ChapterOutline):
                        final_chapters.append(item)
                    elif isinstance(item, dict): 
                        try:
                            final_chapters.append(ChapterOutline(**item))
                        except Exception as e_final_conv:
                            print(f"⚠️ Error converting dict item to ChapterOutline in final pass: {e_final_conv}")
                    else:
                        print(f"⚠️ Non-ChapterOutline/dict item in final_chapters list: {type(item)}")
                self.state.book_outline = final_chapters
                print(f"✅ Chapters Outline Extracted (count: {len(self.state.book_outline)}):")
                for i, ch_outline in enumerate(self.state.book_outline):
                    print(f"  {i+1}. {ch_outline.title}")
            else:
                if parsed_book_outline:
                    chapters_attr = getattr(parsed_book_outline, 'chapters', 'MISSING_ATTRIBUTE')
                    is_list = isinstance(chapters_attr, list)
                    print(f"⚠️ Warning: Parsed BookOutline exists, but its 'chapters' attribute is problematic. Present: {chapters_attr != 'MISSING_ATTRIBUTE'}, IsList: {is_list}.")
                    if chapters_attr != 'MISSING_ATTRIBUTE':
                         print(f"   Type of 'chapters': {type(chapters_attr)}. Content: {str(chapters_attr)[:500]}...")
                else:
                    print("⚠️ Warning: BookOutline parsing failed or resulted in None. Outline will be empty.")
                self.state.book_outline = []

        except Exception as e_outer:
            print(f"❌ Overall error during parsing OutlineCrew output: {e_outer}")
            import traceback
            traceback.print_exc()
            self.state.book_outline = []
        
        return self.state.book_outline


    @listen(generate_book_outline)
    async def write_chapters(self):
        print("Writing Book Chapters with Gemini LLM")
        tasks = []

        if not self.state.book_outline:
            print("No chapter outlines to write chapters for. Skipping chapter writing.")
            return

        async def write_single_chapter(chapter_outline: ChapterOutline):
            write_chapter_crew_instance = WriteBookChapterCrew(llm=gemini_llm) 
            crew_to_run = write_chapter_crew_instance.crew()
            print(f"  ✍️  Requesting WriteBookChapterCrew to write: '{chapter_outline.title}'")
            output = crew_to_run.kickoff(
                inputs={
                    "goal": self.state.goal,
                    "topic": self.state.topic,
                    "chapter_title": chapter_outline.title,
                    "chapter_description": chapter_outline.description,
                    "book_outline": [
                        co.model_dump_json() 
                        for co in self.state.book_outline if isinstance(co, ChapterOutline)
                    ],
                }
            )

            print(f"[DEBUG] Crew output for chapter '{chapter_outline.title}': {str(output)[:300]}...") # Limit print length
            print(f"[DEBUG] Type of Crew output for chapter '{chapter_outline.title}': {type(output)}")
            # if isinstance(output, CrewOutput): # Keep for detailed debugging if needed
            #     print(f"  [DEBUG] CrewOutput dir() for chapter: {dir(output)}")
            #     if hasattr(output, 'raw'):
            #         print(f"  [DEBUG] CrewOutput.raw for chapter: {str(output.raw)[:300]}...")


            chapter_to_return = Chapter(title=chapter_outline.title, content="⚠️ Error: No content generated or parsed.")

            try:
                parsed_chapter = None
                if isinstance(output, CrewOutput):
                    print(f"✅ Chapter output is CrewOutput for '{chapter_outline.title}'. Processing...")
                    if hasattr(output, 'title') and hasattr(output, 'content') and isinstance(getattr(output, 'title'), str) and isinstance(getattr(output, 'content'), str):
                        try:
                            parsed_chapter = Chapter(title=getattr(output, 'title'), content=getattr(output, 'content'))
                            print(f"✅ Successfully created Chapter from CrewOutput direct attributes for '{chapter_outline.title}'.")
                        except Exception as e_direct_chap:
                            print(f"⚠️ Error creating Chapter from CrewOutput direct attributes: {e_direct_chap}")
                    
                    if parsed_chapter is None and hasattr(output, 'raw') and output.raw is not None:
                        print(f"💡 Direct attribute for Chapter failed or skipped for '{chapter_outline.title}'. Trying CrewOutput.raw.")
                        if isinstance(output.raw, str):
                            raw_chapter_string = output.raw
                            cleaned_chapter_string = _strip_markdown_json(raw_chapter_string)
                            try:
                                parsed_chapter = Chapter.model_validate_json(cleaned_chapter_string)
                                print(f"✅ Successfully parsed CrewOutput.raw (string) into Chapter for '{chapter_outline.title}'.")
                            except Exception as e_raw_str_chap:
                                print(f"⚠️ Error parsing CrewOutput.raw (string) as JSON for Chapter '{chapter_outline.title}': {e_raw_str_chap}")
                                print(f"   Original raw string: {str(raw_chapter_string)[:200]}...")
                                print(f"   Cleaned string content for Chapter: {str(cleaned_chapter_string)[:200]}...")
                        elif isinstance(output.raw, dict):
                            try:
                                parsed_chapter = Chapter(**output.raw)
                                print(f"✅ Successfully parsed CrewOutput.raw (dict) into Chapter for '{chapter_outline.title}'.")
                            except Exception as e_raw_dict_chap:
                                print(f"⚠️ Error parsing CrewOutput.raw (dict) into Chapter for '{chapter_outline.title}': {e_raw_dict_chap}")
                        else:
                            print(f"⚠️ CrewOutput.raw is not a string or dict for chapter '{chapter_outline.title}'. Type: {type(output.raw)}")
                    elif parsed_chapter is None and not (hasattr(output, 'title') and hasattr(output, 'content')):
                         print(f"⚠️ CrewOutput for chapter '{chapter_outline.title}' has no usable direct attributes and .raw is None or missing.")

                elif isinstance(output, Chapter):
                    parsed_chapter = output
                    print(f"✅ Chapter output was directly a Chapter Pydantic model for '{chapter_outline.title}'.")
                elif isinstance(output, dict):
                    try:
                        parsed_chapter = Chapter(**output)
                        print(f"✅ Chapter output was a dict, parsed into Chapter for '{chapter_outline.title}'.")
                    except Exception as e_dict_chap:
                        print(f"⚠️ Error parsing dict into Chapter for '{chapter_outline.title}': {e_dict_chap}")
                elif isinstance(output, str):
                    cleaned_chapter_string = _strip_markdown_json(output)
                    try:
                        parsed_chapter = Chapter.model_validate_json(cleaned_chapter_string)
                        print(f"✅ Chapter output was a string, parsed as JSON into Chapter for '{chapter_outline.title}'.")
                    except Exception as e_str_chap:
                        print(f"⚠️ Error parsing string into Chapter for '{chapter_outline.title}': {e_str_chap}")
                        print(f"   Original string: {str(output)[:200]}...")
                        print(f"   Cleaned string content for Chapter: {str(cleaned_chapter_string)[:200]}...")
                else:
                    print(f"⚠️ Warning: Chapter crew returned an unrecognized type: {type(output)} for '{chapter_outline.title}'.")

                if parsed_chapter:
                    # Ensure the title from the Pydantic model is used, not the original outline title if they differ.
                    # However, for consistency, we might prefer the outline's title if the LLM changes it.
                    # For now, let's trust parsed_chapter.title if it exists and is a string.
                    if isinstance(getattr(parsed_chapter, 'title', None), str) and isinstance(getattr(parsed_chapter, 'content', None), str):
                        chapter_to_return = parsed_chapter
                        print(f"  ➡️  Successfully processed chapter: '{chapter_to_return.title}'")
                    else:
                        print(f"⚠️ Parsed chapter for '{chapter_outline.title}' has invalid title/content types. Using default error content.")
                        chapter_to_return = Chapter(title=chapter_outline.title, content=f"⚠️ Error: Parsed chapter for '{chapter_outline.title}' had malformed title/content.")
                else:
                    print(f"⚠️ Chapter parsing failed for '{chapter_outline.title}'. Using default error content.")
                    # chapter_to_return remains the default error chapter
            
            except Exception as e_chapter_outer:
                print(f"❌ Overall error parsing chapter output for '{chapter_outline.title}': {e_chapter_outer}")
                import traceback
                traceback.print_exc()
                # chapter_to_return remains the default error chapter

            return chapter_to_return


        for i, chapter_outline_item in enumerate(self.state.book_outline):
            if not isinstance(chapter_outline_item, ChapterOutline):
                print(f"Skipping invalid chapter outline item at index {i}: {chapter_outline_item}")
                continue
            print(f"  ⏳ Scheduling chapter {i+1}/{len(self.state.book_outline)}: '{chapter_outline_item.title}' for writing...")
            task = asyncio.create_task(write_single_chapter(chapter_outline_item))
            tasks.append(task)

        if tasks:
            chapters = await asyncio.gather(*tasks)
            self.state.book.extend([ch for ch in chapters if isinstance(ch, Chapter)]) # Ensure only valid Chapter objects are added
        else:
            print("No chapters were scheduled for writing.")

        print("📚 Final Book Chapters in State (titles):")
        for i, ch in enumerate(self.state.book):
            print(f"  {i+1}. {ch.title if hasattr(ch, 'title') else 'Untitled Chapter object'}")


    @listen(write_chapters)
    async def join_and_save_chapter(self):
        print("Joining and Saving Book Chapters")
        book_content = ""

        chapters_to_save = self.state.book if isinstance(self.state.book, list) else []
        if not chapters_to_save:
            print("⚠️ No chapters found in the book state. Will still save placeholder content.")

        for chapter in chapters_to_save:
            if not isinstance(chapter, Chapter):
                print(f"⚠️ Skipping invalid chapter item during save: {chapter}")
                book_content += f"\n\n# ⚠️ Invalid Chapter Object\n\nThis entry was not a valid Chapter object.\n\n"
                continue

            title = getattr(chapter, "title", "Untitled Chapter")
            content = getattr(chapter, "content", "(No content available)")

            # Attempt to remove redundant title from content if LLM included it
            # This regex matches a markdown header (e.g., "# Title", "## Title")
            # if it's at the very beginning of the content string and matches the chapter's title.
            
            # More robust way to check and remove leading title
            # Normalize whitespace and case for comparison, though titles should be exact
            normalized_content_start = re.sub(r'\s+', ' ', content.lstrip()).lower()
            normalized_title = re.sub(r'\s+', ' ', title).lower()
            
            cleaned_content = content
            # Regex to find markdown header at the beginning of the content
            # Allows for #, ##, ### etc. and optional spaces
            # Ensures it's at the start of the string (^)
            # Matches up to the first double newline
            header_pattern = re.compile(r"^\s*#+\s*(.+?)\s*(\r\n\r\n|\n\n|\r\r)", re.MULTILINE | re.DOTALL)
            match = header_pattern.match(content)

            if match:
                content_title_text = match.group(1).strip()
                normalized_content_title_text = re.sub(r'\s+', ' ', content_title_text).lower()
                if normalized_content_title_text == normalized_title:
                    # Remove the matched header (group 0 is the whole match)
                    cleaned_content = content[len(match.group(0)):]
                    print(f"  🧼 Cleaned redundant title '{content_title_text}' from content of chapter '{title}'")
            
            book_content += f"# {title}\n\n{cleaned_content.strip()}\n\n"


        output_dir = "./output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "book.md")

        try:
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(book_content.strip() or "# ⚠️ Book is empty\n\nNo valid chapters were generated.")
            print(f"✅ Book saved as {output_path}")
        except Exception as e:
            print(f"❌ Failed to save book: {e}")

        return book_content


def kickoff():
    book_flow_instance = BookFlow()
    book_flow_instance.kickoff()


def plot():
    book_flow_instance = BookFlow()
    book_flow_instance.plot()


if __name__ == "__main__":
    print("Starting book generation flow via direct script execution...")
    kickoff() 
    print("Book generation flow finished via direct script execution.")
# --- END OF FILE main.py ---