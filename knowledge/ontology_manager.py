"""
weAID Ontology Manager
RDF/OWL2 기반 온톨로지 관리자 - SPARQL 쿼리 지원

Palantir Foundry 스타일의 온톨로지를 파이썬으로 조회/관리합니다.
S-P-O (Subject-Predicate-Object) 트리플 구조를 활용합니다.
"""
import os
from pathlib import Path
from typing import Optional
from rdflib import Graph, Namespace, RDF, OWL, RDFS, Literal, URIRef
from rdflib.plugins.sparql import prepareQuery

WEAID = Namespace("http://weaid.ai/ontology#")

BASE_DIR = Path(__file__).resolve().parent.parent


class OntologyManager:
    """
    weAID 온톨로지 관리자
    RDF/OWL2 그래프를 로드하고 SPARQL로 쿼리합니다.

    Palantir Foundry 온톨로지 Object Types:
        - AISystem, Persona, User, Session, Command, Domain, KnowledgeItem
    Links (ObjectProperties):
        - hasPersona, belongsToDomain, hasKnowledge, processedBy, etc.
    """

    def __init__(self):
        self.graph = Graph()
        self.graph.bind("weaid", WEAID)
        self.graph.bind("rdf", RDF)
        self.graph.bind("owl", OWL)
        self.graph.bind("rdfs", RDFS)
        self._loaded = False
        self._persona_cache: dict = {}

    def load(self, ontology_path: str = None, knowledge_path: str = None) -> bool:
        """온톨로지와 지식 베이스를 로드합니다."""
        try:
            if ontology_path is None:
                ontology_path = str(BASE_DIR / "ontology" / "weaid_ontology.owl")
            if knowledge_path is None:
                knowledge_path = str(BASE_DIR / "ontology" / "knowledge_base.ttl")

            if os.path.exists(ontology_path):
                self.graph.parse(ontology_path, format="xml")

            if os.path.exists(knowledge_path):
                self.graph.parse(knowledge_path, format="turtle")

            self._loaded = True
            self._build_persona_cache()
            return True
        except Exception as e:
            print(f"[OntologyManager] 로드 오류: {e}")
            self._loaded = False
            return False

    def _build_persona_cache(self):
        """페르소나 정보를 메모리에 캐싱합니다."""
        self._persona_cache = {}
        personas = self.get_all_personas()
        for p in personas:
            agent_id = p.get("agent_id", "")
            if agent_id:
                self._persona_cache[agent_id] = p

    # =========================================================================
    # SPARQL Queries - Foundry-style Object/Link/Property 조회
    # =========================================================================

    def get_all_personas(self) -> list[dict]:
        """
        SPARQL: 모든 페르소나 조회
        Triple Pattern:
          ?system weaid:hasPersona ?persona
          ?persona weaid:hasRole ?role
        """
        query = """
        PREFIX weaid: <http://weaid.ai/ontology#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?persona ?name ?role ?emoji ?color ?description ?systemPrompt ?priority
        WHERE {
            # S: WeAIDSystem  P: hasPersona  O: ?persona
            weaid:WeAIDSystem weaid:hasPersona ?persona .

            # P: hasName  O: ?name
            ?persona weaid:hasName ?name .

            # P: hasRole  O: ?role
            ?persona weaid:hasRole ?role .

            OPTIONAL { ?persona weaid:hasEmoji ?emoji }
            OPTIONAL { ?persona weaid:hasColor ?color }
            OPTIONAL { ?persona weaid:hasDescription ?description }
            OPTIONAL { ?persona weaid:hasSystemPrompt ?systemPrompt }
            OPTIONAL { ?persona weaid:hasPriority ?priority }
        }
        ORDER BY ?priority
        """
        results = []
        try:
            for row in self.graph.query(query):
                agent_id = str(row.persona).replace(str(WEAID), "").lower()
                results.append({
                    "uri": str(row.persona),
                    "agent_id": agent_id,
                    "name": str(row.name) if row.name else "",
                    "role": str(row.role) if row.role else "",
                    "emoji": str(row.emoji) if row.emoji else "🤖",
                    "color": str(row.color) if row.color else "#666666",
                    "description": str(row.description) if row.description else "",
                    "system_prompt": str(row.systemPrompt) if row.systemPrompt else "",
                    "priority": int(str(row.priority)) if row.priority else 99,
                })
        except Exception as e:
            print(f"[OntologyManager] 페르소나 쿼리 오류: {e}")
        return results

    def get_persona_keywords(self, persona_uri: str) -> list[str]:
        """
        SPARQL: 특정 페르소나의 키워드 조회
        Triple Pattern:
          ?persona weaid:hasKeyword ?keyword
        """
        query = """
        PREFIX weaid: <http://weaid.ai/ontology#>

        SELECT ?keyword
        WHERE {
            # S: ?persona  P: hasKeyword  O: ?keyword
            <%s> weaid:hasKeyword ?keyword .
        }
        """ % persona_uri

        keywords = []
        try:
            for row in self.graph.query(query):
                keywords.append(str(row.keyword))
        except Exception as e:
            print(f"[OntologyManager] 키워드 쿼리 오류: {e}")
        return keywords

    def get_persona_capabilities(self, persona_uri: str) -> list[str]:
        """
        SPARQL: 페르소나의 기능 목록 조회
        Triple Pattern:
          ?persona weaid:hasCapability ?cap
          ?cap weaid:hasName ?capName
        """
        query = """
        PREFIX weaid: <http://weaid.ai/ontology#>

        SELECT ?capName
        WHERE {
            # S: ?persona  P: hasCapability  O: ?cap
            <%s> weaid:hasCapability ?cap .
            # S: ?cap  P: hasName  O: ?capName
            ?cap weaid:hasName ?capName .
        }
        """ % persona_uri

        caps = []
        try:
            for row in self.graph.query(query):
                caps.append(str(row.capName))
        except Exception as e:
            print(f"[OntologyManager] 기능 쿼리 오류: {e}")
        return caps

    def get_persona_domain(self, persona_uri: str) -> Optional[dict]:
        """
        SPARQL: 페르소나의 지식 도메인 조회
        Triple Pattern:
          ?persona weaid:belongsToDomain ?domain
          ?domain weaid:hasName ?domainName
        """
        query = """
        PREFIX weaid: <http://weaid.ai/ontology#>

        SELECT ?domain ?domainName ?domainDesc
        WHERE {
            # S: ?persona  P: belongsToDomain  O: ?domain
            <%s> weaid:belongsToDomain ?domain .
            ?domain weaid:hasName ?domainName .
            OPTIONAL { ?domain weaid:hasDescription ?domainDesc }
        }
        """ % persona_uri

        try:
            for row in self.graph.query(query):
                return {
                    "uri": str(row.domain),
                    "name": str(row.domainName),
                    "description": str(row.domainDesc) if row.domainDesc else "",
                }
        except Exception as e:
            print(f"[OntologyManager] 도메인 쿼리 오류: {e}")
        return None

    def find_persona_by_keyword(self, text: str) -> list[dict]:
        """
        키워드 매칭으로 의도에 맞는 페르소나를 찾습니다.
        각 페르소나의 키워드를 SPARQL로 조회하고 텍스트와 매칭합니다.

        Agentic 라우팅: S-P-O 트리플 기반 의도 분류
        """
        query = """
        PREFIX weaid: <http://weaid.ai/ontology#>

        SELECT ?persona ?keyword ?role ?name ?emoji ?priority
        WHERE {
            weaid:WeAIDSystem weaid:hasPersona ?persona .
            ?persona weaid:hasKeyword ?keyword .
            ?persona weaid:hasRole ?role .
            ?persona weaid:hasName ?name .
            OPTIONAL { ?persona weaid:hasEmoji ?emoji }
            OPTIONAL { ?persona weaid:hasPriority ?priority }
        }
        """
        scores: dict[str, dict] = {}
        try:
            for row in self.graph.query(query):
                keyword = str(row.keyword)
                if keyword in text:
                    uri = str(row.persona)
                    if uri not in scores:
                        scores[uri] = {
                            "uri": uri,
                            "agent_id": uri.replace(str(WEAID), "").lower(),
                            "name": str(row.name),
                            "role": str(row.role),
                            "emoji": str(row.emoji) if row.emoji else "🤖",
                            "priority": int(str(row.priority)) if row.priority else 99,
                            "score": 0,
                            "matched_keywords": [],
                        }
                    scores[uri]["score"] += 1
                    scores[uri]["matched_keywords"].append(keyword)
        except Exception as e:
            print(f"[OntologyManager] 키워드 매칭 오류: {e}")

        return sorted(scores.values(), key=lambda x: (-x["score"], x["priority"]))

    def get_system_info(self) -> dict:
        """
        SPARQL: weAID 시스템 전체 정보 조회
        Triple Pattern:
          weaid:WeAIDSystem weaid:hasName ?name
        """
        query = """
        PREFIX weaid: <http://weaid.ai/ontology#>

        SELECT ?name ?description
        WHERE {
            weaid:WeAIDSystem weaid:hasName ?name .
            OPTIONAL { weaid:WeAIDSystem weaid:hasDescription ?description }
        }
        """
        try:
            for row in self.graph.query(query):
                return {
                    "name": str(row.name),
                    "description": str(row.description) if row.description else "",
                }
        except Exception as e:
            print(f"[OntologyManager] 시스템 정보 쿼리 오류: {e}")
        return {"name": "weAID", "description": "생활지능파트너"}

    def get_triple_count(self) -> int:
        """그래프에 로드된 S-P-O 트리플 수를 반환합니다."""
        return len(self.graph)

    def get_persona_by_id(self, agent_id: str) -> Optional[dict]:
        """에이전트 ID로 페르소나 정보를 반환합니다."""
        # Try cache first
        for key, val in self._persona_cache.items():
            if key == agent_id or key.lower() == agent_id.lower():
                return val
        # Fallback: search all
        for p in self.get_all_personas():
            if p["agent_id"] == agent_id or p["agent_id"].lower() == agent_id.lower():
                return p
        return None

    def add_session_triple(self, session_id: str, user_id: str, timestamp: str):
        """
        런타임 S-P-O 트리플 추가 (세션 생성)
        S: User_X  P: initiates  O: Session_Y
        """
        user_uri = WEAID[f"User_{user_id}"]
        session_uri = WEAID[f"Session_{session_id}"]

        self.graph.add((user_uri, RDF.type, WEAID.User))
        self.graph.add((session_uri, RDF.type, WEAID.Session))
        self.graph.add((user_uri, WEAID.initiates, session_uri))
        self.graph.add((session_uri, WEAID.hasTimestamp, Literal(timestamp)))

    def add_command_triple(self, session_id: str, command_id: str,
                           persona_id: str, text: str):
        """
        런타임 S-P-O 트리플 추가 (명령 처리)
        S: Session_Y  P: containsCommand  O: Command_Z
        S: Command_Z  P: processedBy     O: PersonaAgent
        """
        session_uri = WEAID[f"Session_{session_id}"]
        command_uri = WEAID[f"Command_{command_id}"]
        persona_uri = WEAID[persona_id]

        self.graph.add((command_uri, RDF.type, WEAID.Command))
        self.graph.add((session_uri, WEAID.containsCommand, command_uri))
        self.graph.add((command_uri, WEAID.processedBy, persona_uri))
        self.graph.add((command_uri, WEAID.hasDescription, Literal(text[:500])))


# 싱글턴 인스턴스
ontology_manager = OntologyManager()
