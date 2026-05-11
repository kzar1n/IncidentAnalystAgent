package com.incident.analyzer.observability;

import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.exporter.otlp.logs.OtlpGrpcLogRecordExporter;
import io.opentelemetry.instrumentation.logback.appender.v1_0.OpenTelemetryAppender;
import io.opentelemetry.sdk.logs.SdkLoggerProvider;
import io.opentelemetry.sdk.logs.export.BatchLogRecordProcessor;
import io.opentelemetry.sdk.resources.Resource;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.context.event.ApplicationStartedEvent;
import org.springframework.context.ApplicationListener;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.Environment;

import java.time.Duration;

@Configuration
@ConditionalOnClass(OpenTelemetryAppender.class)
public class OpenTelemetryLoggingConfiguration {

    /**
     * Register OTLP {@link SdkLoggerProvider} so Spring merges it into {@link io.opentelemetry.sdk.OpenTelemetrySdk}
     * (see {@link org.springframework.boot.actuate.autoconfigure.opentelemetry.OpenTelemetryAutoConfiguration}).
     */
    @Bean
    SdkLoggerProvider otelSdkLoggerProvider(Environment env,
            @Qualifier("openTelemetryResource") Resource openTelemetryResource) {
        OtlpGrpcLogRecordExporter exporter = OtlpGrpcLogRecordExporter.builder()
                .setEndpoint(normalizeOtlpGrpcEndpoint(resolveEndpoint(env)))
                .setTimeout(Duration.ofSeconds(env.getProperty("otel.exporter.otlp.timeout.seconds", Long.class, 10L)))
                .build();
        return SdkLoggerProvider.builder()
                .setResource(openTelemetryResource)
                .addLogRecordProcessor(BatchLogRecordProcessor.builder(exporter).build())
                .build();
    }

    private static String resolveEndpoint(Environment env) {
        String fromLogs = env.getProperty("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT");
        String fromOtlp = env.getProperty("OTEL_EXPORTER_OTLP_ENDPOINT");
        String traces = env.getProperty("management.tracing.exporter.otlp.endpoint");
        String metrics = env.getProperty("management.metrics.export.otlp.url");

        String ep = fromLogs;
        if (ep == null || ep.isBlank()) {
            ep = fromOtlp;
        }
        if (ep == null || ep.isBlank()) {
            ep = traces;
        }
        if (ep == null || ep.isBlank()) {
            ep = metrics;
        }
        if (ep == null || ep.isBlank()) {
            ep = "http://localhost:4317";
        }
        return stripPathAfterAuthority(ep.trim());
    }

    private static String stripPathAfterAuthority(String url) {
        int schemeEnd = url.indexOf("://");
        if (schemeEnd < 0) {
            return url;
        }
        int slash = url.indexOf('/', schemeEnd + 3);
        if (slash > 0) {
            String path = url.substring(slash).toLowerCase();
            if (path.startsWith("/v1/")) {
                return url.substring(0, slash);
            }
            return url;
        }
        return url.endsWith("/") ? url.substring(0, url.length() - 1) : url;
    }

    private static String normalizeOtlpGrpcEndpoint(String endpoint) {
        String e = endpoint.endsWith("/") ? endpoint.substring(0, endpoint.length() - 1) : endpoint;
        return stripPathAfterAuthority(e);
    }

    @Bean
    ApplicationListener<ApplicationStartedEvent> installOpenTelemetryLogbackAppender(OpenTelemetry openTelemetry) {
        return event -> OpenTelemetryAppender.install(openTelemetry);
    }
}
