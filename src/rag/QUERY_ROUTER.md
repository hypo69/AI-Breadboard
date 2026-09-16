# Query Router: Smart Search Strategy Decision

## Overview

QueryRouter analyzes user queries to determine the optimal search strategy:

- **text** - Only search text documents (TF-IDF/Gemini embeddings)
- **pixel** - Only search images (CLIP embeddings + FAISS index)
- **hybrid** - Search both text documents and images, merge results

## Architecture

```
Query Input
    ↓
┌─────────────────────────────────────┐
│ 1. Language Detection               │
│    Detect: Russian/English/Mixed    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. Visual Keyword Extraction        │
│    Find: покажи, найди, кнопка...   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. Pattern Matching                 │
│    Visual: "где.*?кнопка"           │
│    Text: "объясни.*?как"            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. Routing Decision                 │
│    Combine signals → Decision       │
└─────────────────────────────────────┘
    ↓
QueryAnalysis
├── routing_type: text|pixel|hybrid
├── confidence: 0.0-1.0
├── visual_keywords: [...]
└── reason: explanation
```

## Visual Keywords (Russian)

### Direct Commands
- **покажи**, **показать**, **покажет** - "Show [element]"
- **найди**, **найдите**, **найти** - "Find [element]"
- **где**, **где-то** - "Where is [element]?"

### UI Elements
- **кнопка**, **кнопку**, **кнопке** - Button
- **меню** - Menu
- **иконка**, **иконку** - Icon
- **интерфейс**, **интерфейса** - Interface
- **элемент** - Element

### Visual Properties
- **выглядит**, **видно**, **виден** - "Looks like", "Visible"
- **внешний**, **внешний вид** - Appearance
- **слева**, **справа**, **сверху**, **снизу** - Spatial: left, right, top, bottom

### Content Types
- **скриншот**, **скриншотом**, **скриншотов** - Screenshot
- **экран**, **экране** - Screen
- **фото**, **картинка**, **изображение** - Photo/image

### Actions
- **нажми**, **нажмите** - Click/press
- **кликни**, **кликните** - Click
- **посмотри**, **смотри** - Look at

## Visual Keywords (English)

Similar categories as Russian:
- Commands: show, find, look, where
- UI Elements: button, menu, icon, interface
- Visual: looks, appearance, visible
- Spatial: left, right, top, bottom
- Content: screenshot, screen, image, photo
- Actions: click, tap, show

## Pattern Examples

### High Confidence Visual (0.95)
```
"Покажи кнопку сохранения"
Pattern: "покажи.*?кнопку" ✓
Visual keywords: покажи, кнопку
Decision: PIXEL (confidence 0.95)
```

### Medium Confidence Visual (0.75-0.85)
```
"Где на интерфейсе кнопка отправки?"
Pattern: "где.*?кнопка" ✓
Visual keywords: где, кнопка, интерфейсе
Decision: HYBRID (confidence 0.80)
```

### Text Intent (0.85+)
```
"Объясни как работает система логирования"
Pattern: "объясни.*?как" ✓
Decision: TEXT (confidence 0.90)
Reason: Text pattern detected - explanatory query
```

### Mixed Intent
```
"Покажи на скриншоте где находится кнопка и объясни что она делает"
Visual score: 0.85
Text score: 0.75
Decision: HYBRID (confidence 0.80)
```

### Ambiguous Query
```
"Найди информацию о кнопке"
Mixed signals - could be text search for info or visual search
Decision: HYBRID (confidence 0.50)
Reason: Ambiguous query - defaulting to hybrid search
```

## API Usage

### Basic Analysis

```python
from src.rag import get_query_router

router = get_query_router()

# Analyze query
analysis = router.analyze("Покажи кнопку сохранения")

print(f"Routing: {analysis.routing_type.value}")
print(f"Confidence: {analysis.confidence:.2f}")
print(f"Keywords: {analysis.visual_keywords}")
print(f"Reason: {analysis.reason}")
```

### Output

```
Routing: pixel
Confidence: 0.95
Keywords: ['покажи', 'кнопку']
Reason: Strong visual indicators: keywords=['покажи', 'кнопку'], pattern_score=0.95
```

### Routing Decision

```python
analysis = router.analyze(query)

if analysis.routing_type == RoutingType.TEXT:
    # Search only text documents
    results = doc_rag.search(query)
    results = [r for r in results if r['source_type'] == 'text']

elif analysis.routing_type == RoutingType.PIXEL:
    # Search only images
    results = doc_rag.search(query)
    results = [r for r in results if r['source_type'] == 'pixel']

elif analysis.routing_type == RoutingType.HYBRID:
    # Search both - already hybrid in DocumentRAGManager
    results = doc_rag.search(query)
```

### Configuration

```python
router = get_query_router()
config = router.get_config()

print(f"Russian keywords: {config['visual_keywords_ru_count']}")
print(f"English keywords: {config['visual_keywords_en_count']}")
print(f"Visual patterns: {config['visual_patterns_count']}")
print(f"Text patterns: {config['text_patterns_count']}")
```

## Decision Logic

### Routing Decision Matrix

