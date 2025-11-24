"""
Migration: 006-source-hospitals-nepal
Description: Import hospitals (government and public) from https://nhfr.mohp.gov.np/
Author: Subash Rijal
Date: 2025-01-23
"""

from datetime import datetime, timezone

from nes.core.models import (
    Address,
    Attribution,
    ExternalIdentifier,
    LangText,
    LangTextValue,
    Name,
    NameParts,
)
from nes.core.models.base import NameKind
from nes.core.models.entity import EntitySubType, EntityType
from nes.core.models.version import Author
from nes.core.utils.slug_helper import text_to_slug
from nes.services.migration.context import MigrationContext
from nes.services.scraping.normalization import NameExtractor

# Migration metadata
AUTHOR = "Subash Rijal"
DATE = "2025-01-23"
DESCRIPTION = "Import hospitals from nhfr.mohp.gov.np"
CHANGE_DESCRIPTION = "Initial sourcing from nhfr.mohp.gov.np"

name_extractor = NameExtractor()


async def migrate(context: MigrationContext) -> None:
    """
    Import hospitals from nhfr.mohp.gov.np

    Data source: nhfr.mohp.gov.np
    """
    context.log("Migration started: Importing hospitals from nhfr.mohp.gov.np")

    # Create author
    author = Author(slug=text_to_slug(AUTHOR), name=AUTHOR)
    await context.db.put_author(author)
    author_id = author.id
    context.log(f"Created author: {author.name} ({author_id})")

    # Load hospitals from pre-scraped data file
    context.log("Loading hospitals from source data...")
    try:
        hospitals = context.read_json("source/hospitals.json")
        context.log(f"Loaded {len(hospitals)} health facilities from source/hospitals.json")
    except FileNotFoundError:
        context.log("ERROR: source/hospitals.json not found.")
        context.log("Please run: cd migrations/006-source-hospitals && poetry run python scrape_nhfr.py")
        context.log("to scrape and save hospital data first.")
        raise

    if not hospitals:
        context.log("WARNING: No hospitals in source data. Migration may be incomplete.")
        return

    count = 0
    skipped_count = 0
    linked_count = 0
    relationships_count = 0

    # Hospital data keys
    # 'id', 'hf_code', 'hf_name', 
    # 'type', 'healthFacilityType', 'services',
    #  'opdServices', 'surgicalServices', 'radiologyServices', 
    # 'laboratoryServices', 'specializedServices', 'ayurvedServices', 
    # 'familyPlanningServices', 'safeMotherhoodServices', 'bipannaServices', 
    # 'token', 'authlevel', 'c_hf_name', 'submitto', 
    # 'health_services', 'oxygen', 'plant_capacity', 'cylinder', 
    # 'concentrator', 'ambulance', 'ambulance_category', 'ambulance_contact', 
    # 'ocmc', 'ssu', 'geriatrics', 'ehs', 'pharmacy', 'insurance', 'contact_person',
    #  'contact_person_mobile', 'level', 'healthFacilityLevel', 'oldHealthFacilityLevel', 
    # 'ownership', 'ownerships', 'sectioned', 'functional', 'icu_sectioned', 'icu_functional', 
    # 'ventilator_sectioned', 'ventilator_functional', 'hdu_sectioned', 'hdu_functional', 'nicu_sectioned',
    #  'nicu_functional', 'onlinestatus', 'org_source', 'other_source', 'loan_org', 'building_cost', 'device_cost',
    #  'workforce_cost', 'est_income', 'property_source', 'deviceitems', 'owneritems', 'workeritems', 'rtype', 'hcode',
    #  'internet', 'hmis_code', 'province', 'provinces', 'ftype', 'ftypes', 'district', 'districts', 'municipality', 'municipalitys',
    #  'ward', 'opstatus', 'latitude', 'longitude', 'estd_date', 'email', 'website', 'telephone', 'ren_date', 'validity', 'ucode',
    #  'cbscode', 'reg_orgs', 'org_articles', 'vat_pans', 'org_perms', 'mem_citizenships', 'iee_certs', 'hf_details', 'service_fees', 
    # 'building_maps', 'tax_clears'

    for hospital_data in hospitals:
        # log all hospital_data keys
        context.log(f"Hospital data keys: {hospital_data.keys()}")
        try:
            # Extract basic information from NHFR data format
            name_en = hospital_data.get("hf_name", "").strip()
            if not name_en:
                skipped_count += 1
                continue

            # Get facility details
            hf_code = hospital_data.get("hf_code")
            hf_id = hospital_data.get("id")
            
            # Get Nepali name if available
            name_ne = hospital_data.get("c_hf_name", "").strip()
            
            # Extract location information
            district_name = ""
            municipality_name = ""
            ward = hospital_data.get("ward", "")
            
            if "districts" in hospital_data and hospital_data["districts"]:
                district_name_raw = hospital_data["districts"].get("nameen", "")
                district_name = district_name_raw.strip() if district_name_raw else ""
            
            if "municipalitys" in hospital_data and hospital_data["municipalitys"]:
                municipality_name_raw = hospital_data["municipalitys"].get("nameen", "")
                municipality_name = municipality_name_raw.strip() if municipality_name_raw else ""
            
            province_name = ""
            if "provinces" in hospital_data and hospital_data["provinces"]:
                province_name_raw = hospital_data["provinces"].get("nameen", "")
                province_name = province_name_raw.strip() if province_name_raw else ""
            
            # Build location components
            location_components = []
            if municipality_name:
                if ward:
                    location_components.append(f"{municipality_name}, Ward {ward}")
                else:
                    location_components.append(municipality_name)
            if district_name and district_name not in location_components:
                location_components.append(district_name)
            if province_name and province_name not in location_components:
                location_components.append(province_name)
            
            # Extract facility type and level
            facility_type = "Unknown"
            if "healthFacilityType" in hospital_data and hospital_data["healthFacilityType"]:
                facility_type = hospital_data["healthFacilityType"].get("type_name", "Unknown")
            
            facility_level = ""
            if "healthFacilityLevel" in hospital_data and hospital_data["healthFacilityLevel"]:
                facility_level = hospital_data["healthFacilityLevel"].get("name", "")
            
            # Extract ownership
            ownership = "Unknown"
            if "ownerships" in hospital_data and hospital_data["ownerships"]:
                ownership = hospital_data["ownerships"].get("name", "Unknown")
            
            # Extract bed information
            beds_sectioned = hospital_data.get("sectioned")
            beds_functional = hospital_data.get("functional")
            beds = None
            if beds_functional:
                try:
                    beds = int(beds_functional)
                except (ValueError, TypeError):
                    pass
            elif beds_sectioned:
                try:
                    beds = int(beds_sectioned)
                except (ValueError, TypeError):
                    pass
            
            # Extract contact information
            contact_person = hospital_data.get("contact_person", "")
            contact_mobile = hospital_data.get("contact_person_mobile", "")
            
            # Extract coordinates
            latitude = hospital_data.get("latitude", "")
            longitude = hospital_data.get("longitude", "")
            
            # Build address text
            address_parts = []
            if municipality_name:
                if ward:
                    address_parts.append(f"{municipality_name}, Ward {ward}")
                else:
                    address_parts.append(municipality_name)
            if district_name:
                address_parts.append(district_name)
            if province_name:
                address_parts.append(province_name)
            address_text = ", ".join(address_parts)
            
            # Use the primary location for linking (district or municipality)
            location_name = district_name or municipality_name

            # Normalize ownership
            ownership_normalized = _normalize_ownership(ownership)

            # Build names - ensure we always have at least English name
            if not name_en:
                context.log(f"WARNING: Hospital has no name, skipping")
                continue
            
            # Standardize and clean the name
            name_en_clean = name_extractor.standardize_name(name_en)
            
            names = [
                Name(
                    kind=NameKind.PRIMARY,
                    en=NameParts(full=name_en_clean),
                    ne=NameParts(full=name_ne) if name_ne else None,
                ).model_dump()
            ]

            # Build identifiers (NHFR facility code and ID)
            identifiers = []
            if hf_code:
                identifiers.append(
                    ExternalIdentifier(
                        scheme="other",
                        value=str(hf_code),
                        url=f"https://nhfr.mohp.gov.np/health-facility/{hf_code}",
                        name=LangText(
                            en=LangTextValue(value="NHFR Facility Code", provenance="human"),
                        ),
                    )
                )
            if hf_id:
                identifiers.append(
                    ExternalIdentifier(
                        scheme="other",
                        value=str(hf_id),
                        name=LangText(
                            en=LangTextValue(value="NHFR ID", provenance="human"),
                        ),
                    )
                )

            # Build attributions
            attribution_details = f"Imported from Nepal Health Facility Registry (https://nhfr.mohp.gov.np/) on {datetime.now(timezone.utc).date()}"
            attributions = [
                Attribution(
                    title=LangText(
                        en=LangTextValue(value="Nepal Health Facility Registry", provenance="human"),
                        ne=LangTextValue(value="नेपाल स्वास्थ्य सुविधा रजिस्ट्री", provenance="human"),
                    ),
                    details=LangText(
                        en=LangTextValue(value=attribution_details, provenance="human"),
                        ne=LangTextValue(
                            value=f"नेपाल स्वास्थ्य सुविधा रजिस्ट्री (https://nhfr.mohp.gov.np/) बाट {datetime.now(timezone.utc).date()} मा आयात गरिएको",
                            provenance="human"
                        ),
                    ),
                )
            ]

            # Build address with location linking
            # Try to match each location component to location entities
            location_id = None
            location_entity = None
            province_id = None
            province_entity = None
            matched_components = []

            # Process location_components array to find matching location entities
            for component in location_components:
                if not component or component in matched_components:
                    continue
                
                component_clean = component.strip()
                if not component_clean:
                    continue
                
                # Try to match as province first
                if "province" in component_clean.lower() or component_clean in ["Koshi", "Madhesh", "Bagmati", "Gandaki", "Lumbini", "Karnali", "Sudurpashchim"]:
                    province_query = component_clean.replace(" Province", "").strip()
                    province_results = await context.search.search_entities(
                        query=province_query,
                        entity_type="location",
                        sub_type="province",
                        limit=5,
                    )
                    if province_results and not province_id:
                        # Find best match
                        for result in province_results:
                            # Check if names match
                            if result.names[0].en and province_query.lower() in result.names[0].en.full.lower():
                                province_id = result.id
                                province_entity = result
                                matched_components.append(component_clean)
                                context.log(f"  Matched province component '{component_clean}' to {result.names[0].en.full}")
                                break
                        # If no exact match found, use first result
                        if not province_id and province_results:
                            province_id = province_results[0].id
                            province_entity = province_results[0]
                            matched_components.append(component_clean)
                            context.log(f"  Matched province component '{component_clean}' to {province_results[0].names[0].en.full if province_results[0].names[0].en else 'unknown'}")
                
                # Try to match as district/city/municipality
                elif not location_id:
                    location_results = await context.search.search_entities(
                        query=component_clean,
                        entity_type="location",
                        limit=5,
                    )
                    
                    if location_results:
                        # Find best match (prefer district or city)
                        for result in location_results:
                            if result.sub_type in ["district", "metropolitan_city", "sub_metropolitan_city", "municipality", "rural_municipality"]:
                                location_id = result.id
                                location_entity = result
                                linked_count += 1
                                matched_components.append(component_clean)
                                location_name_display = result.names[0].en.full if result.names[0].en else "unknown"
                                context.log(f"  Matched location component '{component_clean}' to {location_name_display}")
                                break
            
            # Fallback: Try primary location_name if no match found from components
            if not location_id and location_name and location_name not in matched_components:
                location_results = await context.search.search_entities(
                    query=location_name,
                    entity_type="location",
                    limit=5,
                )
                if location_results:
                    for result in location_results:
                        if result.sub_type in ["district", "metropolitan_city", "sub_metropolitan_city", "municipality"]:
                            location_id = result.id
                            location_entity = result
                            linked_count += 1
                            location_name_display = result.names[0].en.full if result.names[0].en else "unknown"
                            context.log(f"Linked {name_en} to location: {location_name_display}")
                            break
            
            # Fallback: Try primary province_name if no match found from components
            if not province_id and province_name and province_name not in matched_components:
                province_query = province_name.replace(" Province", "").strip()
                province_results = await context.search.search_entities(
                    query=province_query,
                    entity_type="location",
                    sub_type="province",
                    limit=5,
                )
                if province_results:
                    for result in province_results:
                        if result.names[0].en and province_query.lower() in result.names[0].en.full.lower():
                            province_id = result.id
                            province_entity = result
                            break
                    if not province_id and province_results:
                        province_id = province_results[0].id
                        province_entity = province_results[0]

            # Build address description
            address = None
            if address_parts := ([address_text] if address_text else []) + ([location_name] if location_name else []) + ([province_name] if province_name else []):
                # Filter out empty strings
                address_parts_clean = [part for part in address_parts if part]
                if address_parts_clean:
                    address = Address(
                        description2=LangText(
                            en=LangTextValue(value=" / ".join(address_parts_clean), provenance="imported"),
                            ne=LangTextValue(value=" / ".join(address_parts_clean), provenance="imported"),
                        ),
                        location_id=location_id,
                    )

            # Build description (from facility level and type)
            description = None
            description_parts = []
            if facility_level:
                description_parts.append(facility_level)
            if facility_type and facility_type != "Unknown":
                description_parts.append(f"({facility_type})")
            
            if description_parts:
                description_text = " ".join(description_parts)
                description = LangText(
                    en=LangTextValue(value=description_text, provenance="imported"),
                )

            # Build entity data
            entity_data = dict(
                slug=text_to_slug(name_en),
                names=names,
                attributions=attributions,
                identifiers=identifiers if identifiers else None,
                description=description.model_dump() if description else None,
            )
            
            # Add Hospital-specific fields (only if not None)
            if beds is not None:
                entity_data["beds"] = beds
            
            if ownership_normalized != "Unknown":
                entity_data["ownership"] = ownership_normalized
            
            # Address - only add if it exists and has valid data
            if address:
                # Use model_dump with exclude to remove deprecated description field
                address_dict = address.model_dump(exclude={"description"}, exclude_none=True)
                if address_dict:
                    entity_data["address"] = address_dict

            # Build attributes (for additional metadata)
            attributes = {}
            if facility_type != "Unknown":
                attributes["facility_type"] = facility_type
            if facility_level:
                attributes["facility_level"] = facility_level
            if contact_person:
                attributes["contact_person"] = contact_person
            if contact_mobile:
                attributes["contact_mobile"] = contact_mobile
            if latitude and longitude:
                attributes["coordinates"] = {
                    "latitude": latitude,
                    "longitude": longitude,
                }

            if attributes:
                entity_data["attributes"] = attributes

            # Create the entity
            hospital = await context.publication.create_entity(
                entity_type=EntityType.ORGANIZATION,
                entity_subtype=EntitySubType.HOSPITAL,
                entity_data=entity_data,
                author_id=author_id,
                change_description=CHANGE_DESCRIPTION,
            )
            context.log(f"Created hospital {hospital.id}")

            # Create LOCATED_IN relationships
            if location_id and location_entity:
                try:
                    location_name_display = location_entity.names[0].en.full if location_entity.names[0].en else location_name
                    await context.publication.create_relationship(
                        source_entity_id=hospital.id,
                        target_entity_id=location_id,
                        relationship_type="LOCATED_IN",
                        author_id=author_id,
                        change_description=f"Hospital located in {location_name_display}",
                    )
                    relationships_count += 1
                    context.log(f"  Created LOCATED_IN relationship: {hospital.id} → {location_id}")
                except Exception as e:
                    context.log(f"  ERROR: Failed to create LOCATED_IN relationship with location: {e}")
            
            if province_id and province_entity:
                try:
                    province_name_display = province_entity.names[0].en.full if province_entity.names[0].en else province_name
                    await context.publication.create_relationship(
                        source_entity_id=hospital.id,
                        target_entity_id=province_id,
                        relationship_type="LOCATED_IN",
                        author_id=author_id,
                        change_description=f"Hospital located in {province_name_display}",
                    )
                    relationships_count += 1
                    context.log(f"  Created LOCATED_IN relationship: {hospital.id} → {province_id}")
                except Exception as e:
                    context.log(f"  ERROR: Failed to create LOCATED_IN relationship with province: {e}")

            count += 1

        except Exception as e:
            context.log(f"ERROR: Failed to create hospital {hospital_data.get('name', 'unknown')}: {e}")
            continue

    context.log(f"Created {count} health facility entities")
    context.log(f"Skipped {skipped_count} facilities (no name)")
    context.log(f"Linked {linked_count} facilities to location entities")
    context.log(f"Created {relationships_count} LOCATED_IN relationships")

    # Verify
    entities = await context.db.list_entities(
        limit=1000, entity_type="organization", sub_type="hospital"
    )
    context.log(f"Verified: {len(entities)} hospital entities in database")

    context.log("Migration completed successfully")


def _normalize_ownership(ownership: str) -> str:
    """Normalize ownership type to standard values.
    
    Args:
        ownership: Raw ownership string
        
    Returns:
        Normalized ownership: "Government", "Public", or "Private"
    """
    if not ownership or ownership == "Unknown":
        return "Unknown"
    
    ownership_lower = ownership.lower()
    
    if any(keyword in ownership_lower for keyword in ["government", "govt", "state"]):
        return "Government"
    elif any(keyword in ownership_lower for keyword in ["public", "municipal", "community"]):
        return "Public"
    elif any(keyword in ownership_lower for keyword in ["private", "privately"]):
        return "Private"
    else:
        return "Unknown"

