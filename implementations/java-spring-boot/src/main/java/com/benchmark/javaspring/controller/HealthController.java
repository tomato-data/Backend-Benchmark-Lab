package com.benchmark.javaspring.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {
    private static final String SERVER_NAME = "java-spring";

    @GetMapping("/health")
    public HealthResponse health() {
        return new HealthResponse("ok", SERVER_NAME);
    }

    public record HealthResponse(String status, String server) {
    }
}
