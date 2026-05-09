package com.incident.analyzer.controller;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/")
public class SimulationController {

    @GetMapping("/error")
    public ResponseEntity<Map<String, String>> simulateError() {
        log.error("Error endpoint called - triggering intentional exception");
        throw new NullPointerException("Fake exception - Simulated error for incident analysis");
    }

    @GetMapping("/timeout")
    public ResponseEntity<Map<String, String>> simulateTimeout() throws InterruptedException {
        log.warn("Timeout endpoint called - simulating 15 second delay");
        Thread.sleep(15000);
        Map<String, String> response = new HashMap<>();
        response.put("status", "timeout_completed");
        return ResponseEntity.ok(response);
    }

    @GetMapping("/payment/{id}")
    public ResponseEntity<Map<String, String>> getPayment(@PathVariable String id) {
        log.info("Payment endpoint called with id: {}", id);
        
        if ("999".equals(id)) {
            log.error("Invalid payment ID: {}", id);
            throw new IllegalArgumentException("Payment ID 999 is not valid - Simulated payment service error");
        }

        Map<String, String> response = new HashMap<>();
        response.put("id", id);
        response.put("status", "processed");
        response.put("amount", "100.00");
        return ResponseEntity.ok(response);
    }
}
