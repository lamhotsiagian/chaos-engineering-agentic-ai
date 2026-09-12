# Agentic AI Chaos Engineering Lab Makefile
.PHONY: help install test test-unit test-chaos test-regression run-experiments streamlit docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  install          - Install dependencies from requirements.txt"
	@echo "  test             - Run all pytest test suites"
	@echo "  test-unit        - Run unit tests for resilience components"
	@echo "  test-chaos       - Run chaos experiment regression tests"
	@echo "  test-regression  - Run security and idempotency regression tests"
	@echo "  run-experiments  - Execute all 15 chapter chaos experiments sequentially"
	@echo "  streamlit        - Launch the Chaos Engineering Control Dashboard"
	@echo "  docker-up        - Start Ollama and Lab containers via docker-compose"
	@echo "  docker-down      - Tear down Docker containers"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-chaos:
	pytest tests/chaos/ -v

test-regression:
	pytest tests/regression/ -v

run-experiments:
	bash scripts/run_all_experiments.sh

streamlit:
	streamlit run app/streamlit_app.py

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
