# Examples

Practical examples for common use cases with the Nepal Entity Service API.

## Basic Examples

### Search for a Person

Search for a person by name:

```python
import requests

response = requests.get(
    "http://localhost:8195/api/entities",
    params={
        "query": "ram chandra poudel",
        "entity_type": "person"
    }
)

data = response.json()
print(f"Found {data['total']} results")

for entity in data['entities']:
    name = entity['names'][0]['en']['full']
    party = entity['attributes'].get('party', 'Unknown')
    print(f"- {name} ({party})")
```

### Get Entity Details

Retrieve complete information about an entity:

```python
import requests

entity_id = "entity:person/ram-chandra-poudel"
response = requests.get(f"http://localhost:8195/api/entities/{entity_id}")

entity = response.json()

# Print basic info
print(f"Name: {entity['names'][0]['en']['full']}")
print(f"Type: {entity['type']}")

# Print attributes
print("\nAttributes:")
for key, value in entity['attributes'].items():
    print(f"  {key}: {value}")

# Print identifiers
print("\nExternal Links:")
for identifier in entity['identifiers']:
    if identifier.get('url'):
        print(f"  {identifier['scheme']}: {identifier['url']}")
```

### Find All Members of a Political Party

Query relationships to find all members of a party:

```python
import requests

party_id = "entity:organization/political_party/nepali-congress"
response = requests.get(
    "http://localhost:8195/api/relationships",
    params={
        "relationship_type": "MEMBER_OF",
        "target_entity_id": party_id,
        "limit": 50
    }
)

data = response.json()
print(f"Found {data['total']} members")

# Get details for each member
for rel in data['relationships']:
    person_id = rel['source_entity_id']
    person_response = requests.get(f"http://localhost:8195/api/entities/{person_id}")
    person = person_response.json()
    
    name = person['names'][0]['en']['full']
    role = rel['attributes'].get('role', 'Member')
    print(f"- {name} ({role})")
```

## Advanced Examples

### Search with Multiple Filters

Combine multiple filters for precise results:

```python
import requests
import json

response = requests.get(
    "http://localhost:8195/api/entities",
    params={
        "query": "pradesh",
        "entity_type": "location",
        "sub_type": "province",
        "attributes": json.dumps({"population": ">5000000"}),
        "limit": 10
    }
)

data = response.json()
for location in data['entities']:
    name = location['names'][0]['en']['full']
    pop = location['attributes'].get('population', 'Unknown')
    print(f"{name}: {pop} people")
```

### Paginate Through Large Result Sets

Handle pagination for large datasets:

```python
import requests

def get_all_entities(entity_type, page_size=20):
    """Fetch all entities of a given type with pagination."""
    all_entities = []
    offset = 0
    
    while True:
        response = requests.get(
            "http://localhost:8195/api/entities",
            params={
                "entity_type": entity_type,
                "limit": page_size,
                "offset": offset
            }
        )
        
        data = response.json()
        all_entities.extend(data['entities'])
        
        # Check if we've fetched all results
        if offset + page_size >= data['total']:
            break
        
        offset += page_size
    
    return all_entities

# Get all political parties
parties = get_all_entities("organization")
print(f"Total parties: {len(parties)}")
```

### Track Entity Changes Over Time

View version history to see how an entity changed:

```python
import requests
from datetime import datetime

entity_id = "entity:person/ram-chandra-poudel"

# Get version history
response = requests.get(f"http://localhost:8195/api/entities/{entity_id}/versions")
versions = response.json()['versions']

print(f"Entity has {len(versions)} versions\n")

for version in versions:
    created_at = datetime.fromisoformat(version['created_at'].replace('Z', '+00:00'))
    author = version['author']
    description = version.get('change_description', 'No description')
    
    print(f"Version {version['version_number']}:")
    print(f"  Date: {created_at.strftime('%Y-%m-%d %H:%M')}")
    print(f"  By: {author}")
    print(f"  Change: {description}")
    
    # Show what changed
    snapshot = version['snapshot']
    party = snapshot['attributes'].get('party', 'Unknown')
    position = snapshot['attributes'].get('position', 'Unknown')
    print(f"  State: {party}, {position}\n")
```

### Build a Relationship Graph

Create a network graph of entity relationships:

```python
import requests
import networkx as nx
import matplotlib.pyplot as plt

def build_relationship_graph(entity_id, depth=2):
    """Build a relationship graph starting from an entity."""
    G = nx.DiGraph()
    visited = set()
    
    def add_relationships(entity_id, current_depth):
        if current_depth > depth or entity_id in visited:
            return
        
        visited.add(entity_id)
        
        # Get entity details
        entity_response = requests.get(f"http://localhost:8195/api/entities/{entity_id}")
        entity = entity_response.json()
        entity_name = entity['names'][0]['en']['full']
        
        # Add node
        G.add_node(entity_id, label=entity_name, type=entity['type'])
        
        # Get relationships
        rel_response = requests.get(
            f"http://localhost:8195/api/entities/{entity_id}/relationships"
        )
        relationships = rel_response.json()['relationships']
        
        for rel in relationships:
            target_id = rel['target_entity_id']
            rel_type = rel['type']
            
            # Add edge
            G.add_edge(entity_id, target_id, type=rel_type)
            
            # Recursively add target's relationships
            add_relationships(target_id, current_depth + 1)
    
    add_relationships(entity_id, 0)
    return G

# Build graph
entity_id = "entity:person/ram-chandra-poudel"
G = build_relationship_graph(entity_id, depth=2)

print(f"Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

# Visualize (requires matplotlib)
pos = nx.spring_layout(G)
labels = nx.get_node_attributes(G, 'label')
nx.draw(G, pos, labels=labels, with_labels=True, node_color='lightblue', 
        node_size=1500, font_size=8, arrows=True)
plt.show()
```

