from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import hashlib
import time
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import spacy
from neo4j import GraphDatabase
import re
from collections import defaultdict

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
mongo_client = AsyncIOMotorClient(mongo_url)
db = mongo_client[os.environ['DB_NAME']]

# Neo4j connection
neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
neo4j_password = os.environ.get('NEO4J_PASSWORD', 'neo4j123')

neo4j_driver = None

def get_neo4j_driver():
    global neo4j_driver
    if neo4j_driver is None:
        neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    return neo4j_driver

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Simple cache
_cache: Dict[str, Any] = {}
CACHE_TTL = 300  # 5 minutes

app = FastAPI(title="Fake News Detection API", docs_url="/api/docs", openapi_url="/api/openapi.json")
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Pydantic Models ---

class AnalyzeRequest(BaseModel):
    text: str
    source: Optional[str] = "unknown"
    author: Optional[str] = "unknown"

class AnalyzeResponse(BaseModel):
    id: str
    score: float
    label: str
    reason: str
    fake_score: float  # alias for score (backward compat)
    verdict: str  # alias for label (backward compat)
    explanation: List[str]
    breakdown: Dict[str, Any]
    entities: Dict[str, Any]
    graph_data: Dict[str, Any]
    timestamp: str

class AddDataRequest(BaseModel):
    articles: List[Dict[str, Any]]

class GraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    links: List[Dict[str, Any]]

class HistoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    text_preview: str
    fake_score: float
    verdict: str
    source: str
    timestamp: str

# --- NLP Entity Extraction ---

def extract_entities(text: str) -> Dict[str, Any]:
    doc = nlp(text)
    
    organizations = list(set([ent.text for ent in doc.ents if ent.label_ == "ORG"]))
    persons = list(set([ent.text for ent in doc.ents if ent.label_ == "PERSON"]))
    locations = list(set([ent.text for ent in doc.ents if ent.label_ in ("GPE", "LOC")]))
    
    # Extract keywords (nouns and proper nouns)
    keywords = list(set([
        token.lemma_.lower() for token in doc 
        if token.pos_ in ("NOUN", "PROPN") and len(token.text) > 2 and not token.is_stop
    ]))[:10]
    
    # Extract topics from noun chunks
    topics = list(set([
        chunk.text.lower() for chunk in doc.noun_chunks 
        if len(chunk.text) > 3
    ]))[:8]
    
    return {
        "organizations": organizations,
        "persons": persons,
        "locations": locations,
        "keywords": keywords,
        "topics": topics
    }

# --- Neo4j Operations ---

def store_in_neo4j(article_id: str, text: str, source: str, author: str, entities: Dict, fake_score: float, verdict: str):
    driver = get_neo4j_driver()
    with driver.session() as session:
        # Create News node
        session.run("""
            MERGE (n:News {id: $id})
            SET n.text = $text, n.fake_score = $fake_score, n.verdict = $verdict,
                n.created_at = datetime()
        """, id=article_id, text=text[:500], fake_score=fake_score, verdict=verdict)
        
        # Create Source node and relationship
        if source and source != "unknown":
            session.run("""
                MERGE (s:Source {name: $source})
                WITH s
                MATCH (n:News {id: $id})
                MERGE (n)-[:PUBLISHED_BY]->(s)
            """, source=source.lower().strip(), id=article_id)
        
        # Create Author node and relationship
        if author and author != "unknown":
            session.run("""
                MERGE (a:Author {name: $author})
                WITH a
                MATCH (n:News {id: $id})
                MERGE (n)-[:WRITTEN_BY]->(a)
            """, author=author.lower().strip(), id=article_id)
        
        # Create Topic nodes and relationships
        for topic in entities.get("topics", [])[:5]:
            session.run("""
                MERGE (t:Topic {name: $topic})
                WITH t
                MATCH (n:News {id: $id})
                MERGE (n)-[:ABOUT]->(t)
            """, topic=topic.lower().strip(), id=article_id)
        
        # Create Person entity nodes
        for person in entities.get("persons", [])[:3]:
            session.run("""
                MERGE (p:Person {name: $person})
                WITH p
                MATCH (n:News {id: $id})
                MERGE (n)-[:MENTIONS]->(p)
            """, person=person.lower().strip(), id=article_id)


