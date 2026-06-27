from models import AuditLog


async def log_action(
    db,
    action_type: str,
    entity_type: str,
    entity_id: str,
    entity_name: str,
    description: str,
):
    db.add(AuditLog(
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        description=description,
    ))
    # Caller commits the session — audit entry is part of the same transaction.
