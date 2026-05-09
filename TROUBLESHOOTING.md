# Guia de Solução de Problemas

Soluções rápidas para problemas comuns ao executar a plataforma.

## Problemas de Inicialização

### Docker Compose falha ao iniciar

**Sintoma**: `docker-compose up` falha com erro

**Solução**:
```bash
# 1. Verifique se Docker está rodando
docker ps

# 2. Verifique versão do Docker Compose
docker-compose --version

# 3. Limpe containers antigos
docker-compose down
docker volume rm incidentanalystagent_*

# 4. Tente novamente
docker-compose up -d
```

### Porta já em uso

**Sintoma**: `bind: address already in use`

**Solução**:
```bash
# Verifique quais portas estão em uso
netstat -tuln | grep -E '8000|8080|5432|3301|4317'

# Mude a porta no docker-compose.yml ou .env
# Ou encerre o serviço usando a porta

# Linux/Mac
sudo lsof -i :8080
kill -9 <PID>

# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

### Erro: "Cannot connect to Docker daemon"

**Sintoma**: `Cannot connect to Docker daemon`

**Solução**:
- Abra Docker Desktop
- Aguarde inicialização completa
- Tente `docker ps` novamente

## Problemas de Serviço

### Serviço não fica healthy

**Sintoma**: `docker-compose ps` mostra `unhealthy`

**Solução**:
```bash
# Verifique logs
docker-compose logs <service_name>

# Exemplo para orchestrator
docker-compose logs orchestrator

# Reinicie o serviço
docker-compose restart orchestrator

# Se ainda falhar, reconstrua a imagem
docker-compose build --no-cache orchestrator
docker-compose up -d orchestrator
```

### Spring Boot não inicia

**Sintoma**: Container spring-app continua reiniciando

**Solução**:
```bash
# Verifique logs
docker-compose logs spring-app

# Comum: erro de compilação Maven
# Solução: reconstruir imagem
docker-compose build --no-cache spring-app
docker-compose up -d spring-app
```

### Orchestrator falha ao conectar ao PostgreSQL

**Sintoma**: `orchestrator` logs mostram erro de conexão

**Solução**:
```bash
# Verifique se PostgreSQL está rodando
docker-compose ps postgres

# Teste conexão ao banco
docker exec incident-postgres pg_isready

# Se não responder, reinicie
docker-compose restart postgres

# Verifique credenciais em .env
cat .env | grep DB_

# Recrie o banco se necessário
docker-compose down
docker volume rm incidentanalystagent_postgres_data
docker-compose up -d
```

### SigNoz não inicia

**Sintoma**: Erro ao conectar em localhost:3301

**Solução**:
```bash
# Verifique dependências
docker-compose logs clickhouse
docker-compose logs signoz

# ClickHouse requer espaco em disco
# Libere espaco se necessário

# Recrie volumes
docker-compose down
docker volume rm incidentanalystagent_clickhouse_data
docker volume rm incidentanalystagent_signoz_data
docker-compose up -d
```

## Problemas de Conectividade

### Não consegue acessar endpoints

**Sintoma**: `curl: Failed to connect`

**Solução**:
```bash
# Verifique se container está rodando
docker-compose ps

# Tente via nome do container na rede docker
docker exec orchestrator curl http://spring-app:8080/health

# Verifique firewall local
# Linux: sudo ufw allow 8080
# Windows: check firewall settings

# Tente localhost vs 127.0.0.1
curl http://127.0.0.1:8080/health
```

### Webhook do SigNoz não dispara

**Sintoma**: Incidente não é criado mesmo com erro

**Solução**:
```bash
# 1. Verifique se SigNoz está rodando
curl http://localhost:3301

# 2. Teste endpoint do orchestrator manualmente
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -d '{"alerts":[],"error_message":"test"}'

# 3. Configure alert rule no SigNoz
# - Abra http://localhost:3301
# - Alerts → Alert Rules → New
# - Webhook: http://orchestrator:8000/incidents

# 4. Verifique logs do orchestrator
docker-compose logs orchestrator
```

## Problemas de Dados

### Incidentes não aparecem no banco

**Sintoma**: `GET /incidents` retorna lista vazia

**Solução**:
```bash
# Verifique se tabela foi criada
docker exec incident-postgres psql -U incident_user -d incident_db \
  -c "\dt"

# Se tabela não existe, triggere erro para criar
curl http://localhost:8080/error

# Verifique dados
docker exec incident-postgres psql -U incident_user -d incident_db \
  -c "SELECT * FROM incidents;"
```

### Dados desaparecem após restart

**Sintoma**: Incidentes perdidos após `docker-compose down`

**Solução**:
```bash
# Verifique se volumes estão configurados
docker volume ls | grep postgres_data

# Certifique-se que não está usando volumes temporários
# Em docker-compose.yml, volumes devem estar nomeados
volumes:
  postgres_data:
    driver: local

# Não use: 
# volumes: []  # Isso apaga dados
```

## Problemas de AI/OpenAI

### CrewAI falha na análise

**Sintoma**: `/incidents/analyze` retorna erro

**Solução**:
```bash
# 1. Verifique API key em .env
cat .env | grep OPENAI_API_KEY

# 2. Teste conectividade com OpenAI
# Deve retornar página de status
curl https://status.openai.com/

