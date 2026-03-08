# Oriphim Operations CLI
# Make-based interface to backend REST API
# See OPS_CLI_GUIDE.md for complete documentation

.PHONY: help health-check server-start server-stop test tenant-create tenant-list user-create user-list key-generate key-list audit-trail metrics reset-db

# API base configuration
BASE_URL ?= http://localhost:8000
API_KEY ?=

# Python executable
PYTHON := python3

# Help target - lists all available commands
help:
	@echo "Oriphim Operations CLI"
	@echo "======================"
	@echo ""
	@echo "SYSTEM:"
	@echo "  make health-check        - Check system health status"
	@echo "  make server-start        - Start backend server"
	@echo "  make server-stop         - Stop backend server"
	@echo "  make docker-up           - Start services with Docker Compose"
	@echo "  make docker-down         - Stop Docker services"
	@echo "  make reset-db            - Delete and reset databases"
	@echo ""
	@echo "TESTING:"
	@echo "  make test                - Run unit tests"
	@echo "  make test-integration    - Run integration tests"
	@echo "  make test-e2e            - Run end-to-end tests"
	@echo "  make test-all            - Run all tests with coverage"
	@echo "  make test-performance    - Run load tests (requires locust)"
	@echo ""
	@echo "TENANTS:"
	@echo "  make tenant-create NAME=<name> DOMAIN=<domain> - Create tenant"
	@echo "  make tenant-list         - List all tenants"
	@echo ""
	@echo "USERS:"
	@echo "  make user-create TENANT=<id> EMAIL=<email> ROLE=<role> - Create user"
	@echo "  make user-list TENANT=<id> - List users for tenant"
	@echo ""
	@echo "API KEYS:"
	@echo "  make key-generate TENANT=<id> USER=<id> SCOPE=<scope> - Generate API key"
	@echo "  make key-list TENANT=<id> - List API keys for tenant"
	@echo ""
	@echo "MONITORING:"
	@echo "  make audit-trail         - View audit log"
	@echo "  make metrics             - View system metrics"
	@echo ""
	@echo "Environment variables:"
	@echo "  BASE_URL=http://localhost:8000  (API endpoint)"
	@echo "  API_KEY=<key>                   (Authentication token)"

# ============================================================================
# SYSTEM
# ============================================================================

health-check:
	@echo "Checking system health..."
	@$(PYTHON) scripts/ops_cli/health.py $(API_KEY)

server-start:
	@echo "Starting backend server..."
	@uvicorn app.main:app --reload --port 8000 &
	@echo "Server starting on http://localhost:8000"
	@echo "Swagger docs: http://localhost:8000/docs"

server-stop:
	@echo "Stopping backend server..."
	@pkill -f "uvicorn app.main:app" || echo "No server running"

docker-up:
	@echo "Starting services with Docker Compose..."
	@docker-compose up -d
	@echo "Services started:"
	@echo "  Oriphim API: http://localhost:8000"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana: http://localhost:3000"

docker-down:
	@echo "Stopping Docker services..."
	@docker-compose down

docker-logs:
	@docker-compose logs -f oriphim

docker-build:
	@echo "Building Docker image..."
	@docker-compose build

# ============================================================================
# DATABASE MANAGEMENT
# ============================================================================

reset-db:
	@echo "Resetting database..."
	@rm -f .watcher_demo.db .onboarding.db
	@echo "Database files deleted. Server will create fresh DBs on next startup."

# ============================================================================
# TESTING
# ============================================================================

test:
	@echo "Running unit tests..."
	@$(PYTHON) -m pytest tests/test_*.py -v --tb=short

test-integration:
	@echo "Running integration tests..."
	@$(PYTHON) -m pytest tests/integration/ -v --tb=short

test-e2e:
	@echo "Running end-to-end tests..."
	@$(PYTHON) -m pytest tests/e2e/ -v --tb=short

test-all:
	@echo "Running complete test suite..."
	@$(PYTHON) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term

