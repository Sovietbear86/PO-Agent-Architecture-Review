"""Clarification options generators for PO Agent Platform v2.

Generates deterministic options for clarification questions.
"""

from typing import List, Dict, Any

from po_agent.clarification.models import ClarificationOption


class OptionsGenerator:
    """Generates clarification options from available data."""

    @staticmethod
    def from_products(products: List[str]) -> List[ClarificationOption]:
        """Generate product options.

        Args:
            products: List of product IDs

        Returns:
            List of ClarificationOption
        """
        return [
            ClarificationOption(
                label=product,
                value=product,
                description=f"Product: {product}"
            )
            for product in products
        ]

    @staticmethod
    def from_sprints(sprints: List[str]) -> List[ClarificationOption]:
        """Generate sprint options.

        Args:
            sprints: List of sprint IDs

        Returns:
            List of ClarificationOption
        """
        return [
            ClarificationOption(
                label=sprint,
                value=sprint,
                description=f"Sprint: {sprint}"
            )
            for sprint in sprints
        ]

    @staticmethod
    def from_members(members: List[str]) -> List[ClarificationOption]:
        """Generate member options.

        Args:
            members: List of member logins

        Returns:
            List of ClarificationOption
        """
        return [
            ClarificationOption(
                label=member,
                value=member,
                description=f"Member: {member}"
            )
            for member in members
        ]

    @staticmethod
    def from_releases(releases: List[str]) -> List[ClarificationOption]:
        """Generate release options.

        Args:
            releases: List of release IDs

        Returns:
            List of ClarificationOption
        """
        return [
            ClarificationOption(
                label=release,
                value=release,
                description=f"Release: {release}"
            )
            for release in releases
        ]

    @staticmethod
    def default_products() -> List[ClarificationOption]:
        """Generate default product options.

        Returns:
            List of ClarificationOption
        """
        return OptionsGenerator.from_products(["WMB", "OLP", "DMS", "STS"])

    @staticmethod
    def default_sprints() -> List[ClarificationOption]:
        """Generate default sprint options.

        Returns:
            List of ClarificationOption
        """
        return OptionsGenerator.from_sprints([
            "DMS-SPRNT-1",
            "OLP-SPRNT-1",
            "WMB-SPRNT-1",
            "STS-SPRNT-1",
        ])


# Export for convenience
__all__ = ["OptionsGenerator"]
