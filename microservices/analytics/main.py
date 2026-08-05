"""
Analytics (exemplo)

Mantém, por entidade, a média corrente de temperature/humidity/co2 (as
métricas que já trafegam de fato pelo pipeline). Guarda soma + contagem
por atributo, pra calcular a média sem reprocessar o histórico inteiro
a cada evento.

Persiste no seu próprio SQLite (data/analytics.db).
"""

import sqlite3

from common.base_consumer import BaseConsumer

DB_PATH = "data/analytics.db"
TRACKED_ATTRS = ["temperature", "humidity", "pressure", "co2"]


class AnalyticsService(BaseConsumer):
    def __init__(self):
        super().__init__(
            service_name="analytics",
            group_id="analytics-group",
            db_path=DB_PATH,
        )
        self._db = sqlite3.connect(DB_PATH)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS attribute_stats (
                entity_id TEXT NOT NULL,
                attribute TEXT NOT NULL,
                sum_value REAL NOT NULL DEFAULT 0,
                count     INTEGER NOT NULL DEFAULT 0,
                last_value REAL,
                last_update TEXT,
                PRIMARY KEY (entity_id, attribute)
            )
            """
        )
        self._db.commit()

    def handle_entity(self, entity: dict, notified_at: str) -> None:
        entity_id = entity["id"]

        for attr in TRACKED_ATTRS:
            prop = entity.get(attr)
            if not prop or "value" not in prop:
                continue
            value = float(prop["value"])

            self._db.execute(
                """
                INSERT INTO attribute_stats (entity_id, attribute, sum_value, count, last_value, last_update)
                VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(entity_id, attribute) DO UPDATE SET
                    sum_value = sum_value + excluded.last_value,
                    count = count + 1,
                    last_value = excluded.last_value,
                    last_update = excluded.last_update
                """,
                (entity_id, attr, value, value, notified_at),
            )
            self._db.commit()

            row = self._db.execute(
                "SELECT sum_value, count FROM attribute_stats WHERE entity_id=? AND attribute=?",
                (entity_id, attr),
            ).fetchone()
            avg = row[0] / row[1]
            self.log.info(
                "Analytics: %s.%s = %.2f (média corrente: %.2f, n=%d)",
                entity_id, attr, value, avg, row[1],
            )


if __name__ == "__main__":
    AnalyticsService().run()