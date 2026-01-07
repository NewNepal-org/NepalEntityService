# Migration: 008-complete-political-parties

## Purpose

Complete the political party database by importing the remaining registered political parties from the Election Commission of Nepal. This migration adds parties with registration numbers 204-230 that were not included in migration 003 (which covered registration numbers 1-116). Additionally, updates the National Independent Party to use "Rastriya Swatantra Party" as the primary English name.

## Data Sources

- Election Commission of Nepal: Registered Political Parties list (2082 B.S.)
- CSV file: `source/parties-list.csv` containing parties with registration numbers 204-230
- Complements data from migration 003 which imported parties 1-116
- Google Vertex AI translation service for generating English party names and addresses

## Migration Process

This migration operates in four distinct stages to ensure data integrity:

### Stage 0: Update Existing Party Name
Updates the National Independent Party entity to use "Rastriya Swatantra Party" as the primary English name, with "National Independent Party" moved to an alternate name. This change reflects the party's commonly used romanized name.

### Stage 1: Data Preparation
Processes all 27 new parties from the CSV source, building complete entity data structures including:
- Bilingual names (Nepali Devanagari and romanized English)
- Party symbols with translations
- Registration dates converted from Nepali calendar
- Addresses with bilingual descriptions
- Party leadership information
- Election Commission registration identifiers

### Stage 2: Collision Detection
Validates that all generated entity slugs are unique by checking against existing political party entities in the database. The migration aborts if any slug collisions are detected.

### Stage 3: Entity Creation
Creates all 27 new political party entities in the database using the Publication Service to ensure proper versioning and audit trails.

## Changes Made

- Created 27 political party entities with registration numbers 204-230
- Updated 1 existing entity (National Independent Party name structure)
- All parties include both Nepali (Devanagari) and romanized English names
- Added party symbols, registration dates, addresses, and leadership information
- Maintained consistent entity structure matching migration 003 format
- All parties are marked as ORGANIZATION type with POLITICAL_PARTY subtype

## Execution Results

**Completed on**: 2026-01-07  
**Duration**: 0.1 seconds  
**Entities created**: 27 new political parties  
**Entities updated**: 1 (National Independent Party)  
**Total versions created**: 28  
**Final database count**: 151 total political parties  

### Parties Added (Registration Numbers 204-230)

1. Shram Sanskriti Party (श्रम संस्कृति पार्टी)
2. Gatisheel Loktantrik Party (गतिशील लोकतान्त्रिक पार्टी)
3. Nagarik Unmukti Party, Nepal (नागरिक उन्मुक्ति पार्टी, नेपाल)
4. Nepali Communist Party (नेपाली कम्युनिष्ट पार्टी)
5. Rastriya Parivartan Party (राष्ट्रिय परिवर्तन पार्टी)
6. Rastriya Janamat Party (राष्ट्रिय जनमत पार्टी)
7. Nepal Communist Party (Maobadi) (नेपाल कम्युनिस्ट पार्टी (माओबादी))
8. Rastra Nirman Dal Nepal (राष्ट्र निर्माण दल नेपाल)
9. Rastriya Urjasheel Party, Nepal (राष्ट्रिय उर्जाशील पार्टी, नेपाल)
10. People First Party (पिपुल फर्स्ट पार्टी)
11. Ujyalo Nepal Party (उज्यालो नेपाल पार्टी)
12. Swabhiman Party (स्वाभिमान पार्टी)
13. Hamro Party Nepal (हाम्रो पार्टी नेपाल)
14. Nagarik Sarvochata Party Nepal (नागरिक सर्वोच्चता पार्टी नेपाल)
15. Janadesh Party Nepal (जनादेश पार्टी नेपाल)
16. Sarbabhauma Nagarik Party (सार्वभौम नागरिक पार्टी)
17. Nagarik Sewa Party (नागरिक सेवा पार्टी)
18. Jai Matribhumi Party (जय मातृभूमि पार्टी)
19. Pragatisheel Nagarik Party (प्रगतिशील नागरिक पार्टी)
20. Sarvodaya Party (सर्वोदय पार्टी)
21. Samunnat Nepal Party (समुन्नत नेपाल पार्टी)
22. Nagarik Bachau Dal, Nepal (नागरिक बचाउ दल, नेपाल)
23. Nepal Jansewa Party (नेपाल जनसेवा पार्टी)
24. Samabeshi Samajbadi Party (समावेशी समाजवादी पार्टी)
25. Awaz Party (आवाज पार्टी)
26. Janata Loktantrik Party, Nepal (जनता लोकतान्त्रिक पार्टी, नेपाल)
27. Jan Adhikar Party (जन अधिकार पार्टी)

## Verification

The migration was verified through multiple checks:

- **Entity count validation**: Confirmed creation of exactly 27 new entities
- **Name structure verification**: All entities have both Nepali and English names
- **Symbol data validation**: Party symbols correctly imported with bilingual descriptions
- **Registration data integrity**: All registration numbers (204-230) properly stored as external identifiers
- **Address data completeness**: Bilingual address information correctly structured
- **Slug uniqueness**: No duplicate slugs created, maintaining database integrity
- **National Independent Party update**: Confirmed name structure change with primary/alternate names
- **Database consistency**: Final count of 151 total political parties matches expected coverage

## Technical Notes

- Migration uses romanized Nepali names to maintain authentic context while ensuring accessibility
- Address fields use the `description2` field with proper LangText structure
- Entity updates use `change_description2` parameter following current API patterns
- Three-stage processing ensures data integrity and prevents partial failures
- Migration is idempotent and can be safely re-run
- Completes the political party registry coverage from Election Commission data
