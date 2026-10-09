from typing import List
from decimal import Decimal
from dependency_injector.wiring import inject, Provide
from src.applications.config.auth_utils import get_user_and_roles
from mcp.server.fastmcp import FastMCP
from src.applications.middleware.auth_middleware import user_ctx
from src.applications.settings.container import Container
from src.domain.usecase.paper_usecase import PaperUseCase
from src.domain.usecase.sum_usecase import SumUseCase
from src.domain.usecase.retrieve_personal_data_use_case import (
    RetrievePersonalDataUseCase
)
# ANCHOR_TOOLS_IMPORT (no borrar)
from src.domain.usecase.CurrencyConverter_use_case import CurrencyconverterUseCase


@inject
def bind_tools(
    mcp: FastMCP,
    paper_usecase: PaperUseCase = Provide[Container.paper_usecase],
    sum_usecase: SumUseCase = Provide[Container.sum_usecase],
    personal_data_usecase: RetrievePersonalDataUseCase = Provide[
        Container.personal_data_usecase
    ],
    # ANCHOR_TOOLS_PROVIDE (no borrar)
    CurrencyConverter_use_case: CurrencyconverterUseCase = Provide[Container.CurrencyConverter_use_case],
):
    """
    Bind tools.
    """

    @mcp.tool("search_papers")
    async def search_papers(topic: str, max_results: int = 5) -> List[str]:
        """
        Search for papers on arXiv based on a topic and store
        their information.

        Args:
            topic: The topic to search for
            max_results: Maximum number of results to retrieve (default: 5)

        Returns:
            List of paper IDs found in the search
        """  

        user = user_ctx.get()
        get_user_and_roles(type('Context', (), {'user': user})(), ["MCP.TOOL.SEARCH"], log_prefix="tool")
        return await paper_usecase.search_papers(topic, max_results)

    @mcp.tool("extract_info")
    async def extract_info(paper_id: str) -> str:
        """
        Search for information about a specific paper across all topic
        directories.

        Args:
            paper_id: The ID of the paper to look for

        Returns:
            JSON string with paper information if found, error message
            if not found
        """
        
        user = user_ctx.get()
        get_user_and_roles(type('Context', (), {'user': user})(), ["MCP.TOOL.EXTRACT"], log_prefix="tool")
        return await paper_usecase.extract_info(paper_id)

    @mcp.tool("sum_numbers")
    async def sum_numbers(a: float, b: float) -> float:
        """
        Sum two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            The sum of both numbers
        """
       
        user = user_ctx.get()
        get_user_and_roles(type('Context', (), {'user': user})(), ["MCP.TOOL.INTERACTION"], log_prefix="tool")
        return await sum_usecase.execute(a, b)

    @mcp.tool("get_basic_personal_data")
    async def get_basic_personal_data(
        identification_type: str,
        identification_number: str
    ) -> dict:
        """
        Get basic personal information for a customer.

        Args:
            identification_type: Type of identification (e.g., 'CC', 'CE')
            identification_number: Identification number

        Returns:
            Dictionary with basic personal information including
            customer key, identification, and general information
        """
       
        user = user_ctx.get()
        get_user_and_roles(type('Context', (), {'user': user})(), ["MCP.TOOL.PERSONAL_DATA.BASIC"], log_prefix="tool")
        result = await personal_data_usecase.get_basic_information(
            identification_type,
            identification_number
        )
        return result.model_dump()

    @mcp.tool("get_detailed_personal_data")
    async def get_detailed_personal_data(
        identification_type: str,
        identification_number: str
    ) -> dict:
        """
        Get detailed personal information for a customer.

        Args:
            identification_type: Type of identification (e.g., 'CC', 'CE')
            identification_number: Identification number

        Returns:
            Dictionary with detailed personal information including
            customer key, identification, natural/legal person information,
            nationality, and detailed information
        """
        
        user = user_ctx.get()
        get_user_and_roles(type('Context', (), {'user': user})(), ["MCP.TOOL.PERSONAL_DATA.DETAILED"], log_prefix="tool")
        result = await personal_data_usecase.get_detailed_information(
            identification_type,
            identification_number
        )
        return result.model_dump()
    
    # ANCHOR_TOOLS_BIND (no borrar)

    @mcp.tool()
    async def convert_currency(
        amount: float,
        from_currency: str,
        to_currency: str,
    ) -> dict:
        """Convert an amount between two currencies using Frankfurter's latest rate."""
        result_model = await CurrencyConverter_use_case.execute(
            Decimal(str(amount)),
            from_currency,
            to_currency,
        )
        return result_model.model_dump(mode="json")
    