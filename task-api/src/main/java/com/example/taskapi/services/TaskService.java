package com.example.taskapi.services;

import com.example.taskapi.models.Status;
import com.example.taskapi.models.Task;
import com.example.taskapi.repositories.TaskRepository;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Service
public class TaskService {

    private final TaskRepository repository;

    public TaskService(TaskRepository repository) {
        this.repository = repository;
    }

    public Task createTask(String title, String description, String assignee) {
        Task task = new Task(title, description, assignee);
        return repository.save(task);
    }

    public Optional<Task> getTaskById(UUID id) {
        return repository.findById(id);
    }

    public List<Task> getTasks(Status status, String assignee, int limit, int offset) {
        return repository.findAll(status, assignee, limit, offset);
    }

    public Optional<Task> updateTask(UUID id, String title, String description, String assignee, String status) {
        Optional<Task> optionalTask = repository.findById(id);
        if (optionalTask.isEmpty()) {
            return Optional.empty();
        }

        Task existingTask = optionalTask.get();
        Task updatedTask = existingTask;

        if (title != null) updatedTask = updatedTask.withTitle(title);
        if (description != null) updatedTask = updatedTask.withDescription(description);
        if (assignee != null) updatedTask = updatedTask.withAssignee(assignee);
        if (status != null) updatedTask = updatedTask.withStatus(Status.fromValue(status));
        updatedTask = updatedTask.withUpdatedAt(Instant.now());

        Task saved = repository.update(id, updatedTask);
        return Optional.of(saved);
    }

    public boolean deleteTask(UUID id) {
        return repository.delete(id);
    }

    public Optional<Task> updateTaskStatus(UUID id, String status) {
        Optional<Task> optionalTask = repository.findById(id);
        if (optionalTask.isEmpty()) {
            return Optional.empty();
        }

        Task existingTask = optionalTask.get();
        Task updatedTask = existingTask.withStatus(Status.fromValue(status)).withUpdatedAt(Instant.now());

        Task saved = repository.update(id, updatedTask);
        return Optional.of(saved);
    }
}
