#!/bin/bash
# Testa o pipeline Orion -> Draco (NiFi) -> Kafka
set -e

ORION_URL="http://localhost:1026"
ENTITY_ID="urn:ngsi-ld:Device:indoor001"   # ajuste para um ID que já exista no seu Orion
KAFKA_TOPIC="context.device"

echo "1) Criando subscription no Orion apontando para o Draco..."
curl -s -X POST "${ORION_URL}/ngsi-ld/v1/subscriptions" \
  -H "Content-Type: application/json" \
  -d @subscription-draco.json
echo -e "\n"

echo "2) Atualizando atributo temperature na entidade ${ENTITY_ID}..."
curl -s -X PATCH "${ORION_URL}/ngsi-ld/v1/entities/${ENTITY_ID}/attrs" \
  -H "Content-Type: application/ld+json" \
  -d '{
        "temperature": { "type": "Property", "value": 27.5 },
        "@context": "http://context/campus-context.jsonld"
      }'
echo -e "\n"

echo "3) Lendo mensagens do tópico Kafka '${KAFKA_TOPIC}' (Ctrl+C para sair)..."
docker exec -it kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic "${KAFKA_TOPIC}" \
  --from-beginning \
  --max-messages 5