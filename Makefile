# ─── Historia Clínica Distribuida v3.0 ───
# Comandos útiles para microservicios

.PHONY: help build up down logs ps clean

help:
	@echo "Historia Clínica Distribuida - Microservicios"
	@echo ""
	@echo "  make build       → Construye todas las imágenes"
	@echo "  make up          → Levanta todos los servicios"
	@echo "  make down        → Detiene todos los servicios"
	@echo "  make logs        → Sigue logs de todos los servicios"
	@echo "  make ps          → Muestra estado de servicios"
	@echo "  make clean       → Detiene todo y limpia volúmenes"
	@echo "  make gateway     → Logs solo del gateway"
	@echo "  make patient     → Logs solo de patient-service"
	@echo "  make clinical    → Logs solo de clinical-service"
	@echo "  make sync        → Logs solo de sync-service"

build:
	docker compose build --no-cache

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

clean:
	docker compose down -v --rmi all

gateway:
	docker compose logs -f gateway-service

patient:
	docker compose logs -f patient-service

clinical:
	docker compose logs -f clinical-service

sync:
	docker compose logs -f sync-service

shell-gateway:
	docker exec -it gateway_service sh

shell-patient:
	docker exec -it patient_service sh

shell-clinical:
	docker exec -it clinical_service sh

shell-sync:
	docker exec -it sync_service sh