def calculate_fake_score(text: str, source: str, author: str, entities: Dict) -> tuple:
    """
    New scoring formula using pure Neo4j graph analysis:
    score = (source_count * 5) + (author_count * 3) + (topic_frequency * 2)
    
    - source_count: number of suspicious/fake articles from same source
    - author_count: number of suspicious/fake articles by same author
    - topic_frequency: number of suspicious articles sharing the same topics
    """
    driver = get_neo4j_driver()
    reasons = []
    source_count = 0
    author_count = 0
    topic_frequency = 0
    
    # Raw counts from Neo4j for breakdown display
    source_total = 0
    author_total = 0
    
    with driver.session() as session:
        # 1. Source credibility — count suspicious articles from this source
        if source and source != "unknown":
            result = session.run("""
                MATCH (s:Source {name: $source})<-[:PUBLISHED_BY]-(n:News)
                RETURN count(n) as total_articles,
                       count(CASE WHEN n.verdict IN ['LIKELY FAKE', 'SUSPICIOUS'] THEN 1 END) as suspicious_count
            """, source=source.lower().strip())
            record = result.single()
            if record:
                source_total = record["total_articles"] or 0
                source_count = record["suspicious_count"] or 0
                if source_count > 3:
                    reasons.append(
                        f"Source '{source}' has {source_count} suspicious articles out of {source_total} total "
                        f"(>{3} threshold) — graph query: MATCH (s:Source {{name: '{source}'}})<-[:PUBLISHED_BY]-(n:News)"
                    )
                elif source_total > 0 and source_count == 0:
                    reasons.append(f"Source '{source}' has {source_total} articles with 0 flagged — credible source")
                elif source_total > 0:
                    reasons.append(f"Source '{source}' has {source_count}/{source_total} suspicious articles")
        
        # 2. Author credibility — count suspicious articles by this author
        if author and author != "unknown":
            result = session.run("""
                MATCH (a:Author {name: $author})<-[:WRITTEN_BY]-(n:News)
                RETURN count(n) as total_articles,
                       count(CASE WHEN n.verdict IN ['LIKELY FAKE', 'SUSPICIOUS'] THEN 1 END) as suspicious_count
            """, author=author.lower().strip())
            record = result.single()
            if record:
                author_total = record["total_articles"] or 0
                author_count = record["suspicious_count"] or 0
                if author_count > 0:
                    reasons.append(
                        f"Author '{author}' linked to {author_count} suspicious articles out of {author_total} total "
                        f"— graph query: MATCH (a:Author {{name: '{author}'}})<-[:WRITTEN_BY]-(n:News)"
                    )
                elif author_total > 0:
                    reasons.append(f"Author '{author}' has {author_total} articles with 0 flagged — credible author")
        
        # 3. Topic clustering — count suspicious articles sharing the same topics
        topics = entities.get("topics", [])
        if topics:
            clean_topics = [t.lower().strip() for t in topics[:5]]
            result = session.run("""
                UNWIND $topics AS topic_name
                MATCH (t:Topic {name: topic_name})<-[:ABOUT]-(n:News)
                WHERE n.verdict IN ['LIKELY FAKE', 'SUSPICIOUS']
                RETURN count(DISTINCT n) as suspicious_topic_articles
            """, topics=clean_topics)
            record = result.single()
            if record:
                topic_frequency = record["suspicious_topic_articles"] or 0
                if topic_frequency > 0:
                    reasons.append(
                        f"Topics overlap with {topic_frequency} previously flagged articles "
                        f"— graph query: MATCH (t:Topic)<-[:ABOUT]-(n:News) WHERE n.verdict IN ['LIKELY FAKE','SUSPICIOUS']"
                    )
    
    # Apply formula: score = (source_count * 5) + (author_count * 3) + (topic_frequency * 2)
    raw_score = (source_count * 5) + (author_count * 3) + (topic_frequency * 2)
    
    # Cap at 100
    final_score = round(min(raw_score, 100), 1)
    
    # Determine label
    if final_score < 30:
        label = "Likely True"
    elif final_score <= 70:
        label = "Suspicious"
    else:
        label = "Likely Fake"
    
    # Build detailed reason string
    if not reasons:
        reasons.append("No suspicious patterns detected in the graph. Article appears credible.")
    
    reason_text = (
        f"Score {final_score} = (source_count:{source_count} x 5) + (author_count:{author_count} x 3) + (topic_frequency:{topic_frequency} x 2). "
        + " | ".join(reasons)
    )
    
    breakdown = {
        "source_count": source_count,
        "source_total": source_total,
        "author_count": author_count,
        "author_total": author_total,
        "topic_frequency": topic_frequency,
        "formula": f"({source_count} x 5) + ({author_count} x 3) + ({topic_frequency} x 2) = {raw_score}",
        "raw_score": raw_score,
        "capped_score": final_score
    }
    
    return final_score, label, reason_text, reasons, breakdown


