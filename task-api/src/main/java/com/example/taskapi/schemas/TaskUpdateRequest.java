package com.example.taskapi.schemas;

import jakarta.validation.constraints.Size;

public class TaskUpdateRequest {
    @Size(min = 1, max = 200, message = "Title must be between 1 and 200 characters")
    private String title;

    @Size(max = 1000, message = "Description must be 1000 characters or less")
    private String description;

    @Size(max = 100, message = "Assignee must be 100 characters or less")
    private String assignee;

    private String status;

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getAssignee() {
        return assignee;
    }

    public void setAssignee(String assignee) {
        this.assignee = assignee;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public boolean isTitleEmpty() {
        return title == null || title.trim().isEmpty();
    }
}
