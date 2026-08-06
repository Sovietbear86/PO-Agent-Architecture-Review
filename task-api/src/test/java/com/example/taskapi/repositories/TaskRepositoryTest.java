package com.example.taskapi.repositories;

import com.example.taskapi.models.Status;
import com.example.taskapi.models.Task;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for TaskRepository.
 */
public class TaskRepositoryTest {

    private TaskRepository repository;

    @BeforeEach
    void setUp() {
        repository = new TaskRepository();
    }

    @Test
    void saveTask_returnsSavedTask() {
        Task task = new Task("Test Task");
        Task saved = repository.save(task);

        assertNotNull(saved.getId());
        assertEquals("Test Task", saved.getTitle());
        assertEquals(task.getId(), saved.getId());
    }

    @Test
    void findById_returnsOptionalWithTask() {
        Task task = new Task("Test Task");
        repository.save(task);

        Optional<Task> found = repository.findById(task.getId());

        assertTrue(found.isPresent());
        assertEquals("Test Task", found.get().getTitle());
    }

    @Test
    void findById_returnsEmptyForNonExistent() {
        UUID nonExistentId = UUID.randomUUID();
        Optional<Task> found = repository.findById(nonExistentId);

        assertFalse(found.isPresent());
    }

    @Test
    void findAll_returnsAllTasks() {
        repository.save(new Task("Task 1"));
        repository.save(new Task("Task 2"));
        repository.save(new Task("Task 3"));

        List<Task> all = repository.findAll(null, null, 100, 0);

        assertEquals(3, all.size());
    }

    @Test
    void findAll_withStatusFilter_returnsFilteredTasks() {
        Task task1 = repository.save(new Task("Task 1"));
        Task task2 = repository.save(new Task("Task 2"));
        Task task2Updated = task2.withStatus(Status.IN_PROGRESS);
        repository.save(task2Updated);
        Task task3 = repository.save(new Task("Task 3"));

        List<Task> todoTasks = repository.findAll(Status.TODO, null, 100, 0);

        assertEquals(2, todoTasks.size());
        assertTrue(todoTasks.contains(task1));
        assertTrue(todoTasks.contains(task3));
        assertFalse(todoTasks.contains(task2Updated));
    }

    @Test
    void findAll_withAssigneeFilter_returnsFilteredTasks() {
        Task task1 = repository.save(new Task("Task 1"));
        Task task1Updated = task1.withAssignee("John");
        repository.save(task1Updated);
        
        Task task2 = repository.save(new Task("Task 2"));
        Task task2Updated = task2.withAssignee("Jane");
        repository.save(task2Updated);
        
        Task task3 = repository.save(new Task("Task 3"));
        Task task3Updated = task3.withAssignee("John");
        repository.save(task3Updated);

        List<Task> johnTasks = repository.findAll(null, "John", 100, 0);

        assertEquals(2, johnTasks.size());
        assertTrue(johnTasks.contains(task1Updated));
        assertTrue(johnTasks.contains(task3Updated));
        assertFalse(johnTasks.contains(task2Updated));
    }

    @Test
    void findAll_withPagination_returnsCorrectPage() {
        for (int i = 0; i < 5; i++) {
            repository.save(new Task("Task " + i));
        }

        List<Task> page1 = repository.findAll(null, null, 2, 0);
        List<Task> page2 = repository.findAll(null, null, 2, 2);

        assertEquals(2, page1.size());
        assertEquals(2, page2.size());
    }

    @Test
    void updateTask_returnsUpdatedTask() {
        Task task = repository.save(new Task("Original"));
        UUID taskId = task.getId();

        Task updated = task.withTitle("Updated").withAssignee("New Assignee");

        Task result = repository.update(taskId, updated);

        assertNotNull(result);
        assertEquals("Updated", result.getTitle());
        assertEquals("New Assignee", result.getAssignee());
    }

    @Test
    void updateTask_returnsNullForNonExistent() {
        UUID nonExistentId = UUID.randomUUID();
        Task updated = new Task("Updated");

        Task result = repository.update(nonExistentId, updated);

        assertNull(result);
    }

    @Test
    void deleteTask_returnsTrueForExisting() {
        Task task = repository.save(new Task("To Delete"));
        boolean deleted = repository.delete(task.getId());

        assertTrue(deleted);
        assertFalse(repository.findById(task.getId()).isPresent());
    }

    @Test
    void deleteTask_returnsFalseForNonExistent() {
        UUID nonExistentId = UUID.randomUUID();
        boolean deleted = repository.delete(nonExistentId);

        assertFalse(deleted);
    }

    @Test
    void clear_removesAllTasks() {
        repository.save(new Task("Task 1"));
        repository.save(new Task("Task 2"));

        repository.clear();

        List<Task> all = repository.findAll(null, null, 100, 0);
        assertEquals(0, all.size());
    }
}
