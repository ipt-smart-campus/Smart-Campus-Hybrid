#!/usr/bin/env bash
# Fase 1 - testa criação e query de entidades no Orion-LD.
set -euo pipefail

ORION="http://localhost:1026"
CONTEXT_LINK='Link: <http://context/campus-context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'

echo "==> 1. Versão do Orion-LD"
curl -s "$ORION/version" | head -c 300; echo

echo -e "\n==> 2. Criar entidade Building"
curl -iX POST "$ORION/ngsi-ld/v1/entities" \
  -H 'Content-Type: application/json' \
  -H "$CONTEXT_LINK" \
  -d '{
    "id": "urn:ngsi-ld:Building:B1",
    "type": "Building",
    "name": { "type": "Property", "value": "Edificio A" },
    "location": { "type": "GeoProperty", "value": { "type": "Point", "coordinates": [-8.5382, 39.4784] } }
  }'

echo -e "\n\n==> 3. Criar entidade Room (com relação a Building)"
curl -iX POST "$ORION/ngsi-ld/v1/entities" \
  -H 'Content-Type: application/json' \
  -H "$CONTEXT_LINK" \
  -d '{
    "id": "urn:ngsi-ld:Room:B1-101",
    "type": "Room",
    "name": { "type": "Property", "value": "Sala 101" },
    "refBuilding": { "type": "Relationship", "object": "urn:ngsi-ld:Building:B1" },
    "floor": { "type": "Property", "value": 1 },
    "capacity": { "type": "Property", "value": 40 },
    "occupied": { "type": "Property", "value": false }
  }'

echo -e "\n\n==> 4. Query: todas as entidades Room"
curl -s -G "$ORION/ngsi-ld/v1/entities" \
  -H "$CONTEXT_LINK" \
  --data-urlencode "type=Room" | python3 -m json.tool

echo -e "\n==> Fase 1 OK: Orion-LD a criar e devolver entidades corretamente."
