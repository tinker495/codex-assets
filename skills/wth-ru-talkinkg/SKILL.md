---
name: wth-ru-talkinkg
description: Rescues a Codex /side conversation when the user has lost the thread of a technical explanation, using gap-finding, zoom-out maps, concrete examples, known-concept bridges, and grilling questions until understanding is restored. Use only from Codex /side when the user says they do not understand, cannot follow the context, asks what the agent is talking about, or asks to be grilled until it makes sense.
disable-model-invocation: true
---

# WTH RU Talkinkg

## When To Use

Use this skill only in Codex `/side` conversations when the user interrupts because they cannot follow what the agent is saying.

The goal is not to finish the coding task. The goal is to rebuild shared understanding until the user says the explanation now makes sense.

Do not use this for the agent's own uncertainty, ambiguous requirements, or routine confirmation questions.

## Loop And Exit

```text
1. Locate the gap -> 2. Re-explain with one strategy -> 3. Check understanding
                              ^                              |
                              | failed / partial             |
                              +------------------------------+

Exit only when the user explicitly says it now makes sense.
```

## Step 1: Locate The Gap

Do this first. Do not guess where the confusion is.

Ask one narrow question, such as "마지막으로 여기까진 알겠다 싶었던 지점이 어디였나요?", "막힌 게 용어인가요, 왜 이걸 하는지인가요, 아니면 전체에서 어디 위치인지인가요?", or "제가 방금 말한 것 중 제일 낯선 단어 하나만 찍어주세요."

## Step 2: Re-Explain

- Start from the outermost layer the user understands, then walk inward one layer at a time.
- Use one explanation strategy per round. If it fails, switch strategy instead of repeating harder.
- Prefer real files, real numbers, real inputs, and real outputs when repo context exists.
- Watch for jargon smuggled into the simpler explanation. Define terms before using them.
- Do not dump a long lecture. Teach in short rounds.

## Explanation Strategies

- Zoom-out map: show the broad system shape and where the current detail sits.
- Known-concept bridge: connect the new idea to something the user already understands.
- Concrete example: replace abstraction with one specific case.
- Trace: show "input -> process -> output".
- Before/after: show what changes if the idea is applied.
- Counterexample: show a wrong interpretation and why it fails.
- ELI5 fallback: strip every technical term when abstraction itself is the problem.

## Response Shape

```text
1. Gap / question: <what broke, or one question to find it>
2. Big picture + map: <one or two sentences plus ASCII diagram>
3. Terms: <plain meanings for the key words>
4. Tiny example: <one concrete input -> output example>
5. Check: <one applied question that tests understanding>
```

## Step 3: Comprehension Check

Always ask one applied question. Do not accept a weak acknowledgement as comprehension.

Good checks: "그럼 여기서 X를 빼면 어떤 문제가 생길까요?", "방금 설명한 걸 한 줄로 표현하면 어떻게 되나요?", or "이 입력이 들어오면 어느 단계에서 막힐까요?"

If the answer is vague, hedged, or wrong, say it directly and try a different strategy:

```text
그건 살짝 다릅니다. 다른 각도로 다시 가볼게요.
```

## Exit

- Exit only when the user explicitly says "이제 알겠다", "이해됐어", or equivalent.
- Then briefly re-anchor to the original task: "그럼 원래 하던 <작업>으로 돌아갈게요."
- If the user says to proceed without understanding, respect it once, but flag the risk briefly.

## Guardrails

- Use the user's language; do not insult, baby-talk, or imply the user is at fault.
- Ask one question per turn and do not resume implementation inside this skill.
- Do not use external research unless the confusion depends on an external fact.
- If the user asks "what should I know first?", give the minimum prerequisite ladder.
- If the user's confusion comes from missing repo facts, inspect the repo before explaining.
- Do not treat this as a one-shot answer. It is an interactive loop.
