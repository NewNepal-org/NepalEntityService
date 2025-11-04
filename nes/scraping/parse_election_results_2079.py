import asyncio
import json
import re
from hashlib import md5
from datetime import datetime, UTC

import aiohttp
from unidecode import unidecode

from nes.core.models.base import Name
from nes.core.models.entity import Person, PoliticalParty
from nes.core.models.relationship import Relationship
from nes.core.models.version import Actor, VersionSummary
from nes.database.file_database import FileDatabase

ELECTION_URL = "https://result.election.gov.np/JSONFiles/ElectionResultCentral2079.txt"
ATTRIBUTION = "Election Commission Nepal, २०७९ BS election results"

def decode_nepali(text: str) -> str:
    if not text:
        return ""
    try:
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

def clean_str(value: str) -> str:
    if value is None:
        return ""
    v = value.strip()
    if v == "-" or v == "":
        return ""
    return v

def slugify(name: str) -> str:
    ascii_name = unidecode(name or "").lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", ascii_name)
    slug = re.sub(r"[-\s]+", "-", slug).strip("-")
    return slug

def make_slug_from(value: str, fallback_seed: str) -> str:
    s = slugify(value)
    return s if s else md5(fallback_seed.encode("utf-8")).hexdigest()[:12]

async def ingest():
    db = FileDatabase("entity-db")
    actor = Actor(slug="election-importer", name="Election Results Importer")
    await db.put_actor(actor)

    # Fetch JSON with basic hardening
    async with aiohttp.ClientSession(
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=aiohttp.ClientTimeout(total=60),
    ) as session:
        async with session.get(ELECTION_URL) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise RuntimeError(f"Failed to fetch data: {resp.status} {resp.reason}; body snippet: {body[:200]!r}")
            raw = await resp.read()
            text = raw.decode("utf-8", errors="ignore").strip()
            if not text:
                raise RuntimeError("Fetched empty response body from election endpoint")
            data = json.loads(text)

    created = 0
    now = datetime.now(UTC)

    independent_aliases = {"", "स्वतन्त्र", "Independent", "independent", "IND", "Independents"}

    for rec in data:
        # Candidate
        raw_name = rec.get("CandidateName", "")
        cand_name = decode_nepali(clean_str(raw_name))
        if not cand_name:
            continue
        cand_slug = make_slug_from(cand_name, f"person:{raw_name}")

        # Party
        raw_party = rec.get("PoliticalPartyName", "")
        party_name_ne = decode_nepali(clean_str(raw_party))
        if party_name_ne in independent_aliases:
            party_name_ne = "स्वतन्त्र"
            party_slug = "independent"
        else:
            party_slug = make_slug_from(party_name_ne, f"party:{raw_party}")

        # Locations and misc
        district = decode_nepali(clean_str(rec.get("DistrictName", "")))
        state = decode_nepali(clean_str(rec.get("StateName", "")))
        votes = rec.get("TotalVoteReceived")

        # Upsert Political Party
        party_entity = PoliticalParty(
            slug=party_slug,
            names=[Name(kind="DEFAULT", value=party_name_ne, lang="ne")],
            createdAt=now,
            versionSummary=VersionSummary(
                entityOrRelationshipId=f"entity:organization/political_party/{party_slug}",
                type="ENTITY",
                versionNumber=1,
                actor=actor,
                changeDescription="Imported from election results २०७९",
                createdAt=now,
            ),
            attributes={
                "sys:election_year": 2079,
            },
            attributions=[ATTRIBUTION],
        )
        await db.put_entity(party_entity)
        version_party = VersionSummary.model_validate(
            dict(
                **party_entity.versionSummary.model_dump(),
                snapshot=party_entity.model_dump(),
                changes={},
            ),
            extra="ignore",
        )
        await db.put_version(version_party)

        # Build person attributes (rich set from commission file)
        person_attrs = {
            "sys:gender": decode_nepali(clean_str(rec.get("Gender", ""))),
            "sys:age": rec.get("Age"),
            "sys:political_party": party_name_ne,            # Nepali
            "sys:political_party_slug": party_slug,          # ASCII key
            "sys:symbol_id": rec.get("SymbolID"),
            "sys:symbol_name": decode_nepali(clean_str(rec.get("SymbolName", ""))),
            "sys:candidate_id": rec.get("CandidateID"),
            "sys:district_code": rec.get("DistrictCd"),
            "sys:district": district,
            "sys:state_code": rec.get("State"),
            "sys:state": state,
            "sys:sc_constituency_id": rec.get("SCConstID"),
            "sys:center_constituency_id": rec.get("CenterConstID"),
            "sys:serial_no": rec.get("SerialNo"),
            "sys:votes_received": votes,
            "sys:rank": rec.get("Rank"),
            "sys:remarks": decode_nepali(clean_str(rec.get("Remarks", ""))),
            "sys:dob_bs": rec.get("DOB"),
            "sys:citizenship_district": decode_nepali(clean_str(rec.get("CTZDIST", ""))),
            "sys:father_name": decode_nepali(clean_str(rec.get("FATHER_NAME", ""))),
            "sys:spouse_name": decode_nepali(clean_str(rec.get("SPOUCE_NAME", ""))),
            "sys:qualification": decode_nepali(clean_str(rec.get("QUALIFICATION", ""))),
            "sys:experience": decode_nepali(clean_str(rec.get("EXPERIENCE", ""))),
            "sys:institute": decode_nepali(clean_str(rec.get("NAMEOFINST", ""))),
            "sys:address": decode_nepali(clean_str(rec.get("ADDRESS", ""))),
            "sys:election_year": 2079,
        }

        # Create Person
        person_entity = Person(
            slug=cand_slug,
            names=[Name(kind="DEFAULT", value=cand_name, lang="ne")],
            createdAt=now,
            versionSummary=VersionSummary(
                entityOrRelationshipId=f"entity:person/{cand_slug}",
                type="ENTITY",
                versionNumber=1,
                actor=actor,
                changeDescription="Imported candidate result from election २०७९",
                createdAt=now,
            ),
            attributes=person_attrs,
            attributions=[ATTRIBUTION],
        )
        await db.put_entity(person_entity)
        version_person = VersionSummary.model_validate(
            dict(
                **person_entity.versionSummary.model_dump(),
                snapshot=person_entity.model_dump(),
                changes={},
            ),
            extra="ignore",
        )
        await db.put_version(version_person)

        # Person → Party Relationship
        rel_entity = Relationship(
            sourceEntityId=person_entity.id,
            targetEntityId=party_entity.id,
            type="MEMBER_OF",
            createdAt=now,
            versionSummary=VersionSummary(
                entityOrRelationshipId=f"relationship/{cand_slug}-to-{party_slug}-member_of",
                type="RELATIONSHIP",
                versionNumber=1,
                actor=actor,
                changeDescription="Candidate → Party membership",
                createdAt=now,
            ),
            attributions=[ATTRIBUTION],
        )
        await db.put_relationship(rel_entity)
        version_rel = VersionSummary.model_validate(
            dict(
                **rel_entity.versionSummary.model_dump(),
                snapshot=rel_entity.model_dump(),
                changes={},
            ),
            extra="ignore",
        )
        await db.put_version(version_rel)

        created += 1
        if created % 100 == 0:
            print(f"{created} candidates processed")

    print(f"Finished ingestion: {created} candidates")

if __name__ == "__main__":
    asyncio.run(ingest())