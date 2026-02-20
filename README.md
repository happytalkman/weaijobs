# 🏠 weAID - 생활지능파트너

> **Living Intelligence AI Partner**
> RDF/OWL2 온톨로지 기반 Agentic AI 홈 어시스턴트

---

## 📋 개요

**weAID**는 가정용 AI 생활지능파트너입니다.
5가지 전문 페르소나가 일상생활의 모든 질문에 답해드립니다.

| 페르소나 | 역할 | 전문 분야 |
|---------|------|----------|
| 📚 선생님 | 과외선생님 | 수학, 과학, 국어, 영어, 역사 |
| 💪 코치님 | 홈트레이닝코치 | 운동, 체력, 다이어트, 건강 |
| 👨‍🍳 셰프님 | 요리사 | 레시피, 식단, 영양, 요리팁 |
| ⚖️ 변호사님 | 가정법률변호사 | 임대차, 가족법, 소비자, 노동 |
| 🧘 선생님 | 명상심리상담사 | 명상, 스트레스, 감정, 마음챙김 |

---

## ⚡ 핵심 기술: Palantir Foundry 스타일 온톨로지

### RDF/OWL2 S-P-O 트리플 구조

```turtle
# Subject  Predicate         Object
weaid:WeAIDSystem weaid:hasPersona weaid:TutorAgent .
weaid:WeAIDSystem weaid:hasPersona weaid:TrainerAgent .
weaid:WeAIDSystem weaid:hasPersona weaid:ChefAgent .
weaid:WeAIDSystem weaid:hasPersona weaid:LawyerAgent .
weaid:WeAIDSystem weaid:hasPersona weaid:TherapistAgent .

weaid:Command_001 weaid:processedBy  weaid:TutorAgent .
weaid:TutorAgent  weaid:belongsToDomain weaid:EducationDomain .
weaid:EducationDomain weaid:hasKnowledge weaid:MathKnowledge .
```

### Palantir Foundry 매핑

| Foundry 개념 | RDF/OWL2 구현 |
|-------------|--------------|
| Object Types | `owl:Class` |
| Links | `owl:ObjectProperty` |
| Properties | `owl:DatatypeProperty` |
| Actions | 런타임 트리플 추가 |
| SPARQL | 온톨로지 쿼리 |

### 아키텍처 흐름

```
사용자 음성/텍스트
       ↓
[STT: 음성→텍스트]
       ↓
[Orchestrator]
  ① SPARQL 키워드 매칭 (1차 라우팅)
     → ?persona weaid:hasKeyword ?keyword
  ② Claude tool_use 의도 분류 (정밀 라우팅)
  ③ S-P-O 트리플 기록
     → Command --processedBy--> Persona
       ↓
[페르소나 에이전트 (Claude API)]
  📚 TutorAgent
  💪 TrainerAgent
  👨‍🍳 ChefAgent
  ⚖️ LawyerAgent
  🧘 TherapistAgent
       ↓
[TTS: 텍스트→음성]
       ↓
사용자에게 응답
```

---

## 🚀 시작하기

### 1. 설치

```bash
# Python 3.11+ 필요
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 설정
```

### 3. 실행

```bash
# 웹 서버 실행 (브라우저 접속)
python main.py

# CLI 모드 (터미널)
python main.py --cli

# 개발 모드
python main.py --reload
```

### 4. 접속

```
http://localhost:8001
```

---

## 📁 프로젝트 구조

```
weaijobs/
├── ontology/
│   ├── weaid_ontology.owl    # RDF/OWL2 온톨로지 정의
│   └── knowledge_base.ttl    # Turtle 형식 지식 베이스 (인스턴스)
├── agents/
│   ├── base_agent.py         # 기본 에이전트 클래스
│   ├── orchestrator.py       # 오케스트레이터 (의도 분류 + 라우팅)
│   ├── tutor_agent.py        # 과외선생님 페르소나
│   ├── trainer_agent.py      # 홈트레이닝코치 페르소나
│   ├── chef_agent.py         # 요리사 페르소나
│   ├── lawyer_agent.py       # 가정법률변호사 페르소나
│   └── therapist_agent.py    # 명상심리상담사 페르소나
├── knowledge/
│   └── ontology_manager.py   # RDF 그래프 + SPARQL 쿼리
├── voice/
│   ├── speech_to_text.py     # STT (음성→텍스트)
│   └── text_to_speech.py     # TTS (텍스트→음성)
├── api/
│   └── main.py               # FastAPI 백엔드 + WebSocket
├── ui/
│   └── index.html            # 웹 UI
├── config/
│   └── settings.py           # 설정
├── main.py                   # 진입점
├── requirements.txt
└── .env.example
```

---

## 🔌 API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/` | 웹 UI |
| `GET` | `/api/health` | 서버 상태 |
| `GET` | `/api/personas` | 페르소나 목록 |
| `GET` | `/api/ontology` | 온톨로지 구조 정보 |
| `POST` | `/api/chat` | 텍스트 채팅 |
| `POST` | `/api/voice/transcribe` | 음성 → 텍스트 |
| `POST` | `/api/voice/chat` | 음성 채팅 (올인원) |
| `GET` | `/api/tts?text=...` | 텍스트 → 음성 MP3 |
| `WS` | `/ws/{session_id}` | WebSocket 실시간 채팅 |

---

## 💬 사용 예시

```python
# REST API 사용 예시
import requests

response = requests.post("http://localhost:8001/api/chat", json={
    "message": "냉장고에 달걀, 감자, 양파 있어. 뭐 만들어 먹어?",
    "session_id": "my_session"
})

data = response.json()
print(f"[{data['persona_role']}] {data['response']}")
# [요리사] 스페인식 감자 오믈렛(Tortilla Española)을 만들어보세요!...
```

---

## ⚠️ 법률/의료 면책 고지

- 법률 상담은 일반적인 정보 제공이며 정식 법률 자문을 대체하지 않습니다
- 심리 상담은 전문 치료를 대체하지 않습니다
- 의료적 판단이 필요한 경우 반드시 전문가와 상담하세요

---

## 📄 라이선스

MIT License
