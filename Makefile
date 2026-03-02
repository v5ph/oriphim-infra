# Oriphim Operations CLI
# Make-based interface to backend REST API
# See OPS_CLI_GUIDE.md for complete documentation

.PHONY: help health-check server-start server-stop

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
	@echo ""
	@echo "TESTING:"
	@echo "  make test-quick          - Run Tier 1-2 tests (smoke + critical)"
	@echo "  make test-full           - Run all Tier 1-5 tests"
	@echo "  make test-tier1          - Unit tests only"
	@echo "  make test-tier2          - API integration tests"
	@echo "  make test-tier3          - End-to-end workflows"
	@echo "  make test-tier4          - Load/performance tests"
	@echo "  make test-tier5          - Security/compliance tests"
	@echo ""
	@echo "DEPLOYMENT:"
	@echo "  make deploy-canary       - Start canary deployment (10% traffic)"
	@echo "  make deploy-status       - Check deployment status"
	@echo "  make deploy-rollback ID=<id> - Rollback deployment"
	@echo ""
	@echo "INCIDENTS:"
	@echo "  make incidents-list      - List active incidents"
	@echo "  make incidents-create SEV=<p1|p2|p3> DESC=\"...\" - Create incident"
	@echo "  make incidents-resolve ID=<id> - Resolve incident"
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

# ============================================================================
# TESTING
# ============================================================================

test-quick:
	@echo "Running quick tests (Tier 1-2)..."
	@$(PYTHON) scripts/ops_cli/run_tier.py 1 $(API_KEY)
	@$(PYTHON) scripts/ops_cli/run_tier.py 2 $(API_KEY)

test-full:
	@echo "Running full test suite (Tier 1-5)..."
	@for tier in 1 2 3 4 5; do \
		$(PYTHON) scripts/ops_cli/run_tier.py $$tier $(API_KEY); \
	done

test-tier1:
	@echo "Running Tier 1 tests (unit tests)..."
	@$(PYTHON) scripts/ops_cli/run_tier.py 1 $(API_KEY)

test-tier2:
	@echo "Running Tier 2 tests (API integration)..."
	@$(PYTHON) scripts/ops_cli/run_tier.py 2 $(API_KEY)

test-tier3:
	@echo "Running Tier 3 tests (end-to-end)..."
	@$(PYTHON) scripts/ops_cli/run_tier.py 3 $(API_KEY)

test-tier4:
	@echo "Running Tier 4 tests (load/performance)..."
	@$(PYTHON) scripts/ops_cli/run_tier.py 4 $(API_KEY)

test-tier5:
	@echo "Running Tier 5 tests (security/compliance)..."
	@$(PYTHON) scripts/ops_cli/run_tier.py 5 $(API_KEY)

# ============================================================================
# DEPLOYMENT
# ============================================================================

deploy-canary:
	@echo "Initiating canary deployment..."
	@$(PYTHON) scripts/ops_cli/deploy.py canary $(API_KEY)

deploy-status:
	@echo "Checking deployment status..."
	@$(PYTHON) scripts/ops_cli/deploy.py status $(ID) $(API_KEY)

deploy-rollback:
	@if [ -z "$(ID)" ]; then \
		echo "Error: ID required. Usage: make deploy-rollback ID=<deployment_id>"; \
		exit 1; \
	fi
	@echo "Rolling back deployment $(ID)..."
	@$(PYTHON) scripts/ops_cli/deploy.py rollback $(ID) $(API_KEY)

# ============================================================================
# INCIDENTS
# ============================================================================

incidents-list:
	@echo "Listing active incidents..."
	@$(PYTHON) scripts/ops_cli/incidents.py list $(API_KEY)

incidents-create:
	@if [ -z "$(SEV)" ] || [ -z "$(DESC)" ]; then \
		echo "Error: SEV and DESC required. Usage: make incidents-create SEV=p1 DESC=\"Description\""; \
		exit 1; \
	fi
	@echo "Creating incident..."
	@$(PYTHON) scripts/ops_cli/incidents.py create $(SEV) "$(DESC)" $(API_KEY)

incidents-resolve:
	@if [ -z "$(ID)" ]; then \
		echo "Error: ID required. Usage: make incidents-resolve ID=<incident_id>"; \
		exit 1; \
	fi
	@echo "Resolving incident $(ID)..."
	@$(PYTHON) scripts/ops_cli/incidents.py resolve $(ID) $(API_KEY)

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
	@if [ -z "$(TENANT)" ] || [ -z "$(USER)" ]; then \
		echo "Error: TENANT and USER required."; \
		echo "Usage: make key-generate TENANT=<id> USER=<id> SCOPE=admin"; \
		exit 1; \
	fi
	@echo "Generating API key..."
	@$(PYTHON) scripts/ops_cli/keys.py generate $(TENANT) $(USER) $(SCOPE) $(API_KEY)

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
	@echo "Viewing audit trail..."
	@curl -s $(BASE_URL)/ops/audit/trail $(if $(API_KEY),-H "Authorization: Bearer $(API_KEY)",) | python -m json.tool

metrics:
	@echo "Viewing system metrics..."
	@curl -s $(BASE_URL)/ops/metrics $(if $(API_KEY),-H "Authorization: Bearer $(API_KEY)",) | python -m json.tool
