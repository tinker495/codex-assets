---
name: monkey-explain
description: Explains any concept in extremely simple, stepwise language with highly structured ASCII diagrams and summaries. Use when the user asks to explain something so clearly that even a monkey could understand, requests monkey-level explanation, or needs a very structured beginner-friendly explanation.
---

# Monkey Explain

## Purpose

Use this skill when the user wants an explanation that is deliberately simple, concrete, and visually structured.

The output should make the target idea easy to follow for a complete beginner without insulting the user.

## Output Rules

- Use the user's language.
- Keep sentences short.
- Define every important term before using it deeply.
- Prefer concrete examples over abstract wording.
- Use ASCII boxes, arrows, tables, timelines, or trees when they clarify structure.
- Avoid jokes, baby talk, or condescending language.
- Do not say the user is a monkey.
- If the topic is complex, split it into layers from simplest to more detailed.

## Default Structure

```text
+--------------------+
| 1. One-line idea  |
+--------------------+
<single plain sentence>

+--------------------+
| 2. Mental model  |
+--------------------+
<ASCII diagram>

+--------------------+
| 3. Step by step  |
+--------------------+
1. <step>
2. <step>
3. <step>

+--------------------+
| 4. Tiny example |
+--------------------+
<small concrete example>

+--------------------+
| 5. Remember this |
+--------------------+
- <key point>
- <key point>
```

## Explanation Pattern

1. Name the thing.
2. Say what problem it solves.
3. Show the simplest possible shape in ASCII.
4. Walk through one small example.
5. State the common mistake or confusion.
6. End with a compact memory hook.

## ASCII Guidance

Use diagrams like these:

```text
Input ---> Process ---> Output
```

```text
+----------+      +----------+
| Thing A  | ---> | Thing B  |
+----------+      +----------+
```

```text
Big idea
|-- Part 1
|-- Part 2
`-- Part 3
```

## When Details Are Missing

If the user names a broad topic without context, choose the most common meaning and explain it. Add one short note about the assumption.

Ask a question only when different meanings would produce a seriously different explanation.
