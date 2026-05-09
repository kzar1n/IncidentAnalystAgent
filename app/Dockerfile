FROM maven:3.9-eclipse-temurin-21 AS builder

WORKDIR /app

COPY pom.xml .
RUN mvn dependency:go-offline -B

COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

COPY --from=builder /app/target/*.jar app.jar

ENV JAVA_OPTS="-Dotel.sdk.disabled=false \
              -Dotel.traces.exporter=otlp \
              -Dotel.exporter.otlp.endpoint=http://otel-collector:4317 \
              -Dotel.traces.sampler=always_on"

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

CMD ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
