"""
Base reutilizável para os três microsserviços consumidores (Billing,
Analytics, Notificações).

"""

import json
import logging
import os
import signal
import sys

from confluent_kafka import Consumer, KafkaError  # type: ignore
from jsonschema import ValidationError

from common.dedupe import DedupeStore
from common.schema import validate_notification

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)


class BaseConsumer:
    def __init__(self, service_name: str, group_id: str, db_path: str):
        self.service_name = service_name
        self.log = logging.getLogger(service_name)

        brokers = os.environ.get("KAFKA_BROKERS", "kafka:9092")
        self.topic = os.environ.get("KAFKA_TOPIC", "context.device")

        self.consumer = Consumer(
            {
                "bootstrap.servers": brokers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
                # commit manual: só avançamos o offset depois de processar
                # (ou decidir ignorar) a mensagem -> nada se perde num crash.
                "enable.auto.commit": False,
            }
        )
        self.dedupe = DedupeStore(db_path)
        self._running = True
        signal.signal(signal.SIGTERM, self._stop)
        signal.signal(signal.SIGINT, self._stop)

    def _stop(self, *_args):
        self.log.info("Sinal de encerramento recebido, parando...")
        self._running = False

    def handle_entity(self, entity: dict, notified_at: str) -> None:
        """Sobrescrever em cada microsserviço com a lógica de negócio."""
        raise NotImplementedError

    def run(self) -> None:
        self.consumer.subscribe([self.topic])
        self.log.info("A consumir tópico '%s' (group.id=%s)...", self.topic, self.consumer)

        while self._running:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                self.log.error("Erro no consumer: %s", msg.error())
                continue

            try:
                payload = json.loads(msg.value().decode("utf-8"))
                validate_notification(payload)
            except (json.JSONDecodeError, ValidationError) as exc:
                self.log.warning("Mensagem fora do contrato, a ignorar: %s", exc)
                self.consumer.commit(msg)
                continue

            notified_at = payload.get("notifiedAt", "")
            for entity in payload.get("data", []):
                entity_id = entity.get("id", "")
                key = self.dedupe.make_key(entity_id, notified_at)

                if self.dedupe.already_processed(key):
                    self.log.debug("Evento duplicado, a ignorar: %s", key)
                    continue

                try:
                    self.handle_entity(entity, notified_at)
                    self.dedupe.mark_processed(key, entity_id)
                except Exception:
                    self.log.exception("Falha ao processar entidade %s", entity_id)
                    # não marca como processado -> pode ser reprocessado depois
                    # (mas ainda fazemos commit do offset abaixo: trade-off
                    # simples de at-least-once sem travar o consumer;
                    # para retry automático, um dead-letter topic seria o próximo passo)

            self.consumer.commit(msg)

        self.log.info("A encerrar consumer...")
        self.consumer.close()
        self.dedupe.close()
        sys.exit(0)