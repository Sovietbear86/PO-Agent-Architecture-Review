package com.example.taskapi.services;

import com.example.taskapi.models.Status;
import com.example.taskapi.models.Task;
import com.example.taskapi.repositories.TaskRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class TaskServiceTest {

    private TaskRepository repository;
    private TaskService service;

    @BeforeEach
    void setUp() {
        repository = new TaskRepository();
        service = new TaskService(repository);
    }

    @Test
    void createTask_returnsCreatedTask() {
        Task task = service.createTask("Test Task", "Description", "John");

        assertNotNull(task);
        assertEquals("Test Task", task.getTitle());
        assertEquals(Status.TODO, task.getStatus());
        assertNotNull(task.getId());
        assertNotNull(task.getCreatedAt());
        assertNotNull(task.getUpdatedAt());
    }

    @Test
    void getTaskById_returnsOptionalWithTask() {
        Task task = service.createTask("Test", null, null);

        Optional<Task> found = service.getTaskById(task.getId());

        assertTrue(found.isPresent());
        assertEquals("Test", found.get().getTitle());
    }

    @Test
    void getTaskById_returnsEmptyForNonExistent() {
        UUID nonExistentId = UUID.randomUUID();

        Optional<Task> found = service.getTaskById(nonExistentId);

        assertFalse(found.isPresent());
    }

    @Test
    void getTasks_returnsAllTasks() {
        service.createTask("Task 1", null, null);
        service.createTask("Task 2", null, null);

        List<Task> tasks = service.getTasks(null, null, 100, 0);

        assertEquals(2, tasks.size());
    }

    @Test
    void getTasks_withFilters_appliesFilters() {
        service.createTask("Task 1", null, "John");
        service.createTask("Task 2", null, "Jane");
        service.createTask("Task 3", null, "John");

        List<Task> tasks = service.getTasks(null, "John", 100, 0);

        assertEquals(2, tasks.size());
        for (Task task : tasks) {
            assertEquals("John", task.getAssignee());
        }
    }

    @Test
    void updateTask_returnsUpdatedTask() {
        Task original = service.createTask("Original", null, null);

        Optional<Task> result = service.updateTask(
                original.getId(),
                "Updated",
                null,
                null,
                null
        );

        assertTrue(result.isPresent());
        assertEquals("Updated", result.get().getTitle());
    }

    @Test
    void updateTask_returnsEmptyForNonExistent() {
        UUID nonExistentId = UUID.randomUUID();

        Optional<Task> result = service.updateTask(
                nonExistentId,
                "Updated",
                null,
                null,
                null
        );

        assertFalse(result.isPresent());
    }

    @Test
    void deleteTask_returnsTrueForExisting() {
        Task task = service.createTask("Delete Me", null, null);

        boolean deleted = service.deleteTask(task.getId());

        assertTrue(deleted);
        Optional<Task> found = service.getTaskById(task.getId());
        assertFalse(found.isPresent());
    }

    @Test
    void deleteTask_returnsFalseForNonExistent() {
        UUID nonExistentId = UUID.randomUUID();

        boolean deleted = service.deleteTask(nonExistentId);

        assertFalse(deleted);
    }

    @Test
    void updateTaskStatus_returnsUpdatedTask() {
        Task original = service.createTask("Task", null, null);

        Optional<Task> result = service.updateTaskStatus(original.getId(), "in_progress");

        assertTrue(result.isPresent());
        assertEquals(Status.IN_PROGRESS, result.get().getStatus());
    }

    @Test
    void updateTaskStatus_returnsEmptyForNonExistent() {
        UUID nonExistentId = UUID.randomUUID();

        Optional<Task> result = service.updateTaskStatus(nonExistentId, "in_progress");

        assertFalse(result.isPresent());
    }
}
