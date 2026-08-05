"""
Notificações (exemplo)

Verifica limites simples sobre os atributos que já trafegam no pipeline
e "dispara" um alerta (aqui, só regista na base + loga; troque
`_send_alert` por um envio real de e-mail/push/webhook quando quiser).

Persiste no seu próprio SQLite (data/notifications.db).
"""

import sqlite3

from common.base_consumer import BaseConsumer

DB_PATH = "data/notifications.db"

# ajuste estes limiares conforme o que fizer sentido pro projeto
THRESHOLDS = {
    "co2": 1000,          # ppm
    "temperature": 28.0,  # graus C
}


class NotificationsService(BaseConsumer):
    def __init__(self):
        super().__init__(
            service_name="notifications",
            group_id="notifications-group",
            db_path=DB_PATH,
        )
        self._db = sqlite3.connect(DB_PATH)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id   TEXT NOT NULL,
                attribute   TEXT NOT NULL,
                value       REAL NOT NULL,
                threshold   REAL NOT NULL,
                notified_at TEXT
            )
            """
        )
        self._db.commit()

    def _send_alert(self, entity_id: str, attr: str, value: float, threshold: float) -> None:
        # placeholder: troque por integração real (e-mail, push, webhook...)
        self.log.warning(
            "ALERTA: %s.%s = %.2f ultrapassou o limite de %.2f",
            entity_id, attr, value, threshold,
        )

    def handle_entity(self, entity: dict, notified_at: str) -> None:
        entity_id = entity["id"]

        for attr, threshold in THRESHOLDS.items():
            prop = entity.get(attr)
            if not prop or "value" not in prop:
                continue
            value = float(prop["value"])

            if value > threshold:
                self._send_alert(entity_id, attr, value, threshold)
                self._db.execute(
                    """
                    INSERT INTO alerts (entity_id, attribute, value, threshold, notified_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (entity_id, attr, value, threshold, notified_at),
                )
                self._db.commit()


if __name__ == "__main__":
    NotificationsService().run()