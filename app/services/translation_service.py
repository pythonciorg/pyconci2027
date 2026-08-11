import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.translation import Translation

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_deepl_client():
    if not settings.deepl_api_key:
        return None
    import deepl
    return deepl.Translator(settings.deepl_api_key)


async def auto_translate_and_store(
    db: AsyncSession,
    entity_type: str,
    entity_id: int,
    fields: dict[str, str],
    source_lang: str = "FR",
    target_lang: str = "EN-US",
):
    """Traduit automatiquement les champs fournis et les stocke dans la table translations.
    Ne fait rien (silencieusement) si aucune clé DeepL n'est configurée."""
    client = _get_deepl_client()
    if client is None:
        logger.info("DeepL non configuré — traduction automatique ignorée pour %s#%s", entity_type, entity_id)
        return

    for field_name, text in fields.items():
        if not text:
            continue
        try:
            result = client.translate_text(text, source_lang=source_lang, target_lang=target_lang)
            translated_value = result.text
        except Exception as exc:
            logger.warning("Échec traduction DeepL pour %s.%s: %s", entity_type, field_name, exc)
            continue

        existing = await db.execute(
            select(Translation).filter_by(
                entity_type=entity_type, entity_id=entity_id, language="en", field=field_name
            )
        )
        translation = existing.scalar_one_or_none()

        if translation:
            translation.value = translated_value
        else:
            db.add(
                Translation(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    language="en",
                    field=field_name,
                    value=translated_value,
                )
            )

    await db.commit()