# 3. Verifique logs do orchestrator
docker-compose logs orchestrator | grep -i "openai\|crew"

# 4. Confirme que tem quota/crédito na conta OpenAI
# https://platform.openai.com/account/usage/limits
```

### "Invalid API Key" error

**Sintoma**: CrewAI retorna erro de autenticação

**Solução**:
```bash
# 1. Verifique chave correta
# https://platform.openai.com/account/api-keys

# 2. Copie exatamente (sem espaços)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxx

# 3. Atualize .env
nano .env

# 4. Reinicie orchestrator
docker-compose down orchestrator
docker-compose up -d orchestrator

# 5. Aguarde 30 segundos e teste
sleep 30
curl -X POST http://localhost:8000/incidents/analyze \
  -d "service_name=test&error_type=Test&error_message=Test&stacktrace=Test"
```

## Problemas de Performance

### Aplicação lenta

**Sintoma**: Requests demoram muito tempo

**Solução**:
```bash
# 1. Aumente recursos do Docker
# Docker Desktop → Preferences/Settings → Resources
# CPU: 4+, Memory: 4GB+

# 2. Verifique uso de recursos
docker stats

# 3. Limpe dados/containers desnecessários
docker system prune -a

# 4. Reconstrua imagens sem cache
docker-compose build --no-cache

# 5. Use SSD em vez de HDD
```

### Database queries lentas

**Sintoma**: `GET /incidents` demora muito

**Solução**:
```bash
# 1. Verifique índices
docker exec incident-postgres psql -U incident_user -d incident_db \
  -c "\d incidents"

# 2. Execute query diretamente
docker exec incident-postgres psql -U incident_user -d incident_db \
  -c "SELECT COUNT(*) FROM incidents;"

# 3. Se muitos registros, use paginação
curl "http://localhost:8000/incidents?limit=10&offset=0"

# 4. Limpe dados antigos se necessário
docker exec incident-postgres psql -U incident_user -d incident_db \
  -c "DELETE FROM incidents WHERE created_at < now() - interval '30 days';"
```

## Problemas de Logs/Debugging

### Não vê logs detalhados

**Sintoma**: Logs não mostram informações suficientes

**Solução**:
```bash
# Aumente verbosity
# Edite .env
LOG_LEVEL=DEBUG

# Ou configure em application.yml (Spring Boot)
logging:
  level:
    root: DEBUG

# Reinicie serviços
docker-compose restart

# Veja logs detalhados
docker-compose logs -f --tail=100
```

### Logs não aparecem estruturados

**Sintoma**: Logs não são JSON

**Solução**:
```bash
# Verifique configuração de logging
# Spring Boot: src/main/resources/logback-spring.xml
# FastAPI: main.py setup_logging()

# Configure formato JSON
# Spring Boot usa logstash-logback-encoder
# FastAPI usa python-json-logger

# Reinicie após mudanças
docker-compose restart
```

## Comandos Úteis para Debug

```bash
# Ver status de todos os serviços
docker-compose ps

# Ver logs de um serviço específico
docker-compose logs -f orchestrator

# Executar comando em container
docker exec incident-postgres psql -U incident_user -d incident_db

# Ver volumes
docker volume ls

# Ver redes
docker network ls

# Inspeccionar container
docker inspect incident-spring-app

# Ver recuros usados
docker stats

# Reiniciar tudo
docker-compose restart

# Parar sem remover dados
docker-compose stop

# Remover tudo (cuidado!)
docker-compose down -v
```

## Checklist de Verificação

Se nada funciona:

- [ ] Docker está rodando?
  - `docker ps`

- [ ] .env está correto?
  - `cat .env`

- [ ] Portas estão disponíveis?
  - `netstat -tuln` (Linux/Mac)
  - `netstat -ano` (Windows)

- [ ] Espaço em disco?
  - `df -h` (Linux/Mac)
  - `disk usage` (Windows)

- [ ] Versão do Docker Compose?
  - `docker-compose --version` (deve ser 2.0+)

- [ ] Credenciais do banco corretas?
  - Testar: `docker exec incident-postgres pg_isready`

- [ ] API key OpenAI configurada?
  - `grep OPENAI_API_KEY .env`

- [ ] Firewall permite conexões?
  - Teste: `curl http://localhost:8080/health`

## Último Recurso

Se ainda não funciona:

```bash
# 1. Reset completo
docker-compose down
docker system prune -a
docker volume rm incidentanalystagent_*

# 2. Reconstrua tudo do zero
docker-compose build --no-cache

# 3. Inicie novamente
docker-compose up -d

# 4. Aguarde 60 segundos
sleep 60

# 5. Verifique status
docker-compose ps

# 6. Teste endpoint básico
curl http://localhost:8080/health
curl http://localhost:8000/health
```

## Suporte Adicional

Se o problema persistir:

1. **Verifique logs completos**:
   ```bash
   docker-compose logs > debug.log
   cat debug.log
   ```

2. **Teste conectividade entre containers**:
   ```bash
   docker exec orchestrator ping spring-app
   docker exec orchestrator ping postgres
   ```

3. **Verifique DNS**:
   ```bash
   docker exec orchestrator nslookup postgres
   ```

4. **Verifique network**:
   ```bash
   docker network inspect incidentanalystagent_incident-network
   ```

---

**Lembre-se**: Sempre checue os logs primeiro! (`docker-compose logs -f`)
