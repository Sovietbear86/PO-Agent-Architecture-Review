"""Full API endpoint tests for Task Tracker."""
import pytest
from fastapi.testclient import TestClient
from main import app

# Create shared repository for testing persistence
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService

_shared_repository = TaskRepository()


def get_test_task_service():
    """Get task service instance with shared repository."""
    return TaskService(_shared_repository)


# Override the dependency for testing
from app.routers import tasks as router_module
original_get_task_service = None


@pytest.fixture
def client():
    """Create a test client with shared repository for persistence."""
    global original_get_task_service
    original_get_task_service = router_module.get_task_service
    router_module.get_task_service = get_test_task_service
    
    yield TestClient(app)
    
    # Restore original
    if original_get_task_service:
        router_module.get_task_service = original_get_task_service
    _shared_repository.clear()


class TestHealthEndpoint:
    """Tests for /health endpoint."""
    
    def test_health_check_success(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestListTasksEndpoint:
    """Tests for GET /api/v1/tasks endpoint."""
    
    def test_list_tasks_empty(self, client):
        """Test listing tasks when no tasks exist."""
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_tasks_success(self, client):
        """Test listing tasks with data."""
        # Create multiple tasks
        for i in range(3):
            client.post("/api/v1/tasks", json={"title": f"Task {i}"})
        
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 3
        assert all("id" in task for task in tasks)
        assert all("title" in task for task in tasks)
    
    def test_list_tasks_with_status_filter(self, client):
        """Test filtering tasks by status."""
        # Create tasks with different statuses
        task1 = client.post("/api/v1/tasks", json={"title": "Task 1"}).json()
        task2 = client.post("/api/v1/tasks", json={"title": "Task 2"}).json()
        
        # Update task2 to in_progress
        client.patch(f"/api/v1/tasks/{task2['id']}/status", json={"status": "in_progress"})
        
        # Filter by todo status
        response = client.get("/api/v1/tasks", params={"status": "todo"})
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["id"] == task1["id"]
    
    def test_list_tasks_with_assignee_filter(self, client):
        """Test filtering tasks by assignee."""
        # Create tasks with different assignees
        client.post("/api/v1/tasks", json={"title": "Task 1", "assignee": "John"})
        client.post("/api/v1/tasks", json={"title": "Task 2", "assignee": "Jane"})
        client.post("/api/v1/tasks", json={"title": "Task 3", "assignee": "John"})
        
        # Filter by assignee
        response = client.get("/api/v1/tasks", params={"assignee": "John"})
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2
        assert all(task["assignee"] == "John" for task in tasks)
    
    def test_list_tasks_with_pagination(self, client):
        """Test pagination with limit and offset."""
        # Create 5 tasks
        for i in range(5):
            client.post("/api/v1/tasks", json={"title": f"Task {i}"})
        
        # Get first 2 tasks
        response = client.get("/api/v1/tasks", params={"limit": 2, "offset": 0})
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2
        
        # Get next 2 tasks
        response = client.get("/api/v1/tasks", params={"limit": 2, "offset": 2})
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2
    
    def test_list_tasks_combined_filters(self, client):
        """Test combining multiple filters."""
        # Create tasks
        client.post("/api/v1/tasks", json={"title": "Task 1", "assignee": "John", "status": "todo"})
        client.post("/api/v1/tasks", json={"title": "Task 2", "assignee": "Jane", "status": "todo"})
        client.post("/api/v1/tasks", json={"title": "Task 3", "assignee": "John", "status": "todo"})
        
        # Filter by status AND assignee (John with todo status)
        response = client.get("/api/v1/tasks", params={"status": "todo", "assignee": "John"})
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2


class TestCreateTaskEndpoint:
    """Tests for POST /api/v1/tasks endpoint."""
    
    def test_create_task_success(self, client):
        """Test creating a task with all fields."""
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "assignee": "John Doe"
        }
        response = client.post("/api/v1/tasks", json=task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["description"] == "Test Description"
        assert data["assignee"] == "John Doe"
        assert data["status"] == "todo"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_task_minimal(self, client):
        """Test creating a task with only required field."""
        task_data = {"title": "Minimal Task"}
        response = client.post("/api/v1/tasks", json=task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Task"
        assert data["description"] is None
        assert data["assignee"] is None
    
    def test_create_task_validation_empty_title(self, client):
        """Test validation error for empty title."""
        task_data = {"title": ""}
        response = client.post("/api/v1/tasks", json=task_data)
        assert response.status_code == 422
    
    def test_create_task_validation_missing_title(self, client):
        """Test validation error for missing title."""
        task_data = {"description": "No title"}
        response = client.post("/api/v1/tasks", json=task_data)
        assert response.status_code == 422
    
    def test_create_task_validation_title_too_long(self, client):
        """Test validation error for title exceeding max length."""
        task_data = {"title": "A" * 201}
        response = client.post("/api/v1/tasks", json=task_data)
        assert response.status_code == 422
    
    def test_create_task_validation_description_too_long(self, client):
        """Test validation error for description exceeding max length."""
        task_data = {"title": "Task", "description": "A" * 1001}
        response = client.post("/api/v1/tasks", json=task_data)
        assert response.status_code == 422
    
    def test_create_task_validation_assignee_too_long(self, client):
        """Test validation error for assignee exceeding max length."""
        task_data = {"title": "Task", "assignee": "A" * 101}
        response = client.post("/api/v1/tasks", json=task_data)
        assert response.status_code == 422


class TestGetTaskEndpoint:
    """Tests for GET /api/v1/tasks/{id} endpoint."""
    
    def test_get_task_success(self, client):
        """Test getting a task by ID."""
        # Create a task
        task_data = {"title": "Get Me"}
        create_response = client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["id"]
        
        # Get the task
        response = client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Get Me"
        assert data["id"] == task_id
    
    def test_get_task_not_found(self, client):
        """Test getting a non-existent task."""
        task_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"
    
    def test_get_task_invalid_uuid(self, client):
        """Test getting a task with invalid UUID format."""
        response = client.get("/api/v1/tasks/invalid-uuid")
        assert response.status_code == 422


class TestUpdateTaskEndpoint:
    """Tests for PUT /api/v1/tasks/{id} endpoint."""
    
    def test_update_task_success(self, client):
        """Test updating a task with all fields."""
        # Create a task
        create_response = client.post("/api/v1/tasks", json={
            "title": "Original Title",
            "description": "Original Description",
            "assignee": "Original Assignee"
        })
        task_id = create_response.json()["id"]
        
        # Update the task
        update_data = {
            "title": "Updated Title",
            "description": "Updated Description",
            "assignee": "Updated Assignee"
        }
        response = client.put(f"/api/v1/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated Description"
        assert data["assignee"] == "Updated Assignee"
    
    def test_update_task_partial(self, client):
        """Test partial update of a task."""
        # Create a task
        create_response = client.post("/api/v1/tasks", json={
            "title": "Task",
            "description": "Description",
            "assignee": "John"
        })
        task_id = create_response.json()["id"]
        
        # Update only title
        update_data = {"title": "New Title"}
        response = client.put(f"/api/v1/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["description"] == "Description"
        assert data["assignee"] == "John"
    
    def test_update_task_not_found(self, client):
        """Test updating a non-existent task."""
        task_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"title": "Updated"}
        response = client.put(f"/api/v1/tasks/{task_id}", json=update_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"
    
    def test_update_task_validation_empty_title(self, client):
        """Test validation error for empty title in update."""
        # Create a task
        create_response = client.post("/api/v1/tasks", json={"title": "Task"})
        task_id = create_response.json()["id"]
        
        # Try to update with empty title
        update_data = {"title": ""}
        response = client.put(f"/api/v1/tasks/{task_id}", json=update_data)
        assert response.status_code == 422
    
    def test_update_task_validation_title_too_long(self, client):
        """Test validation error for title exceeding max length in update."""
        # Create a task
        create_response = client.post("/api/v1/tasks", json={"title": "Task"})
        task_id = create_response.json()["id"]
        
        # Try to update with long title
        update_data = {"title": "A" * 201}
        response = client.put(f"/api/v1/tasks/{task_id}", json=update_data)
        assert response.status_code == 422


class TestUpdateTaskStatusEndpoint:
    """Tests for PATCH /api/v1/tasks/{id}/status endpoint."""
    
    def test_update_status_success(self, client):
        """Test updating task status to in_progress."""
        # Create a task
        create_response = client.post("/api/v1/tasks", json={"title": "Task"})
        task_id = create_response.json()["id"]
        
        # Update status
        response = client.patch(f"/api/v1/tasks/{task_id}/status", json={"status": "in_progress"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
    
    def test_update_status_to_done(self, client):
        """Test updating task status to done."""
        # Create a task
        create_response = client.post("/api/v1/tasks", json={"title": "Task"})
        task_id = create_response.json()["id"]
        
        # Update status to done
        response = client.patch(f"/api/v1/tasks/{task_id}/status", json={"status": "done"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
    
    def test_update_status_invalid_status(self, client):
        """Test validation error for invalid status."""
        # Create a task
        create_response = client.post("/api/v1/tasks", json={"title": "Task"})
        task_id = create_response.json()["id"]
        
        # Try to set invalid status
        response = client.patch(f"/api/v1/tasks/{task_id}/status", json={"status": "invalid"})
        assert response.status_code == 422
    
    def test_update_status_not_found(self, client):
        """Test updating status of non-existent task."""
        task_id = "00000000-0000-0000-0000-000000000000"
        response = client.patch(f"/api/v1/tasks/{task_id}/status", json={"status": "in_progress"})
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"
    
    def test_update_status_invalid_uuid(self, client):
        """Test updating status with invalid UUID format."""
        response = client.patch("/api/v1/tasks/invalid-uuid/status", json={"status": "in_progress"})
        assert response.status_code == 422


class TestDeleteTaskEndpoint:
    """Tests for DELETE /api/v1/tasks/{id} endpoint."""
    
    def test_delete_task_success(self, client):
        """Test deleting an existing task."""
        # Create a task
        create_response = client.post("/api/v1/tasks", json={"title": "Delete Me"})
        task_id = create_response.json()["id"]
        
        # Delete the task
        response = client.delete(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(f"/api/v1/tasks/{task_id}")
        assert get_response.status_code == 404
    
    def test_delete_task_not_found(self, client):
        """Test deleting a non-existent task."""
        task_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"
    
    def test_delete_invalid_uuid(self, client):
        """Test deleting with invalid UUID format."""
        response = client.delete("/api/v1/tasks/invalid-uuid")
        assert response.status_code == 422


class TestDocsEndpoint:
    """Tests for documentation endpoints."""
    
    def test_swagger_docs_available(self, client):
        """Test that Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        # Swagger UI should contain some HTML elements
        assert "swagger" in response.text.lower()
    
    def test_redoc_docs_available(self, client):
        """Test that ReDoc is available."""
        response = client.get("/redoc")
        assert response.status_code == 200
