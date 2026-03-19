# Brain Skill - Task Router

## Purpose
Classify incoming tasks and route to specialized agent models for optimal performance and token efficiency.

## When to Use
Automatically loaded for all incoming messages. Use when:
- User sends a complex task requiring specialized handling
- Task could benefit from a specific model (coding, writing, analysis)
- Multiple sub-tasks need parallel execution

## Model Routing Logic

### 1. Analyze Task Type
Check for keywords and intent:

| Task Type | Keywords | Route To | Model |
|-----------|----------|----------|-------|
| **Coding** | code, function, bug, debug, API, script, build, refactor | Coder | deepseek-coder:6.7b |
| **Writing** | write, edit, rewrite, summarize, email, post, content | Writer | mistral:7b |
| **Analysis** | analyze, data, compare, why, trend, pattern, stats | Analyst | glm-4.7-flash |
| **Research** | search, find, look up, research, fact-check | Brain | qwen3.5 + web search |
| **Simple Q&A** | what is, who is, when, simple fact | Quick | phi4 OR groq/llama-3.1-8b-instant |
| **Fast Response** | quick, fast, instant, urgent, now | Fast | groq/llama-3.1-8b-instant |
| **Complex reasoning** | multi-step, plan, strategy, architecture | Brain | qwen3.5 OR groq/llama-3.1-70b-versatile |
| **Deep Advice/Thinking** | advise, think deeply, what do you think, serious, important | Advisor | nemotron-3-super:cloud |

### 2. Advisor Mode (Nemotron)
**Nemotron is reserved for heavy thinking** — only use when:
- User explicitly asks for advice/opinion ("what do you think?", "advise me")
- High-stakes decisions (financial, legal, medical, life choices)
- Complex ethical or philosophical questions
- User says "think deeply" or "give me your best answer"

**Do NOT use Nemotron for:**
- Routine tasks
- Simple facts
- Code generation
- Creative writing
- Data analysis

This keeps cloud costs low and respects the "only thinks when asked" principle.

### 2b. Groq Cloud Models (NEW)
**Groq provides ultra-fast inference** (1000+ tokens/sec) with free tier (1M tokens/day):

| Model | Context | Strengths | Use For |
|-------|---------|-----------|---------|
| **llama-3.1-8b-instant** | 128K | Blazing fast | Simple Q&A, quick responses |
| **llama-3.1-70b-versatile** | 128K | Strong reasoning | Complex tasks, coding, analysis |
| **mixtral-8x7b-32768** | 32K | MoE architecture | General purpose, balanced |
| **gemma-7b-it** | 8K | Lightweight | Quick classification, short tasks |

**Groq advantages:**
- ✅ Fastest cloud LLM (real-time responses)
- ✅ Free tier generous (1M tokens/day)
- ✅ OpenAI-compatible API
- ✅ No rate limits on free tier

**Groq limitations:**
- ⚠️ Cloud-based (requires API key)
- ⚠️ 70b model slower than 8b (trade quality for speed)

### 2. Spawn Specialized Agent
Use `sessions_spawn` with appropriate model:

```
sessions_spawn(
  task: "<original user task>",
  model: "<routed model>",
  label: "<task type>"
)
```

### 3. Merge Results
For multi-agent tasks:
- Collect outputs from all spawned agents
- Synthesize into coherent response
- Credit which model handled what

## Efficiency Rules
- Default to Quick (phi4) for simple tasks
- Escalate to Brain (qwen3.5) only when needed
- Never use Coder for writing tasks
- Never use Writer for code tasks

## ⚠️ Model Capability Checks
**Critical:** Not all Ollama models support tool calls!

| Model | Tool Support | Use For |
|-------|--------------|---------|
| qwen3.5 | ✅ Yes | Brain, complex reasoning |
| glm-4.7-flash | ✅ Yes | Analysis with tools |
| deepseek-coder:6.7b | ❌ No | Code generation ONLY (no subagent spawns) |
| mistral:7b | ⚠️ Varies | Writing (test first) |
| phi4 | ⚠️ Varies | Simple Q&A (test first) |
| llama3.2:3b | ✅ Yes | Fast local tasks |
| qwen2.5:7b | ✅ Yes | General purpose |
| **groq/llama-3.1-8b-instant** | ✅ Yes | Fast cloud Q&A |
| **groq/llama-3.1-70b-versatile** | ✅ Yes | Complex cloud reasoning |
| **groq/mixtral-8x7b** | ✅ Yes | Balanced cloud tasks |
| **groq/gemma-7b-it** | ✅ Yes | Lightweight cloud |

**Rule:** Before spawning a subagent, verify the model supports tools. If unsure:
1. Handle the task directly in main session
2. Use exec for code-related tasks
3. Fall back to Brain (qwen3.5) which has confirmed tool support

**Groq models** all support tool calls via OpenAI-compatible API.

## Examples

**User:** "Fix this Python bug"
→ Route to: Coder (deepseek-coder:6.7b)

**User:** "Write a welcome email"
→ Route to: Writer (mistral:7b)

**User:** "Why did my portfolio drop?"
→ Route to: Analyst (glm-4.7-flash) + data fetch

**User:** "What's 2+2?"
→ Route to: Quick (phi4) OR Fast (groq/llama-3.1-8b-instant)

**User:** "I need a fast answer"
→ Route to: Fast (groq/llama-3.1-8b-instant)

**User:** "Analyze this complex dataset"
→ Route to: Analyst (glm-4.7-flash) OR groq/llama-3.1-70b-versatile

**User:** "Advise me on this investment"
→ Route to: Advisor (nemotron-3-super:cloud)

## Fallback
If routing unclear, handle with Brain (qwen3.5) and learn for next time.

## Priority Order
When multiple models could work:
1. **Local first** (free, offline)
2. **Groq 8b** for speed (free cloud)
3. **Groq 70b** for quality (free cloud)
4. **Nemotron** only for explicit advice requests
