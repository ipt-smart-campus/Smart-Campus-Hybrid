#!/usr/bin/env bash
set -euo pipefail

IOTA="http://localhost:4041"
ORION="http://localhost:1026"
# NOTA: hostname da rede Docker interna, não localhost (ver test-fase1-orion.sh)
CONTEXT_LINK='Link: <http://context/campus-context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
cd "$(dirname "$0")/.."

# Detecta se o comando disponível é 'python' ou 'python3'
# (no Windows normalmente é só 'python'; em Linux/WSL geralmente 'python3')
# Detecta o Python funcional (não basta 'existir' no PATH: o Windows tem um
# stub 'python3.exe' da Microsoft Store que aparece no PATH mas não funciona
# de verdade — por isso testamos executando, não só checando command -v).
PYTHON_BIN=""
for candidate in python python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "import sys" >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done
if [ -z "$PYTHON_BIN" ]; then
  echo "ERRO: Python não encontrado no PATH."
  echo "Instale em https://www.python.org/downloads/ marcando 'Add python.exe to PATH',"
  echo "depois abra um NOVO terminal e rode este script de novo."
  exit 1
fi

echo "==> 1. IoT Agent está de pé?"
curl -s "$IOTA/iot/about"
echo

echo -e "\n==> 2. Provisionar service group (409 Conflict é normal se script foi corrido anteriormente)"
curl -iX POST "$IOTA/iot/services" \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' \
  -H 'Content-Type: application/json' \
  -d @iot-agent/provisioning/service-group.json

echo -e "\n\n==> 4. Provisionar device simulado (409 Conflict é normal se script foi corrido anteriormente)"
curl -iX POST "$IOTA/iot/devices" \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' \
  -H 'Content-Type: application/json' \
  -d @iot-agent/provisioning/device-indoor-sensor.json

echo -e "\n\n==> 4. Enviar leituras simuladas via MQTT (precisa de 'pip install paho-mqtt')"
"$PYTHON_BIN" scripts/simulate-sensor.py --host localhost --count 3 --interval 3

echo -e "\n==> 5. Confirmar no Orion-LD que a entidade foi criada/atualizada"
# NOTA: o IoT Agent provisiona sob o tenant NGSI-LD "openiot" (fiware-service
# usado no provisioning + IOTA_FALLBACK_TENANT). Sem o header NGSILD-Tenant
# a query vai ao tenant "vazio" (default) e a entidade parece não existir.
sleep 2
curl -s -G "$ORION/ngsi-ld/v1/entities/urn:ngsi-ld:IndoorEnvironmentObserved:B1-101-sensor01" \
  -H 'NGSILD-Tenant: openiot' \
  -H "$CONTEXT_LINK" | "$PYTHON_BIN" -m json.tool

echo -e "\n==> Fase 2 OK se aparecerem 'temperature', 'humidity', 'pressure' e 'co2' com valores no JSON acima."