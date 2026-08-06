package com.example.taskapi.models;

import java.time.Instant;
import java.util.UUID;

public class Task {
    private final UUID id;
    private final String title;
    private final String description;
    private final String assignee;
    private final Status status;
    private final Instant createdAt;
    private final Instant updatedAt;

    public Task() {
        this.id = null;
        this.title = null;
        this.description = null;
        this.assignee = null;
        this.status = null;
        this.createdAt = null;
        this.updatedAt = null;
    }

    public Task(String title) {
        this.id = UUID.randomUUID();
        this.title = title;
        this.status = Status.TODO;
        this.createdAt = Instant.now();
        this.updatedAt = Instant.now();
        this.description = null;
        this.assignee = null;
    }

    public Task(String title, String description, String assignee) {
        this.id = UUID.randomUUID();
        this.title = title;
        this.description = description;
        this.assignee = assignee;
        this.status = Status.TODO;
        this.createdAt = Instant.now();
        this.updatedAt = Instant.now();
    }

    public UUID getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }

    public String getDescription() {
        return description;
    }

    public String getAssignee() {
        return assignee;
    }

    public Status getStatus() {
        return status;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public Task withTitle(String title) {
        return new Task(
                this.id,
                title,
                this.description,
                this.assignee,
                this.status,
                this.createdAt,
                Instant.now()
        );
    }

    public Task withDescription(String description) {
        return new Task(
                this.id,
                this.title,
                description,
                this.assignee,
                this.status,
                this.createdAt,
                Instant.now()
        );
    }

    public Task withAssignee(String assignee) {
        return new Task(
                this.id,
                this.title,
                this.description,
                assignee,
                this.status,
                this.createdAt,
                Instant.now()
        );
    }

    public Task withStatus(Status status) {
        return new Task(
                this.id,
                this.title,
                this.description,
                this.assignee,
                status,
                this.createdAt,
                Instant.now()
        );
    }

    public Task withCreatedAt(Instant createdAt) {
        return new Task(
                this.id,
                this.title,
                this.description,
                this.assignee,
                this.status,
                createdAt,
                this.updatedAt
        );
    }

    public Task withUpdatedAt(Instant updatedAt) {
        return new Task(
                this.id,
                this.title,
                this.description,
                this.assignee,
                this.status,
                this.createdAt,
                updatedAt
        );
    }

    private Task(UUID id, String title, String description, String assignee, Status status, Instant createdAt, Instant updatedAt) {
        this.id = id;
        this.title = title;
        this.description = description;
        this.assignee = assignee;
        this.status = status;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public Task update(Task updatedTask) {
        Task result = this;
        if (updatedTask.getTitle() != null) result = result.withTitle(updatedTask.getTitle());
        if (updatedTask.getDescription() != null) result = result.withDescription(updatedTask.getDescription());
        if (updatedTask.getAssignee() != null) result = result.withAssignee(updatedTask.getAssignee());
        if (updatedTask.getStatus() != null) result = result.withStatus(updatedTask.getStatus());
        result = result.withUpdatedAt(Instant.now());
        return result;
    }
}
