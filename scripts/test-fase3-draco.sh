#!/bin/bash
# test-fase3-draco.sh
# Testa o pipeline Orion -> Draco (NiFi) -> Kafka
# Rode a partir da raiz do projeto (Smart-Campus-Hybrid)
set -e

ORION_URL="http://localhost:1026"
ENTITY_ID="urn:ngsi-ld:IndoorEnvironmentObserved:B1-101-sensor01"
KAFKA_TOPIC="context.device"
SUBSCRIPTION_FILE="iot-agent/provisioning/sub_draco.json"
cd "$(dirname "$0")/.."

echo "1) Criando subscription no Orion apontando para o Draco..."
curl -s -X POST "${ORION_URL}/ngsi-ld/v1/subscriptions" \
  -H "Content-Type: application/ld+json" \
  -H "NGSILD-Tenant: openiot" \
  -d @"${SUBSCRIPTION_FILE}"
echo -e "\n"

echo "2) Listando subscriptions para conferir..."
curl -s "${ORION_URL}/ngsi-ld/v1/subscriptions" -H "NGSILD-Tenant: openiot" | jq . 2>/dev/null || curl -s "${ORION_URL}/ngsi-ld/v1/subscriptions" -H "NGSILD-Tenant: openiot"
echo -e "\n"

echo "3) Tentando atualizar temperature na entidade ${ENTITY_ID}..."
echo "   (se a entidade ainda não existe, rode antes: bash scripts/test-fase2-iotagent.sh)"
curl -s -X PATCH "${ORION_URL}/ngsi-ld/v1/entities/${ENTITY_ID}/attrs" \
  -H "Content-Type: application/ld+json" \
  -H "NGSILD-Tenant: openiot" \
  -d '{
        "temperature": { "type": "Property", "value": 27.5 },
        "@context": "http://context/campus-context.jsonld"
      }' || echo "   PATCH falhou -- provavelmente a entidade ainda não existe no Orion."
echo -e "\n"

echo "4) Lendo mensagens do tópico Kafka '${KAFKA_TOPIC}' (Ctrl+C para sair)..."
# MSYS_NO_PATHCONV=1 evita que o Git Bash "traduza" /opt/kafka/... pra um caminho Windows
MSYS_NO_PATHCONV=1 docker exec -it sc-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic "${KAFKA_TOPIC}" \
  --from-beginning \
  --max-messages 5