## 1. Environment Setup

- [x] 1.1 Add Neo4j dependencies to requirements.txt (neo4j, rdflib, SPARQLWrapper, jieba, networkx)
- [x] 1.2 Add Neo4j configuration to .env.example (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
- [x] 1.3 Create docker-compose.yml with Neo4j service (skipped - using external Neo4j)
- [x] 1.4 Create core/kg/ module directory structure

## 2. Neo4j Client Implementation

- [x] 2.1 Implement neo4j_client.py with connection pooling
- [x] 2.2 Add health check method to Neo4j client
- [x] 2.3 Implement retry logic with exponential backoff
- [x] 2.4 Add Neo4j configuration to config/settings.py

## 3. Knowledge Graph Handler

- [x] 3.1 Adapt EDUKG kg_handler.py for Neo4j backend
- [x] 3.2 Implement TTL file parsing with rdflib
- [x] 3.3 Implement Neo4j n10s import script
- [x] 3.4 Add entity query methods (by URI, by label)
- [x] 3.5 Add relationship query methods (1-hop neighbors)
- [x] 3.6 Add class hierarchy query methods

## 4. Entity Linking Service

- [x] 4.1 Create entity dictionaries from EDUKG data
- [x] 4.2 Implement jieba dictionary loading
- [x] 4.3 Adapt EDUKG linking.py for text entity recognition
- [x] 4.4 Add subject-context filtering
- [x] 4.5 Implement entity position tracking
- [x] 4.6 Add entity context enrichment (optional)

## 5. Knowledge Graph Models

- [x] 5.1 Create models/kg.py with Pydantic models
- [x] 5.2 Define EntityResponse model
- [x] 5.3 Define EntitySearchRequest model
- [x] 5.4 Define KnowledgeTreeResponse model
- [x] 5.5 Define StudentProgressRequest/Response models

## 6. Knowledge Graph API

- [x] 6.1 Create api/kg.py with FastAPI router
- [x] 6.2 Implement GET /api/kg/entities (search entities)
- [x] 6.3 Implement GET /api/kg/entity/{uri} (entity detail)
- [x] 6.4 Implement POST /api/kg/link (entity linking)
- [x] 6.5 Implement GET /api/kg/subject/{subject}/tree (knowledge tree)
- [x] 6.6 Implement GET /api/kg/subject/{subject}/classes (class list)
- [x] 6.7 Add API documentation with OpenAPI

## 7. Student Progress Tracking

- [x] 7.1 Design Student node and LEARNED relationship in Neo4j
- [x] 7.2 Implement student progress initialization
- [x] 7.3 Implement progress update API (POST /api/kg/student/{id}/progress)
- [x] 7.4 Implement progress query API (GET /api/kg/student/{id}/progress)
- [x] 7.5 Add progress statistics calculation

## 8. Knowledge Visualization

- [x] 8.1 Implement knowledge tree generation
- [x] 8.2 Add tree depth parameter support

## 9. Teacher Lesson Preparation

- [x] 9.1 Implement knowledge point recommendation

## 10. Testing (Read-only, Neo4j real tests)

- [x] 10.1 Create tests/real/test_kg_neo4j.py - Neo4j connection and query tests
- [x] 10.2 Test entity search (by label, by URI, fuzzy search)
- [x] 10.3 Test entity linking (jieba + dictionary matching)
- [x] 10.4 Test knowledge tree generation
- [x] 10.5 Test student progress tracking (update + query) - Skipped per user request
- [x] 10.6 Test Neo4j health check endpoint

## 11. Documentation & Deployment

- [x] 11.1 Update CLAUDE.md with KG module documentation
- [x] 11.2 Create Neo4j setup guide (README or docs)
- [x] 11.3 Create EDUKG data import guide
- [x] 11.4 Update main.py to include KG router
- [x] 11.5 Add configuration validation on startup