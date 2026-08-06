package com.example.taskapi.routers;

import com.example.taskapi.models.Status;
import com.example.taskapi.models.Task;
import com.example.taskapi.schemas.TaskCreateRequest;
import com.example.taskapi.schemas.TaskUpdateRequest;
import com.example.taskapi.schemas.TaskResponse;
import com.example.taskapi.services.TaskService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/tasks")
@Validated
public class TaskController {

    private final TaskService service;

    public TaskController(TaskService service) {
        this.service = service;
    }

    @GetMapping
    public ResponseEntity<List<TaskResponse>> listTasks(
            @RequestParam(required = false) Status status,
            @RequestParam(required = false) String assignee,
            @RequestParam(defaultValue = "100") int limit,
            @RequestParam(defaultValue = "0") int offset) {
        List<TaskResponse> tasks = service.getTasks(status, assignee, limit, offset)
                .stream()
                .map(TaskResponse::new)
                .toList();
        return ResponseEntity.ok(tasks);
    }

    @GetMapping("/{id}")
    public ResponseEntity<TaskResponse> getTask(@PathVariable UUID id) {
        return service.getTaskById(id)
                .map(task -> ResponseEntity.ok(new TaskResponse(task)))
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<TaskResponse> createTask(@RequestBody @Validated TaskCreateRequest request) {
        Task task = service.createTask(
                request.getTitle(),
                request.getDescription(),
                request.getAssignee()
        );
        TaskResponse response = new TaskResponse(task);
        return ResponseEntity.created(URI.create("/api/v1/tasks/" + task.getId()))
                .body(response);
    }

    @PutMapping("/{id}")
    public ResponseEntity<TaskResponse> updateTask(
            @PathVariable UUID id,
            @RequestBody @Validated TaskUpdateRequest request) {
        return service.updateTask(
                id,
                request.getTitle(),
                request.getDescription(),
                request.getAssignee(),
                request.getStatus()
        ).map(task -> ResponseEntity.ok(new TaskResponse(task)))
                .orElse(ResponseEntity.notFound().build());
    }

    @PatchMapping("/{id}/status")
    public ResponseEntity<TaskResponse> updateStatus(
            @PathVariable UUID id,
            @RequestBody @Validated TaskUpdateRequest request) {
        return service.updateTaskStatus(id, request.getStatus())
                .map(task -> ResponseEntity.ok(new TaskResponse(task)))
                .orElse(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteTask(@PathVariable UUID id) {
        boolean deleted = service.deleteTask(id);
        if (!deleted) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.noContent().build();
    }
}