## Web Application Examples

### React Component

Fetch and display entities in a React component:

```javascript
import React, { useState, useEffect } from 'react';

function EntitySearch() {
  const [query, setQuery] = useState('');
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(false);

  const searchEntities = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8195/api/entities?query=${encodeURIComponent(query)}`
      );
      const data = await response.json();
      setEntities(data.entities);
    } catch (error) {
      console.error('Error fetching entities:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search entities..."
      />
      <button onClick={searchEntities} disabled={loading}>
        {loading ? 'Searching...' : 'Search'}
      </button>

      <div>
        {entities.map((entity) => (
          <div key={entity.id}>
            <h3>{entity.names[0].en.full}</h3>
            <p>Type: {entity.type}</p>
            {entity.attributes.party && (
              <p>Party: {entity.attributes.party}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default EntitySearch;
```

### Vue.js Component

Similar functionality in Vue.js:

```vue
<template>
  <div>
    <input
      v-model="query"
      @keyup.enter="searchEntities"
      placeholder="Search entities..."
    />
    <button @click="searchEntities" :disabled="loading">
      {{ loading ? 'Searching...' : 'Search' }}
    </button>

    <div v-for="entity in entities" :key="entity.id">
      <h3>{{ entity.names[0].en.full }}</h3>
      <p>Type: {{ entity.type }}</p>
      <p v-if="entity.attributes.party">
        Party: {{ entity.attributes.party }}
      </p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      query: '',
      entities: [],
      loading: false
    };
  },
  methods: {
    async searchEntities() {
      this.loading = true;
      try {
        const response = await fetch(
          `http://localhost:8195/api/entities?query=${encodeURIComponent(this.query)}`
        );
        const data = await response.json();
        this.entities = data.entities;
      } catch (error) {
        console.error('Error fetching entities:', error);
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

## Data Analysis Examples

### Analyze Political Party Distribution

Analyze the distribution of politicians across parties:

```python
import requests
from collections import Counter

# Get all persons
response = requests.get(
    "http://localhost:8195/api/entities",
    params={"entity_type": "person", "limit": 1000}
)

entities = response.json()['entities']

# Count party affiliations
party_counts = Counter()
for entity in entities:
    party = entity['attributes'].get('party')
    if party:
        party_counts[party] += 1

# Print results
print("Political Party Distribution:")
for party, count in party_counts.most_common():
    print(f"  {party}: {count} members")
```

### Generate Entity Report

Create a comprehensive report for an entity:

```python
import requests
from datetime import datetime

def generate_entity_report(entity_id):
    """Generate a comprehensive report for an entity."""
    
    # Get entity details
    entity_response = requests.get(f"http://localhost:8195/api/entities/{entity_id}")
    entity = entity_response.json()
    
    # Get relationships
    rel_response = requests.get(
        f"http://localhost:8195/api/entities/{entity_id}/relationships"
    )
    relationships = rel_response.json()['relationships']
    
    # Get version history
    version_response = requests.get(
        f"http://localhost:8195/api/entities/{entity_id}/versions"
    )
    versions = version_response.json()['versions']
    
    # Generate report
    print("=" * 60)
    print(f"ENTITY REPORT: {entity['names'][0]['en']['full']}")
    print("=" * 60)
    
    print(f"\nID: {entity['id']}")
    print(f"Type: {entity['type']}")
    if entity.get('sub_type'):
        print(f"Subtype: {entity['sub_type']}")
    
    print("\nNames:")
    for name in entity['names']:
        print(f"  {name['kind']}: {name['en']['full']}")
        if name.get('ne'):
            print(f"    Nepali: {name['ne']['full']}")
    
    print("\nAttributes:")
    for key, value in entity['attributes'].items():
        print(f"  {key}: {value}")
    
    print(f"\nRelationships ({len(relationships)}):")
    for rel in relationships[:5]:  # Show first 5
        target_response = requests.get(
            f"http://localhost:8195/api/entities/{rel['target_entity_id']}"
        )
        target = target_response.json()
        target_name = target['names'][0]['en']['full']
        print(f"  {rel['type']} → {target_name}")
    
    print(f"\nVersion History ({len(versions)} versions):")
    for version in versions[:3]:  # Show first 3
        created_at = datetime.fromisoformat(version['created_at'].replace('Z', '+00:00'))
        print(f"  v{version['version_number']}: {created_at.strftime('%Y-%m-%d')} - {version.get('change_description', 'No description')}")
    
    print("\n" + "=" * 60)

# Generate report
generate_entity_report("entity:person/ram-chandra-poudel")
```

## Error Handling

### Robust Error Handling

Handle API errors gracefully:

```python
import requests

def safe_api_call(url, params=None):
    """Make an API call with proper error handling."""
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raise exception for 4xx/5xx status codes
        return response.json()
    
    except requests.exceptions.Timeout:
        print("Error: Request timed out")
        return None
    
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API")
        return None
    
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            print("Error: Entity not found")
        elif response.status_code == 400:
            error_data = response.json()
            print(f"Error: {error_data['error']['message']}")
        else:
            print(f"Error: HTTP {response.status_code}")
        return None
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Use it
data = safe_api_call(
    "http://localhost:8195/api/entities",
    params={"query": "poudel"}
)

if data:
    print(f"Found {data['total']} results")
```

## Next Steps

- [API Reference](/docs) - Interactive OpenAPI documentation
- [Data Models](/data-models) - Understanding entity schemas
- [Getting Started](/getting-started) - Basic usage guide
- [Architecture](/architecture) - System design overview
