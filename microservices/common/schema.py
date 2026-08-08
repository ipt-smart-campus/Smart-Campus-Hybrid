"""
Contrato do evento que trafega no tópico Kafka.

"""

NOTIFICATION_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "data"],
    "properties": {
        "id": {"type": "string"},
        "type": {"const": "Notification"},
        "subscriptionId": {"type": "string"},
        "notifiedAt": {"type": "string"},
        "data": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id", "type"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                },
            },
        },
    },
}


def validate_notification(payload: dict) -> None:
    """Levanta jsonschema.ValidationError se o payload não seguir o contrato."""
    import jsonschema

    jsonschema.validate(instance=payload, schema=NOTIFICATION_SCHEMA)