test-performance:
	@echo "Running performance tests..."
	@if command -v locust &> /dev/null; then \
		echo "Starting server..."; \
		uvicorn app.main:app --port 8001 & \
		SERVER_PID=$$!; \
		sleep 3; \
		echo "Running load test..."; \
		locust -f tests/performance/locustfile.py --host http://localhost:8001 --headless --users 50 --spawn-rate 5 --run-time 1m --csv=results/loadtest; \
		kill $$SERVER_PID; \
	else \
		echo "Error: locust not installed. Run: pip install locust"; \
		exit 1; \
	fi

# ============================================================================
# TENANTS
# ============================================================================

tenant-create:
	@if [ -z "$(NAME)" ] || [ -z "$(DOMAIN)" ]; then \
		echo "Error: NAME and DOMAIN required. Usage: make tenant-create NAME=\"Acme Corp\" DOMAIN=acme.com"; \
		exit 1; \
	fi
	@echo "Creating tenant..."
	@$(PYTHON) scripts/ops_cli/tenants.py create "$(NAME)" $(DOMAIN) $(TIER) $(API_KEY)

tenant-list:
	@echo "Listing tenants..."
	@$(PYTHON) scripts/ops_cli/tenants.py list $(API_KEY)

# ============================================================================
# USERS
# ============================================================================

user-create:
	@if [ -z "$(TENANT)" ] || [ -z "$(EMAIL)" ] || [ -z "$(ROLE)" ]; then \
		echo "Error: TENANT, EMAIL, and ROLE required."; \
		echo "Usage: make user-create TENANT=<id> EMAIL=admin@acme.com ROLE=admin"; \
		exit 1; \
	fi
	@echo "Creating user..."
	@$(PYTHON) scripts/ops_cli/users.py create $(TENANT) $(EMAIL) $(ROLE) $(API_KEY)

user-list:
	@if [ -z "$(TENANT)" ]; then \
		echo "Error: TENANT required. Usage: make user-list TENANT=<tenant_id>"; \
		exit 1; \
	fi
	@echo "Listing users for tenant $(TENANT)..."
	@$(PYTHON) scripts/ops_cli/users.py list $(TENANT) $(API_KEY)

# ============================================================================
# API KEYS
# ============================================================================

key-generate:
	@tenant_id="$(TENANT)"; \
	if [ -z "$$tenant_id" ] && [ -n "$(TENENT)" ]; then \
		tenant_id="$(TENENT)"; \
		echo "Warning: TENENT is deprecated; use TENANT instead."; \
	fi; \
	if [ -z "$$tenant_id" ] || [ -z "$(USER)" ]; then \
		echo "Error: TENANT and USER required."; \
		echo "Usage: make key-generate TENANT=<id> USER=<id> SCOPE=admin"; \
		exit 1; \
	fi; \
	echo "Generating API key..."; \
	$(PYTHON) scripts/ops_cli/keys.py generate "$$tenant_id" "$(USER)" "$(SCOPE)" "$(API_KEY)"

key-list:
	@if [ -z "$(TENANT)" ]; then \
		echo "Error: TENANT required. Usage: make key-list TENANT=<tenant_id>"; \
		exit 1; \
	fi
	@echo "Listing API keys for tenant $(TENANT)..."
	@$(PYTHON) scripts/ops_cli/keys.py list $(TENANT) $(API_KEY)

# ============================================================================
# MONITORING
# ============================================================================

audit-trail:
	@if [ -z "$(TENANT)" ]; then \
		echo "Error: TENANT required. Usage: make audit-trail TENANT=<tenant_id> API_KEY=<key>"; \
		exit 1; \
	fi
	@if [ -z "$(API_KEY)" ]; then \
		echo "Error: API_KEY required. Usage: make audit-trail TENANT=<tenant_id> API_KEY=<key>"; \
		exit 1; \
	fi
	@echo "Viewing audit trail for tenant $(TENANT)..."
	@curl -s "$(BASE_URL)/v1/onboarding/tenants/$(TENANT)/audit-log" -H "Authorization: Bearer $(API_KEY)" | $(PYTHON) -m json.tool

metrics:
	@echo "Viewing system metrics..."
	@curl -s "$(BASE_URL)/v2/health" | $(PYTHON) -m json.tool
