"""Jira API client for SBT portal."""
import os
import ssl
from typing import Optional, List, Dict, Any
import httpx


class JiraClient:
    """Client for Jira API with PLATFORM_SESSION authentication."""

    def __init__(
        self,
        url: str = "https://portal.works.prod.sbt",
        api_token: Optional[str] = None,
        username: Optional[str] = None,
    ):
        self.base_url = url.rstrip("/")
        self.api_token = api_token
        self.username = username
        self._session_cookie = os.getenv("JIRA_PLATFORM_SESSION")
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create httpx client."""
        if self._client is None:
            headers = {"Accept": "application/json"}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            if self._session_cookie:
                headers["Cookie"] = f"PLATFORM_SESSION={self._session_cookie}"

            # Create SSL context that allows self-signed certificates (for corporate proxies)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            self._client = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0,
                verify=False,  # Disable SSL verification for corporate environments
            )
        return self._client

    def search_tasks(
        self,
        jql: str = "assignee = currentUser()",
        max_results: int = 50,
        start: int = 0,
        fields: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search Jira tasks using JQL query.

        Args:
            jql: JQL query string
            max_results: Maximum number of results
            start: Start index for pagination
            fields: List of fields to return (default: all)

        Returns:
            List of task dictionaries
        """
        client = self._get_client()
        params = {
            "jql": jql,
            "maxResults": max_results,
            "startAt": start,
        }
        if fields:
            params["fields"] = ",".join(fields)

        try:
            response = client.get("/rest/api/2/search", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("issues", [])
        except httpx.HTTPError as e:
            raise Exception(f"Jira API error: {e}") from e

    def get_task(self, key: str, fields: List[str] = None) -> Dict[str, Any]:
        """
        Get a single task by key.

        Args:
            key: Task key (e.g., "WMB-123")

        Returns:
            Task dictionary
        """
        client = self._get_client()
        params = {}
        if fields:
            params["fields"] = ",".join(fields)

        try:
            response = client.get(f"/rest/api/2/issue/{key}", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Jira API error: {e}") from e

    def get_my_tasks(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get tasks assigned to current user.

        Args:
            max_results: Maximum number of results

        Returns:
            List of task dictionaries
        """
        return self.search_tasks(
            jql="assignee = currentUser()",
            max_results=max_results,
            fields=["summary", "description", "status", "assignee", "created", "updated", "priority"],
        )

    def create_task(
        self,
        summary: str,
        description: str = None,
        project: str = None,
        issue_type: str = "Task",
        assignee: str = None,
    ) -> Dict[str, Any]:
        """
        Create a new task.

        Args:
            summary: Task summary
            description: Task description
            project: Project key (default: user's default project)
            issue_type: Issue type (default: Task)
            assignee: Assignee username

        Returns:
            Created task dictionary
        """
        client = self._get_client()

        payload = {
            "fields": {
                "summary": summary,
                "issuetype": {"name": issue_type},
            }
        }

        if description:
            payload["fields"]["description"] = description

        if project:
            payload["fields"]["project"] = {"key": project}

        if assignee:
            payload["fields"]["assignee"] = {"name": assignee}

        try:
            response = client.post("/rest/api/2/issue", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Jira API error: {e}") from e

    def update_task_status(self, key: str, status: str) -> Dict[str, Any]:
        """
        Update task status.

        Args:
            key: Task key
            status: New status name

        Returns:
            Updated task dictionary
        """
        client = self._get_client()

        payload = {
            "transition": {
                "id": self._get_transition_id(key, status),
            }
        }

        try:
            response = client.post(f"/rest/api/2/issue/{key}/transitions", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Jira API error: {e}") from e

    def _get_transition_id(self, key: str, status: str) -> int:
        """
        Get transition ID for a status.

        Args:
            key: Task key
            status: Target status name

        Returns:
            Transition ID
        """
        client = self._get_client()

        try:
            response = client.get(f"/rest/api/2/issue/{key}/transitions")
            response.raise_for_status()
            data = response.json()

            for transition in data.get("transitions", []):
                if transition.get("to", {}).get("name") == status:
                    return transition["id"]
            raise Exception(f"Transition to '{status}' not found")
        except httpx.HTTPError as e:
            raise Exception(f"Jira API error: {e}") from e

    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
