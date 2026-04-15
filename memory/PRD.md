# Fake News Detection System - PRD

## Original Problem Statement
Build a complete end-to-end Real-Time Fake News Detection System using Neo4j graph database with FastAPI backend, React frontend, spaCy NLP, and D3.js graph visualization.

## Architecture
- **Backend**: FastAPI (Python) with Neo4j Bolt driver + MongoDB (for history)
- **Database**: Neo4j (graph DB for news analysis), MongoDB (for analysis history)
- **Frontend**: React.js with D3.js force-directed graph, Tailwind CSS, shadcn/ui
- **NLP**: spaCy (en_core_web_sm) for entity extraction
- **Design**: IBM Plex Sans/Mono, Swiss Brutalist, dark/light mode

## User Personas
- Journalists verifying article authenticity
- Researchers studying misinformation patterns
- General users checking news credibility

## Core Requirements
- Accept news article text input
- Extract entities (Source, Author, Topics, Organizations, Persons)
- Store as graph in Neo4j (News, Source, Author, Topic, Person nodes)
- Calculate Fake Score using graph-based analysis
- Provide explainable verdicts (LIKELY TRUE / SUSPICIOUS / LIKELY FAKE)
- Visualize knowledge graph with D3.js

## What's Been Implemented (April 2026)
- Full backend with Neo4j + MongoDB integration
- spaCy NLP entity extraction
- **Upgraded Fake Score algorithm (April 15)**: Combined graph + content scoring
  - Graph: `(source_count * 5) + (author_count * 3) + (topic_frequency * 2)` via Neo4j Cypher
  - Content: sensational keywords (+10), unrealistic claims (+20), conspiracy phrases (+15)
  - `final_score = graph_score + content_score`, capped at 100
- Thresholds: <30 = Likely True, 30-70 = Suspicious, >70 = Likely Fake
- API response: score, label, reason, breakdown (with graph_score, content_score, detected keywords/phrases)
- Explanation items tagged as [Graph] or [Content]
- 30+ sample articles seeded
- D3.js interactive force-directed graph with zoom/pan/drag
- Dark/light mode toggle
- Analysis history tracking
- Statistics dashboard with verdict distribution, source credibility
- Full-screen graph explorer
- Caching for repeated queries
- Swagger API documentation at /api/docs

## Prioritized Backlog
### P0 (Done)
- [x] Core analysis pipeline
- [x] Neo4j graph storage
- [x] NLP entity extraction
- [x] Fake score calculation
- [x] D3.js visualization
- [x] Dark/light mode

### P1 (Next)
- [ ] URL input support (scrape article from URL)
- [ ] User authentication & personal history
- [ ] Bulk article import
- [ ] Export results as PDF/CSV

### P2 (Future)
- [ ] AI-powered analysis with LLM integration
- [ ] Real-time news feed monitoring
- [ ] Browser extension for inline fact-checking
- [ ] API rate limiting and auth tokens

## Next Tasks
1. Add URL scraping support for article input
2. Add user auth for personal analysis history
3. Enhance graph visualization with time-based filtering
