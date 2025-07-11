from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

# We will get the task model from our shared library
from core_lib.models.task import Task

from .logging_config import logger

# --- System Prompt ---
# This is the core instruction for our AI assistant.
PROMPT_TEMPLATE = """
You are TaskMaster AI, an expert in hierarchical task decomposition and time-based planning.
Transform high-level goals into detailed daily action plans with atomic subtasks.


RULES FOR SUBTASK DECOMPOSITION:
1. ATOMIC TASKS:
   - Each subtask must be executable without further breakdown
   - Maximum 1 core action per subtask
   - Clear completion criteria for every subtask

2. TIME MANAGEMENT:
   - Calculate duration from explicit time markers (e.g., "[15 min]")
   - Default scheduling:
     * Weekdays: First task at 19:00
     * Weekends: First task at 10:00
   - Minimum 10min buffer between subtasks

3. REQUIRED FIELDS PER SUBTASK:
   - title: Action-oriented verb phrase ("Practice scales", "Write API endpoints")
   - description: Numbered steps with time allocations per step
   - time_required: Total minutes (sum of step times)
   - resources: Any needed tools/materials
   - dependencies: Previous subtask IDs if required
   - metrics: Quantifiable success criteria

4. HIERARCHY PRINCIPLES:
   - 3-5 subtasks per day
   - Progressive difficulty: Foundation → Application → Mastery
   - Weekly themes: Week 1: Basics, Week 2: Integration, etc.

5. CONTENT REQUIREMENTS:
   - Include time estimates for EVERY step (e.g., "1. Warm-up [10 min]: ...")
   - Add pedagogical elements:
     * Theory + practice balance
     * Progressive overload
     * Spaced repetition
   - Domain-specific details (technical terms, best practices)

6. DEFAULTS:
   - Start date: Tomorrow (2025-06-23)
   - Subtask duration: 25-50min (learning), 30-90min (projects)
   - Complexity/Priority:
        Skill acquisition: 0.8/0.7
        Project delivery: 0.9/0.9
        Habit building: 0.5/0.6

USER'S GOAL:
{goal}

{format_instructions}
"""


# TODO tags from user tags storage
class TaskProcessor:
    """
    Encapsulates the logic for processing a goal using an LLM chain.
    """

    def __init__(self, model: BaseChatModel):
        # 1. Create a Pydantic parser for our Task model
        self.parser = PydanticOutputParser(pydantic_object=Task)

        # 2. Create a prompt template with format instructions
        self.prompt = ChatPromptTemplate.from_template(
            template=PROMPT_TEMPLATE,
            partial_variables={
                "format_instructions": self.parser.get_format_instructions()
            },
        )
        print(self.parser.get_format_instructions())

        # 3. Create the processing chain
        self.chain = self.prompt | model | self.parser

    async def process_goal(self, goal: str) -> Task:
        """
        Processes the user's goal and returns a structured Task object.
        """
        logger.info(f"Starting to process goal: '{goal[:50]}...'")
        try:
            # The .ainvoke method runs the chain asynchronously
            response = await self.chain.ainvoke({"goal": goal})
            logger.info(
                f"Successfully parsed LLM response for goal: '{goal[:50]}...'"
            )
            return response
        except Exception as e:
            logger.error(
                f"Failed to process goal '{goal[:50]}...'. Error: {e}",
                exc_info=True,
            )
            raise

    async def process_task(self, task: Task) -> Task:
        """
        Processes the user's task and returns new Task object.
        """
        goal = f" - {task.title} - \n{task.description}"
        logger.info(f"Starting to process goal: '{repr(task)[:50]}...'")
        try:
            # The .ainvoke method runs the chain asynchronously
            response = await self.chain.ainvoke({"goal": goal})
            logger.info(
                f"Successfully parsed LLM response for goal: '{goal[:50]}...'"
            )
            return response
        except Exception as e:
            logger.error(
                f"Failed to process goal '{goal[:50]}...'. Error: {e}",
                exc_info=True,
            )
            raise
