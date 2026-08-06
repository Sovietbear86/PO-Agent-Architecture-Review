package com.example.taskapi.repositories;

import com.example.taskapi.models.Status;
import com.example.taskapi.models.Task;
import org.springframework.stereotype.Repository;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

@Repository
public class TaskRepository {

    private final Map<UUID, Task> tasks = new ConcurrentHashMap<>();

    public Task save(Task task) {
        tasks.put(task.getId(), task);
        return task;
    }

    public Optional<Task> findById(UUID id) {
        return Optional.ofNullable(tasks.get(id));
    }

    public List<Task> findAll(Status status, String assignee, int limit, int offset) {
        List<Task> result = new ArrayList<>(tasks.values());

        if (status != null) {
            result = result.stream()
                    .filter(t -> t.getStatus() == status)
                    .collect(Collectors.toList());
        }

        if (assignee != null && !assignee.isEmpty()) {
            result = result.stream()
                    .filter(t -> Objects.equals(t.getAssignee(), assignee))
                    .collect(Collectors.toList());
        }

        int fromIndex = Math.min(offset, result.size());
        int toIndex = Math.min(offset + limit, result.size());

        return result.subList(fromIndex, toIndex);
    }

    public Task update(UUID id, Task updatedTask) {
        Task existing = tasks.get(id);
        if (existing != null) {
            Task updated = existing.update(updatedTask);
            tasks.put(id, updated);
            return updated;
        }
        return null;
    }

    public boolean delete(UUID id) {
        return tasks.remove(id) != null;
    }

    public void clear() {
        tasks.clear();
    }
}
