"""
Billing (exemplo)

Ainda não há um sensor de consumo energético publicando no tópico
(EnergyConsumptionSensor está definido no @context, mas não provisionado
no IoT Agent ainda). Como exemplo funcional de "cobrança por uso", este
serviço conta quantas leituras cada sala gerou e guarda isso como uma
métrica de "unidades de uso" acumuladas por entidade — troque
`_apply_billing_rule` pela fórmula real assim que o sensor de energia
existir (ex: integrar powerConsumption ao longo do tempo).

Persiste no seu próprio SQLite (data/billing.db) — nenhum outro
microsserviço lê ou escreve nesse arquivo.
"""

import sqlite3

from common.base_consumer import BaseConsumer

DB_PATH = "data/billing.db"


class BillingService(BaseConsumer):
    def __init__(self):
        super().__init__(
            service_name="billing",
            group_id="billing-group",
            db_path=DB_PATH,
        )
        self._db = sqlite3.connect(DB_PATH)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_units (
                entity_id    TEXT PRIMARY KEY,
                units        INTEGER NOT NULL DEFAULT 0,
                last_update  TEXT
            )
            """
        )
        self._db.commit()

    def _apply_billing_rule(self, entity: dict) -> int:
        # placeholder: 1 "unidade de uso" por leitura recebida.
        # troque por algo como diferença de powerConsumption quando existir.
        return 1

    def handle_entity(self, entity: dict, notified_at: str) -> None:
        entity_id = entity["id"]
        units = self._apply_billing_rule(entity)

        self._db.execute(
            """
            INSERT INTO usage_units (entity_id, units, last_update)
            VALUES (?, ?, ?)
            ON CONFLICT(entity_id) DO UPDATE SET
                units = units + excluded.units,
                last_update = excluded.last_update
            """,
            (entity_id, units, notified_at),
        )
        self._db.commit()
        self.log.info("Billing: %s +%d unidade(s) (id=%s)", entity_id, units, entity_id)


if __name__ == "__main__":
    BillingService().run()