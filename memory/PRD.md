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
- Fake Score algorithm (source credibility, author credibility, topic clustering, repetition, text analysis)
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