def get_graph_data(article_id: Optional[str] = None) -> Dict:
    driver = get_neo4j_driver()
    nodes = []
    links = []
    node_ids = set()
    
    with driver.session() as session:
        if article_id:
            query = """
                MATCH (n:News {id: $id})
                OPTIONAL MATCH (n)-[r]->(target)
                RETURN n.id as news_id, n.text as news_text, n.fake_score as news_score, 
                       n.verdict as news_verdict,
                       type(r) as rel_type, labels(target)[0] as target_type, 
                       target.name as target_name
            """
            records = list(session.run(query, id=article_id))
        else:
            query = """
                MATCH (n:News)-[r]->(target)
                RETURN n.id as news_id, n.text as news_text, n.fake_score as news_score, 
                       n.verdict as news_verdict,
                       type(r) as rel_type, labels(target)[0] as target_type, 
                       target.name as target_name
                LIMIT 500
            """
            records = list(session.run(query))
        
        for record in records:
            news_id = record["news_id"]
            
            if news_id and news_id not in node_ids:
                node_ids.add(news_id)
                verdict = record["news_verdict"] or "UNKNOWN"
                color = "#3B82F6" if verdict == "LIKELY TRUE" else "#EF4444" if verdict == "LIKELY FAKE" else "#FBBF24"
                nodes.append({
                    "id": news_id,
                    "label": (record["news_text"] or "")[:40] + "...",
                    "type": "News",
                    "score": record["news_score"] or 0,
                    "verdict": verdict,
                    "color": color,
                    "size": 12
                })
            
            target_type = record["target_type"]
            target_name = record["target_name"]
            rel_type = record["rel_type"]
            
            if target_type and target_name and rel_type:
                target_id = f"{target_type}_{target_name}"
                
                if target_id not in node_ids:
                    node_ids.add(target_id)
                    type_colors = {"Source": "#6366F1", "Author": "#10B981", "Topic": "#F59E0B", "Person": "#EC4899"}
                    type_sizes = {"Source": 10, "Author": 8, "Topic": 7, "Person": 7}
                    nodes.append({
                        "id": target_id,
                        "label": target_name,
                        "type": target_type,
                        "color": type_colors.get(target_type, "#94A3B8"),
                        "size": type_sizes.get(target_type, 6)
                    })
                
                links.append({
                    "source": news_id,
                    "target": target_id,
                    "type": rel_type
                })
    
    return {"nodes": nodes, "links": links}


# --- API Endpoints ---

@api_router.get("/")
async def root():
    return {"message": "Fake News Detection API", "status": "running"}

@api_router.get("/health")
async def health():
    try:
        driver = get_neo4j_driver()
        driver.verify_connectivity()
        return {"status": "healthy", "neo4j": "connected"}
    except Exception as e:
        return {"status": "degraded", "neo4j": str(e)}