| Signal | Score | Decision | Confidence |
|--------|-------|----------|-----------|
| Visual >= 0.85, no text | - | PIXEL | 0.95 |
| Visual >= 0.85, text < 0.5 | - | PIXEL | high |
| Visual >= 0.85, text >= 0.5 | - | HYBRID | medium |
| Visual >= 0.75, keywords >= 2 | - | HYBRID | 0.75-0.80 |
| Text >= 0.85 | - | TEXT | high |
| Keyword ratio >= 20% | - | HYBRID | 0.5-0.7 |
| Ambiguous | - | HYBRID | 0.5 |

### Scoring Algorithm

```
visual_score = max(pattern_matches)  # 0-1
keyword_ratio = visual_keywords / query_words

if visual_score >= 0.85 and len(keywords) >= 3:
    routing = PIXEL
    confidence = 0.95

elif visual_score >= 0.75 and len(keywords) >= 2:
    routing = HYBRID
    confidence = (visual_score + 0.5) / 2

elif text_score >= 0.85:
    routing = TEXT
    confidence = text_score

elif keyword_ratio >= 0.2:
    routing = HYBRID
    confidence = 0.5 + keyword_ratio

else:
    routing = HYBRID  # Safe default
    confidence = 0.5
```

## Language Support

### Russian (Русский)
- Full keyword dictionary: 30+ keywords
- Pattern matching for Russian text
- Cyrillic character detection

### English (English)
- Full keyword dictionary: 25+ keywords
- Pattern matching for English text
- ASCII character detection

### Mixed (Russian + English)
- Blended keyword matching
- Both pattern sets applied
- Language-specific patterns prioritized

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Language detection | <1ms | Character analysis |
| Keyword extraction | 1-2ms | Word tokenization |
| Pattern matching | 2-5ms | Regex compilation cached |
| Routing decision | 1-2ms | Scoring algorithm |
| **Total analysis** | **5-10ms** | Negligible overhead |

## Examples

### Example 1: Clear Visual Query

```python
query = "Найди на скриншоте кнопку сохранить"

router.analyze(query)
# → RoutingType.PIXEL
# Keywords: найди, скриншоте, кнопку, сохранить
# Confidence: 0.95
# Reason: Strong visual indicators
```

### Example 2: Clear Text Query

```python
query = "Объясни что такое REST API"

router.analyze(query)
# → RoutingType.TEXT
# Keywords: (none)
# Confidence: 0.90
# Reason: Text intent detected
```

### Example 3: Mixed Intent

```python
query = "Покажи где кнопка отправки и как её использовать"

router.analyze(query)
# → RoutingType.HYBRID
# Keywords: покажи, кнопка, отправки
# Confidence: 0.75
# Reason: Mixed intent - visual and text signals
```

### Example 4: Ambiguous Query

```python
query = "Информация о кнопке"

router.analyze(query)
# → RoutingType.HYBRID
# Keywords: (none)
# Confidence: 0.50
# Reason: Ambiguous - could be text or visual
```

## Integration with DocumentRAGManager

### Automatic Routing

```python
from src.rag import DocumentRAGManager, get_query_router

doc_rag = DocumentRAGManager()
router = get_query_router()

query = "Покажи кнопку сохранения"

# Analyze query
analysis = router.analyze(query)

# Route accordingly
if analysis.routing_type == RoutingType.TEXT:
    results = doc_rag.search(query)
    results = [r for r in results if r['source_type'] == 'text']
elif analysis.routing_type == RoutingType.PIXEL:
    results = doc_rag.search(query)
    results = [r for r in results if r['source_type'] == 'pixel']
else:  # HYBRID
    results = doc_rag.search(query)  # Already hybrid
```

## Future Enhancements

1. **Machine Learning** - Train classifier on query examples
2. **User Feedback** - Improve scores based on user selections
3. **Context Awareness** - Track conversation history
4. **Domain Adaptation** - Customize keywords for specific domains
5. **Semantic Analysis** - Use embeddings for query intent

## Testing

```python
# Test visual queries
assert router.analyze("Покажи кнопку").routing_type == RoutingType.PIXEL

# Test text queries
assert router.analyze("Объясни как").routing_type == RoutingType.TEXT

# Test mixed queries
analysis = router.analyze("Покажи и объясни")
assert analysis.routing_type == RoutingType.HYBRID

# Test ambiguous
analysis = router.analyze("информация")
assert analysis.routing_type == RoutingType.HYBRID
```

## Configuration Reference

### Class Constants

```python
VISUAL_KEYWORDS_RU: Set[str]     # Russian keywords
VISUAL_KEYWORDS_EN: Set[str]     # English keywords
VISUAL_PATTERNS: List[Tuple]      # Regex patterns (pattern, confidence)
TEXT_PATTERNS: List[Tuple]        # Text-intent patterns
```

### QueryAnalysis Fields

```python
@dataclass
class QueryAnalysis:
    query: str                     # Original query
    routing_type: RoutingType      # text | pixel | hybrid
    language: QueryLanguage        # russian | english | mixed
    visual_keywords: List[str]     # Found visual keywords
    confidence: float              # 0.0-1.0 confidence score
    reason: str                    # Human-readable explanation
    metadata: Dict                 # Additional analysis data
```

## References

- **Implementation:** `src/rag/query_router.py`
- **Integration:** Task 8 (RAGEngine integration)
- **Usage:** Task 7 documentation
