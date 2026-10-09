from dependency_injector.wiring import inject, Provide

from mcp.server.fastmcp import FastMCP
from src.applications.middleware.auth_middleware import user_ctx
from src.applications.config.auth_utils import get_user_and_roles
from src.applications.settings.container import Container
from src.domain.usecase.prompt_usecase import PromptUseCase
# ANCHOR_PROMPTS_IMPORT (no borrar)

@inject
def bind_prompts(mcp: FastMCP,
                   prompt_usecase: PromptUseCase = Provide[Container.prompt_usecase],
                   # ANCHOR_PROMPTS_PROVIDE (no borrar)
                   ):

    """
    Bind prompts.
    """

    @mcp.prompt()
    async def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
        """Generate a prompt for Claude to find and discuss academic papers on a specific topic."""
        user = user_ctx.get()
        get_user_and_roles(type('Context', (), {'user': user})(), ["MCP.PROMPT.SEARCH"], log_prefix="prompt")
        return await prompt_usecase.generate_search_prompt(topic=topic, num_papers=num_papers)
    
    # ANCHOR_PROMPTS_BIND (no borrar)