@api_router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_news(req: AnalyzeRequest):
    start_time = time.time()
    
    if not req.text or len(req.text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Article text must be at least 10 characters")
    
    # Check cache
    text_hash = hashlib.md5(req.text[:500].encode()).hexdigest()
    cache_key = f"analyze_{text_hash}"
    if cache_key in _cache and (time.time() - _cache[cache_key]["time"]) < CACHE_TTL:
        logger.info(f"Cache hit for {cache_key}")
        return _cache[cache_key]["data"]
    
    article_id = str(uuid.uuid4())[:8]
    
    # Extract entities
    entities = extract_entities(req.text)
    
    source = req.source or "unknown"
    author = req.author or "unknown"
    
    # If no author found from input, try NLP
    if author == "unknown" and entities["persons"]:
        author = entities["persons"][0]
    
    # Calculate fake score using Neo4j graph analysis
    fake_score, label, reason_text, explanations, breakdown = calculate_fake_score(req.text, source, author, entities)
    
    # Map label to internal verdict for storage
    verdict_map = {"Likely True": "LIKELY TRUE", "Suspicious": "SUSPICIOUS", "Likely Fake": "LIKELY FAKE"}
    verdict = verdict_map.get(label, "SUSPICIOUS")
    
    # Store in Neo4j
    try:
        store_in_neo4j(article_id, req.text, source, author, entities, fake_score, verdict)
    except Exception as e:
        logger.error(f"Neo4j store error: {e}")
    
    # Get graph data for this article
    graph_data = get_graph_data(article_id)
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Store in MongoDB history
    history_doc = {
        "id": article_id,
        "text_preview": req.text[:150],
        "full_text": req.text,
        "fake_score": fake_score,
        "score": fake_score,
        "label": label,
        "verdict": verdict,
        "reason": reason_text,
        "source": source,
        "author": author,
        "entities": entities,
        "explanations": explanations,
        "breakdown": breakdown,
        "timestamp": timestamp
    }
    await db.analysis_history.insert_one(history_doc)
    
    response = AnalyzeResponse(
        id=article_id,
        score=fake_score,
        label=label,
        reason=reason_text,
        fake_score=fake_score,
        verdict=verdict,
        explanation=explanations,
        breakdown=breakdown,
        entities=entities,
        graph_data=graph_data,
        timestamp=timestamp
    )
    
    # Cache result
    _cache[cache_key] = {"data": response, "time": time.time()}
    
    elapsed = time.time() - start_time
    logger.info(f"Analysis completed in {elapsed:.2f}s - Score: {fake_score}, Verdict: {verdict}")
    
    return response


@api_router.post("/add-data")
async def add_sample_data(req: AddDataRequest):
    added = 0
    driver = get_neo4j_driver()
    
    for article in req.articles:
        article_id = str(uuid.uuid4())[:8]
        text = article.get("text", "")
        source = article.get("source", "unknown")
        author = article.get("author", "unknown")
        is_fake = article.get("is_fake", False)
        
        entities = extract_entities(text)
        
        fake_score = article.get("fake_score", 80 if is_fake else 15)
        verdict = "LIKELY FAKE" if is_fake else "LIKELY TRUE"
        
        try:
            store_in_neo4j(article_id, text, source, author, entities, fake_score, verdict)
            added += 1
        except Exception as e:
            logger.error(f"Error adding article: {e}")
    
    return {"message": f"Added {added} articles to the graph database", "count": added}


@api_router.post("/seed")
async def seed_database():
    """Seed the database with sample data"""
    sample_articles = [
        # Trustworthy articles
        {"text": "The Federal Reserve announced a 0.25% interest rate cut on Wednesday, citing slowing economic growth. Chair Jerome Powell stated the decision was unanimous among board members. Markets responded positively with the S&P 500 rising 1.2%.", "source": "reuters", "author": "sarah johnson", "is_fake": False, "fake_score": 8},
        {"text": "NASA's Artemis III mission successfully landed astronauts on the lunar south pole on March 15, 2026. The crew of four will spend 14 days conducting scientific experiments. This marks humanity's return to the Moon after over 50 years.", "source": "associated press", "author": "michael chen", "is_fake": False, "fake_score": 5},
        {"text": "The World Health Organization reported a 30% decline in malaria deaths across sub-Saharan Africa, attributing the improvement to increased distribution of insecticide-treated bed nets and new antimalarial drugs approved in 2025.", "source": "bbc news", "author": "emma wilson", "is_fake": False, "fake_score": 10},
        {"text": "Apple Inc. reported quarterly revenue of $124.3 billion, exceeding analyst expectations. CEO Tim Cook highlighted strong iPhone 17 sales in emerging markets and growing services revenue. The company's stock rose 3.5% in after-hours trading.", "source": "reuters", "author": "david park", "is_fake": False, "fake_score": 7},
        {"text": "The European Parliament passed landmark AI regulation requiring transparency in automated decision-making systems. Companies must now disclose when AI is used in hiring, lending, and law enforcement. The law takes effect January 2027.", "source": "bbc news", "author": "anna schmidt", "is_fake": False, "fake_score": 12},
        {"text": "Scientists at MIT developed a new battery technology using sodium-ion cells that could reduce electric vehicle costs by 40%. The research, published in Nature Energy, shows the batteries achieve 95% of lithium-ion energy density.", "source": "nature", "author": "james liu", "is_fake": False, "fake_score": 9},
        {"text": "India's GDP growth rate reached 7.8% in Q4 2025, driven by strong manufacturing output and digital services exports. Finance Minister Nirmala Sitharaman attributed growth to government infrastructure spending and tax reforms.", "source": "associated press", "author": "priya patel", "is_fake": False, "fake_score": 11},
        {"text": "The UN Climate Summit in Dubai concluded with 195 nations agreeing to phase down fossil fuel production by 50% by 2040. The agreement includes a $200 billion fund to help developing nations transition to renewable energy.", "source": "reuters", "author": "carlos mendez", "is_fake": False, "fake_score": 14},
        {"text": "Google DeepMind's latest AI model achieved human-level performance on graduate-level mathematics problems, scoring 92% on the International Mathematical Olympiad qualifying tests. The breakthrough was peer-reviewed by Fields Medal laureates.", "source": "nature", "author": "robert zhang", "is_fake": False, "fake_score": 13},
        {"text": "Japan's population declined by 800,000 in 2025, according to government census data. Prime Minister Kishida announced expanded childcare subsidies and immigration reforms to address the demographic crisis.", "source": "associated press", "author": "yuki tanaka", "is_fake": False, "fake_score": 6},
        
        # Suspicious / Fake articles
        {"text": "BREAKING: Secret government documents EXPOSED showing they've been hiding alien technology since 1947! The mainstream media doesn't want you to know about the advanced energy devices recovered from crash sites. Share before this gets deleted!", "source": "truthrevealed.net", "author": "patriot investigator", "is_fake": True, "fake_score": 92},
        {"text": "SHOCKING: New study proves 5G towers cause cancer and mind control! Scientists who tried to publish were SILENCED by big tech. Wake up people! They are experimenting on us!", "source": "freedomwatch.blog", "author": "anonymous whistleblower", "is_fake": True, "fake_score": 95},
        {"text": "URGENT: Banks are about to COLLAPSE! Move your money NOW! Insider sources reveal the entire financial system is a hoax. The elite have already moved their wealth offshore. This is the biggest cover-up in history!", "source": "truthrevealed.net", "author": "financial patriot", "is_fake": True, "fake_score": 88},
        {"text": "EXPOSED: Vaccines contain microchips for population tracking! A leaked memo from pharmaceutical companies reveals the conspiracy. They don't want you to know the truth about what's really in those injections!", "source": "healthtruth.org", "author": "dr. natural cure", "is_fake": True, "fake_score": 94},
        {"text": "BOMBSHELL: Famous celebrity secretly replaced by clone! You won't believe the evidence. Look at these photos - the ears are completely different! The original was eliminated years ago and nobody noticed!", "source": "freedomwatch.blog", "author": "truth seeker", "is_fake": True, "fake_score": 90},
        {"text": "SECRET: The moon landing was filmed in a Hollywood studio! New analysis of footage shows impossible lighting angles. NASA has been lying for decades. The evidence is overwhelming but they keep censoring it!", "source": "conspiracyfiles.net", "author": "patriot investigator", "is_fake": True, "fake_score": 91},
        {"text": "BREAKING: Water fluoridation is a government mind control program! Classified documents prove it reduces IQ by 30 points. Scientists who speak out are silenced. Protect your family - filter your water NOW!", "source": "healthtruth.org", "author": "dr. natural cure", "is_fake": True, "fake_score": 87},
        {"text": "CENSORED: Free energy device invented but suppressed by oil companies! This machine runs on water and produces unlimited electricity. They murdered the inventor to keep their profits. SHARE THIS EVERYWHERE!", "source": "truthrevealed.net", "author": "anonymous whistleblower", "is_fake": True, "fake_score": 93},
        {"text": "EXCLUSIVE: World leaders caught in secret meeting planning population reduction by 80%! Hidden camera footage shows them discussing engineered viruses and food supply manipulation. This is NOT a drill!", "source": "conspiracyfiles.net", "author": "truth seeker", "is_fake": True, "fake_score": 96},
        {"text": "VIRAL: Eating only raw meat cures all diseases! Big pharma doesn't want you to know about this ancient secret. Thousands have healed themselves by abandoning cooked food. Doctors are lying to keep you sick!", "source": "healthtruth.org", "author": "wellness warrior", "is_fake": True, "fake_score": 85},
        
        # Suspicious / Mixed articles  
        {"text": "A new report suggests some popular supplements may contain undisclosed ingredients. While the FDA is investigating, no recalls have been issued yet. Consumers should be cautious but not alarmed.", "source": "health daily", "author": "lisa morgan", "is_fake": False, "fake_score": 35},
        {"text": "Sources close to the investigation claim the CEO may have been involved in insider trading, though no charges have been filed. The company denies all allegations and says the investigation is politically motivated.", "source": "news weekly", "author": "anonymous", "is_fake": False, "fake_score": 45},
        {"text": "An unverified video circulating on social media appears to show unusual lights in the sky over Nevada. While some claim it's military testing, others speculate about extraterrestrial origins. Official channels have not commented.", "source": "daily buzz", "author": "viral reporter", "is_fake": False, "fake_score": 55},
        {"text": "Local residents report unusual animal behavior before the earthquake, though seismologists say there is no scientific evidence that animals can predict seismic events. The 4.2 magnitude quake caused minor damage.", "source": "local times", "author": "sam brooks", "is_fake": False, "fake_score": 25},
        {"text": "A controversial study published in a lesser-known journal claims a link between common household chemicals and neurological disorders. Mainstream scientists call for more research before drawing conclusions.", "source": "science today", "author": "research team", "is_fake": False, "fake_score": 40},
        # More trustworthy
        {"text": "Amazon announced it will hire 150,000 seasonal workers for the holiday season, offering $18-25/hour wages. The company also plans to expand its electric delivery fleet to 100,000 vehicles by end of 2026.", "source": "reuters", "author": "jennifer adams", "is_fake": False, "fake_score": 8},
        {"text": "The International Space Station completed its 150,000th orbit of Earth. NASA hosted a live stream celebrating the milestone, featuring messages from current crew members and retired astronauts.", "source": "associated press", "author": "michael chen", "is_fake": False, "fake_score": 5},
        {"text": "South Korea's Samsung announced a $230 billion investment in advanced chip manufacturing over the next 20 years. The plan includes building five new fabrication plants and hiring 80,000 engineers.", "source": "bbc news", "author": "ji-won kim", "is_fake": False, "fake_score": 10},
        # More fake
        {"text": "BANNED VIDEO: Government admits chemtrails are REAL! They've been spraying us with chemicals for decades to control the weather and our minds! Multiple pilots have come forward but keep getting silenced!", "source": "freedomwatch.blog", "author": "patriot investigator", "is_fake": True, "fake_score": 89},
        {"text": "SHOCKING DISCOVERY: Ancient civilization with advanced technology found under Antarctic ice! The government has known for years but keeps it secret. This changes everything we know about human history!", "source": "conspiracyfiles.net", "author": "truth seeker", "is_fake": True, "fake_score": 86},
    ]
    
    driver = get_neo4j_driver()
    added = 0
    
    # Clear existing data
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    
    for article in sample_articles:
        article_id = str(uuid.uuid4())[:8]
        text = article["text"]
        source = article["source"]
        author = article["author"]
        fake_score = article["fake_score"]
        is_fake = article["is_fake"]
        verdict = "LIKELY FAKE" if fake_score > 70 else "SUSPICIOUS" if fake_score > 30 else "LIKELY TRUE"
        
        entities = extract_entities(text)
        
        try:
            store_in_neo4j(article_id, text, source, author, entities, fake_score, verdict)
            added += 1
        except Exception as e:
            logger.error(f"Error seeding article: {e}")
    
    # Clear MongoDB history too
    await db.analysis_history.delete_many({})
    
    return {"message": f"Database seeded with {added} articles", "count": added}


@api_router.get("/history")
async def get_history():
    history = await db.analysis_history.find({}, {"_id": 0}).sort("timestamp", -1).to_list(50)
    return history


@api_router.get("/graph")
async def get_full_graph():
    graph_data = get_graph_data()
    return graph_data


@api_router.get("/stats")
async def get_stats():
    driver = get_neo4j_driver()
    with driver.session() as session:
        # Node counts
        result = session.run("""
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
        """)
        node_counts = {r["label"]: r["count"] for r in result}
        
        # Verdict distribution
        result = session.run("""
            MATCH (n:News)
            RETURN n.verdict as verdict, count(n) as count
        """)
        verdict_dist = {r["verdict"]: r["count"] for r in result}
        
        # Top suspicious sources
        result = session.run("""
            MATCH (s:Source)<-[:PUBLISHED_BY]-(n:News)
            WITH s, count(n) as total, 
                 count(CASE WHEN n.verdict = 'LIKELY FAKE' THEN 1 END) as fake_count
            WHERE total > 0
            RETURN s.name as source, total, fake_count, 
                   toFloat(fake_count)/total as fake_ratio
            ORDER BY fake_ratio DESC
            LIMIT 10
        """)
        suspicious_sources = [dict(r) for r in result]
        
        # Relationship count
        result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
        rel_count = result.single()["count"]
    
    return {
        "node_counts": node_counts,
        "verdict_distribution": verdict_dist,
        "suspicious_sources": suspicious_sources,
        "total_relationships": rel_count
    }


# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    try:
        driver = get_neo4j_driver()
        driver.verify_connectivity()
        logger.info("Neo4j connected successfully")
        # Create indexes
        with driver.session() as session:
            session.run("CREATE INDEX news_id IF NOT EXISTS FOR (n:News) ON (n.id)")
            session.run("CREATE INDEX source_name IF NOT EXISTS FOR (s:Source) ON (s.name)")
            session.run("CREATE INDEX author_name IF NOT EXISTS FOR (a:Author) ON (a.name)")
            session.run("CREATE INDEX topic_name IF NOT EXISTS FOR (t:Topic) ON (t.name)")
        logger.info("Neo4j indexes created")
    except Exception as e:
        logger.error(f"Neo4j connection failed: {e}")

@app.on_event("shutdown")
async def shutdown():
    mongo_client.close()
    if neo4j_driver:
        neo4j_driver.close()
