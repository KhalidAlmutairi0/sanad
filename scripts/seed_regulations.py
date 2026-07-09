"""Load the seed PDPL + Labor Law corpus into regulation_versions with embeddings.

Run inside the api container (has deps + network to db + embedder):
    docker compose -f infra/docker-compose.yml run --rm api python scripts/seed_regulations.py

Idempotent: reruns skip regulations/users/articles that already exist. Each article is
inserted with verified_by = the seed verifier user (the human-gate stand-in) and an
embedding from the self-hosted embedder. Also creates a demo reviewer login.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import os
import pathlib
import sys

import yaml
from sqlalchemy import select

# Allow `import app...` when run as a script from /app.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.core.db import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import Regulation, RegulationVersion, User  # noqa: E402
from app.services.retrieval import embed_texts  # noqa: E402

DATA = pathlib.Path(__file__).resolve().parent / "seed_data" / "regulations.yaml"
# Demo password for seeded logins. Override via env; never a production credential.
DEMO_PASSWORD = os.environ.get("SEED_DEFAULT_PASSWORD", "sanad-dev-password")


async def _get_or_create_user(session, *, email, display_name, role) -> User:
    existing = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing:
        return existing
    user = User(
        email=email,
        display_name=display_name,
        role=role,
        password_hash=hash_password(DEMO_PASSWORD),
    )
    session.add(user)
    await session.flush()
    return user


async def _get_or_create_regulation(session, reg: dict) -> Regulation:
    existing = (
        await session.execute(select(Regulation).where(Regulation.code == reg["code"]))
    ).scalar_one_or_none()
    if existing:
        return existing
    row = Regulation(
        code=reg["code"],
        name_ar=reg["name_ar"],
        name_en=reg["name_en"],
        authority=reg["authority"],
        source_domain=reg["source_domain"],
    )
    session.add(row)
    await session.flush()
    return row


async def main() -> None:
    spec = yaml.safe_load(DATA.read_text(encoding="utf-8"))

    async with SessionLocal() as session:
        verifier = await _get_or_create_user(
            session,
            email=spec["verifier"]["email"],
            display_name=spec["verifier"]["display_name"],
            role=spec["verifier"]["role"],
        )
        # Demo reviewer login for the review workspace.
        await _get_or_create_user(
            session,
            email="reviewer@sanad.local",
            display_name="Compliance Reviewer",
            role="reviewer",
        )

        regs: dict[str, Regulation] = {}
        for reg in spec["regulations"]:
            row = await _get_or_create_regulation(session, reg)
            regs[reg["code"]] = row

        inserted = 0
        for art in spec["articles"]:
            reg = regs[art["regulation"]]
            text_ar = " ".join(art["article_text_ar"].split())
            content_hash = hashlib.sha256(text_ar.encode("utf-8")).hexdigest()

            dup = (
                await session.execute(
                    select(RegulationVersion.id).where(
                        RegulationVersion.regulation_id == reg.id,
                        RegulationVersion.article_ref == art["article_ref"],
                        RegulationVersion.content_hash == content_hash,
                    )
                )
            ).scalar_one_or_none()
            if dup:
                continue

            [embedding] = await embed_texts([text_ar], input_type="passage")
            session.add(
                RegulationVersion(
                    regulation_id=reg.id,
                    article_ref=art["article_ref"],
                    article_text_ar=text_ar,
                    article_text_en=" ".join(art["article_text_en"].split())
                    if art.get("article_text_en")
                    else None,
                    source_url=art["source_url"],
                    content_hash=content_hash,
                    fetched_at=dt.datetime.now(dt.timezone.utc),
                    effective_date=art.get("effective_date"),
                    verified_by=verifier.id,
                    embedding=embedding,
                )
            )
            inserted += 1

        await session.commit()
        print(f"Seed complete: {inserted} new article version(s). Verifier: {verifier.email}")
        print(f"Demo logins (password '{DEMO_PASSWORD}'): reviewer@sanad.local, verifier@sanad.local")


if __name__ == "__main__":
    asyncio.run(main())
