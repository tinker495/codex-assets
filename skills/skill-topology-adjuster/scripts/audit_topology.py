#!/usr/bin/env python3
"""Topology/delegation strict auditor for Codex skills."""

from __future__ import annotations

import argparse
import itertools
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

DELEGATION_KEYWORDS = (
    "delegate",
    "delegation",
    "handoff",
    "hand off",
    "위임",
    "handover",
    "orchestrator -> specialist",
)
SUB_AGENT_GUIDANCE_KEYWORDS = (
    "delegate",
    "delegation",
    "handoff",
    "sub-agent",
    "fresh-context",
    "long-running",
    "timeout",
    "run.sh",
)
STANDALONE_MARKERS = ("standalone", "delegation optional")
ORCHESTRATOR_ROLES = {"orchestrator", "specialist-orchestrator"}
META_ORCHESTRATOR_ROLES = {"meta-orchestrator"}
UTILITY_LIKE_ROLES = {"utility", "meta-tool"}
RESPONSIBILITY_SECTION_HINTS = (
    "objective",
    "purpose",
    "ownership",
    "scope",
    "workflow",
    "trigger",
    "use case",
    "responsibilit",
)
RESPONSIBILITY_STOPWORDS = {
    "about",
    "across",
    "agent",
    "agents",
    "analysis",
    "and",
    "are",
    "assist",
    "assistant",
    "best",
    "by",
    "can",
    "check",
    "codex",
    "context",
    "create",
    "creating",
    "creation",
    "default",
    "delegation",
    "design",
    "editing",
    "ensure",
    "for",
    "from",
    "guide",
    "handle",
    "help",
    "if",
    "in",
    "install",
    "into",
    "is",
    "it",
    "its",
    "mode",
    "new",
    "not",
    "of",
    "on",
    "or",
    "output",
    "path",
    "process",
    "request",
    "requests",
    "run",
    "should",
    "skill",
    "skills",
    "task",
    "tasks",
    "that",
    "the",
    "their",
    "this",
    "to",
    "tool",
    "tools",
    "use",
    "used",
    "user",
    "users",
    "using",
    "when",
    "where",
    "with",
    "workflow",
    "workflows",
}
TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9-]{2,}")
MERMAID_NODE_PATTERN = re.compile(r'([A-Za-z0-9_]+)\["([^"]+)"\]')
MERMAID_EDGE_PATTERN = re.compile(
    r"([A-Za-z0-9_]+)(?:\[[^\]]*\])?\s*-->\s*([A-Za-z0-9_]+)(?:\[[^\]]*\])?"
)
OVERLAP_MIN_SHARED_TOKENS = 7
OVERLAP_MIN_SIMILARITY = 0.34
OVERLAP_UTILITY_MIN_SIMILARITY = 0.42


@dataclass(frozen=True)
class SkillRecord:
    name: str
    path: Path
    text: str


def parse_args() -> argparse.Namespace:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    default_skills_root = codex_home / "skills"
    default_topology = (
        default_skills_root / "skill-topology-adjuster" / "references" / "skill_topology.md"
    )
    parser = argparse.ArgumentParser(
        description=(
            "Audit all installed skills for topology/delegation consistency. "
            "Returns exit code 1 when any needs-fix item is found."
        )
    )
    parser.add_argument("--skills-root", type=Path, default=default_skills_root)
    parser.add_argument("--topology", type=Path, default=default_topology)
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    return parser.parse_args()


def load_skills(skills_root: Path) -> list[SkillRecord]:
    records: list[SkillRecord] = []
    for path in sorted(skills_root.rglob("SKILL.md")):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"^name:\s*(.+)$", text, flags=re.M)
        if not match:
            continue
        name = match.group(1).strip().strip('"')
        records.append(SkillRecord(name=name, path=path, text=text))
    return records


def parse_role_map(topology_text: str) -> dict[str, str]:
    role_map: dict[str, str] = {}
    for line in topology_text.splitlines():
        match = re.match(r"\| `([^`]+)` \| ([^|]+) \|", line)
        if match:
            role_map[match.group(1)] = match.group(2).strip()
    return role_map


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    end_index = -1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break
    if end_index == -1:
        return {}

    frontmatter: dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return frontmatter


def remove_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text

    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[idx + 1 :])
    return text


def split_sections(text: str) -> dict[str, str]:
    section_lines: dict[str, list[str]] = {}
    current = "__body__"
    section_lines[current] = []
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip().lower()
            section_lines.setdefault(current, [])
            continue
        section_lines.setdefault(current, []).append(line)
    return {name: "\n".join(lines).strip() for name, lines in section_lines.items()}


def normalize_token(token: str) -> str:
    value = token.lower().strip()
    if value.endswith("s") and len(value) > 4:
        value = value[:-1]
    return value


def tokenize(text: str) -> set[str]:
    tokens: set[str] = set()
    for match in TOKEN_PATTERN.findall(text.lower()):
        for piece in match.replace("-", " ").split():
            token = normalize_token(piece)
            if len(token) < 4:
                continue
            if token in RESPONSIBILITY_STOPWORDS:
                continue
            tokens.add(token)
    return tokens


def build_responsibility_profile(skill: SkillRecord) -> tuple[str, set[str]]:
    frontmatter = parse_frontmatter(skill.text)
    text_without_frontmatter = remove_frontmatter(skill.text)
    sections = split_sections(text_without_frontmatter)

    selected_chunks: list[str] = []
    description = frontmatter.get("description", "")
    if description:
        selected_chunks.append(description)

    for section_name, section_body in sections.items():
        if section_name == "__body__":
            continue
        if any(hint in section_name for hint in RESPONSIBILITY_SECTION_HINTS):
            selected_chunks.append(section_body)

    intro_lines = [line for line in sections.get("__body__", "").splitlines() if line.strip()]
    if intro_lines:
        selected_chunks.append("\n".join(intro_lines[:40]))

    if not selected_chunks:
        selected_chunks.append(skill.text)

    corpus = "\n".join(chunk.strip() for chunk in selected_chunks if chunk.strip())
    return corpus, tokenize(corpus)


def extract_section(text: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.M | re.S)
    return match.group(1) if match else ""


def parse_mermaid_aliases_and_edges(section_text: str) -> tuple[dict[str, str], set[tuple[str, str]]]:
    alias_to_label: dict[str, str] = {}
    edges: set[tuple[str, str]] = set()
    for raw in section_text.splitlines():
        line = raw.strip()
        for alias, label in MERMAID_NODE_PATTERN.findall(line):
            alias_to_label.setdefault(alias, label)
        match = MERMAID_EDGE_PATTERN.search(line)
        if match:
            edges.add((match.group(1), match.group(2)))
    return alias_to_label, edges


def detect_responsibility_overlaps(
    names: list[str],
    name_to_skill: dict[str, SkillRecord],
    role_map: dict[str, str],
) -> list[dict]:
    profiles: dict[str, tuple[str, set[str]]] = {}
    for name in names:
        profiles[name] = build_responsibility_profile(name_to_skill[name])
    token_document_frequency: Counter[str] = Counter()
    for _, tokens in profiles.values():
        token_document_frequency.update(tokens)
    max_common_token_frequency = max(4, len(names) // 3)

    overlaps: list[dict] = []
    for left, right in itertools.combinations(names, 2):
        left_text = name_to_skill[left].text
        right_text = name_to_skill[right].text
        has_explicit_link = right in left_text or left in right_text
        if has_explicit_link:
            continue

        left_tokens = {
            token for token in profiles[left][1] if token_document_frequency[token] <= max_common_token_frequency
        }
        right_tokens = {
            token for token in profiles[right][1] if token_document_frequency[token] <= max_common_token_frequency
        }
        if not left_tokens or not right_tokens:
            continue

        shared_tokens = sorted(left_tokens & right_tokens)
        if len(shared_tokens) < OVERLAP_MIN_SHARED_TOKENS:
            continue

        similarity = len(shared_tokens) / len(left_tokens | right_tokens)
        left_role = role_map.get(left, "missing")
        right_role = role_map.get(right, "missing")

        min_similarity = OVERLAP_MIN_SIMILARITY
        if UTILITY_LIKE_ROLES & {left_role, right_role}:
            min_similarity = OVERLAP_UTILITY_MIN_SIMILARITY
        if similarity < min_similarity:
            continue

        overlaps.append(
            {
                "skills": [left, right],
                "roles": [left_role, right_role],
                "similarity": round(similarity, 3),
                "shared_token_count": len(shared_tokens),
                "shared_tokens_preview": shared_tokens[:12],
            }
        )

    return sorted(overlaps, key=lambda row: (row["similarity"], row["shared_token_count"]), reverse=True)


def audit(skills: list[SkillRecord], role_map: dict[str, str], topology_text: str) -> dict:
    name_to_skill = {skill.name: skill for skill in skills}
    installed_names = sorted(name_to_skill)
    role_map_names = sorted(role_map)

    layers_section = extract_section(topology_text, "Orchestration Layers")
    graph_section = extract_section(topology_text, "Delegation Graph")
    tree_section = extract_section(topology_text, "Delegation Tree (Operational View)")
    graph_alias_to_label, graph_edges = parse_mermaid_aliases_and_edges(graph_section)
    tree_alias_to_label, tree_edges = parse_mermaid_aliases_and_edges(tree_section)
    missing_graph_edges_in_tree = sorted(graph_edges - tree_edges)
    edge_sync_impacted_skills: set[str] = set()
    for left_alias, right_alias in missing_graph_edges_in_tree:
        for alias in (left_alias, right_alias):
            resolved = graph_alias_to_label.get(alias) or tree_alias_to_label.get(alias) or alias
            if resolved in installed_names:
                edge_sync_impacted_skills.add(resolved)

    required_graph_doc_edges: set[tuple[str, str]] = set()
    for left_alias, right_alias in graph_edges:
        source = graph_alias_to_label.get(left_alias) or tree_alias_to_label.get(left_alias) or left_alias
        target = graph_alias_to_label.get(right_alias) or tree_alias_to_label.get(right_alias) or right_alias
        if source in installed_names and target in installed_names and source != target:
            required_graph_doc_edges.add((source, target))
    required_graph_targets_by_skill: dict[str, set[str]] = {name: set() for name in installed_names}
    for source, target in required_graph_doc_edges:
        required_graph_targets_by_skill[source].add(target)

    meta_tool_any_skill_access = bool(
        re.search(r"codex-exec-sub-agent", topology_text, flags=re.I)
        and re.search(r"any skill", topology_text, flags=re.I)
    )
    sub_agent_aliases = {
        alias for alias, label in graph_alias_to_label.items() if label == "codex-exec-sub-agent"
    } or {"CESA"}
    required_sub_agent_doc_skills: set[str] = set()
    for left_alias, right_alias in graph_edges:
        if right_alias not in sub_agent_aliases:
            continue
        source = graph_alias_to_label.get(left_alias) or tree_alias_to_label.get(left_alias) or left_alias
        if source in installed_names and source != "codex-exec-sub-agent":
            required_sub_agent_doc_skills.add(source)
    overlap_candidates = detect_responsibility_overlaps(
        names=installed_names,
        name_to_skill=name_to_skill,
        role_map=role_map,
    )
    overlap_index: dict[str, list[dict]] = {name: [] for name in installed_names}
    for candidate in overlap_candidates:
        left, right = candidate["skills"]
        overlap_index[left].append(candidate)
        overlap_index[right].append(candidate)

    per_skill: dict[str, dict] = {}
    missing_graph_edge_docs: list[str] = []
    missing_sub_agent_doc_skills: list[str] = []
    weak_sub_agent_doc_skills: list[str] = []
    for name in installed_names:
        text = name_to_skill[name].text
        lower = text.lower()
        refs = sorted(other for other in installed_names if other != name and other in text)
        delegation_hits = [kw for kw in DELEGATION_KEYWORDS if kw in lower or kw in text]
        sub_agent_lines = [line.lower() for line in text.splitlines() if "codex-exec-sub-agent" in line.lower()]
        has_sub_agent_ref = bool(sub_agent_lines)
        has_sub_agent_guidance = bool(
            sub_agent_lines
            and any(
                any(keyword in line for keyword in SUB_AGENT_GUIDANCE_KEYWORDS)
                for line in sub_agent_lines
            )
        )
        if not has_sub_agent_guidance and "codex-exec-sub-agent/scripts/run.sh" in lower:
            has_sub_agent_guidance = True
        standalone = all(marker in lower for marker in STANDALONE_MARKERS)
        role = role_map.get(name, "missing")
        issues: list[str] = []

        if role == "missing":
            issues.append("missing from role map")
        elif role in (ORCHESTRATOR_ROLES | META_ORCHESTRATOR_ROLES):
            if not refs:
                issues.append("no explicit cross-skill references")
            if not delegation_hits:
                issues.append("no delegation/handoff wording")
        elif role == "meta":
            if not delegation_hits and not standalone:
                issues.append("meta missing delegation signal or standalone markers")

        if name in role_map:
            if name not in layers_section:
                issues.append("missing from orchestration layers section")
            if name not in graph_section:
                issues.append("missing from delegation graph section")
            if name not in tree_section:
                issues.append("missing from delegation tree section")
        if name in edge_sync_impacted_skills:
            issues.append("delegation graph edge not mirrored in delegation tree section")
        if name == "codex-exec-sub-agent" and not meta_tool_any_skill_access:
            issues.append("topology missing explicit any-skill meta-tool access statement")
        required_targets = sorted(required_graph_targets_by_skill.get(name, set()))
        missing_targets = [target for target in required_targets if target not in text]
        for target in missing_targets:
            issues.append(
                f"delegation graph edge {name}->{target} exists but SKILL.md lacks explicit target-skill reference"
            )
            missing_graph_edge_docs.append(f"{name}->{target}")
        if name in required_sub_agent_doc_skills:
            if not has_sub_agent_ref:
                issues.append(
                    "delegation graph declares skill -> codex-exec-sub-agent but SKILL.md lacks explicit codex-exec-sub-agent reference"
                )
                missing_sub_agent_doc_skills.append(name)
            elif not has_sub_agent_guidance:
                issues.append(
                    "delegation graph declares skill -> codex-exec-sub-agent but SKILL.md lacks scenario-bound delegation wording near that reference"
                )
                weak_sub_agent_doc_skills.append(name)
        for candidate in overlap_index.get(name, []):
            peer = candidate["skills"][0] if candidate["skills"][1] == name else candidate["skills"][1]
            issues.append(
                (
                    "possible overlapping ownership with "
                    f"{peer} (similarity={candidate['similarity']}, shared={candidate['shared_token_count']}) "
                    "without explicit cross-skill delegation/reference"
                )
            )

        per_skill[name] = {
            "role": role,
            "path": str(name_to_skill[name].path),
            "references": refs,
            "delegation_keywords": delegation_hits,
            "required_graph_targets": required_targets,
            "missing_graph_targets": missing_targets,
            "requires_sub_agent_doc": name in required_sub_agent_doc_skills,
            "has_sub_agent_reference": has_sub_agent_ref,
            "has_sub_agent_guidance": has_sub_agent_guidance,
            "standalone_markers": standalone,
            "overlap_candidates": overlap_index.get(name, []),
            "status": "needs-fix" if issues else "pass",
            "issues": issues,
        }

    missing_in_role_map = sorted(set(installed_names) - set(role_map_names))
    extra_in_role_map = sorted(set(role_map_names) - set(installed_names))
    missing_in_layers = sorted(name for name in role_map_names if name not in layers_section)
    missing_in_graph = sorted(name for name in role_map_names if name not in graph_section)
    missing_in_tree = sorted(name for name in role_map_names if name not in tree_section)

    global_findings: list[str] = []
    if missing_in_role_map:
        global_findings.append(f"installed skills missing in role map: {', '.join(missing_in_role_map)}")
    if extra_in_role_map:
        global_findings.append(f"role map has non-installed skills: {', '.join(extra_in_role_map)}")
    if missing_in_layers:
        global_findings.append(f"role-map skills missing in layers: {', '.join(missing_in_layers)}")
    if missing_in_graph:
        global_findings.append(f"role-map skills missing in graph: {', '.join(missing_in_graph)}")
    if missing_in_tree:
        global_findings.append(f"role-map skills missing in tree: {', '.join(missing_in_tree)}")
    if missing_graph_edges_in_tree:
        global_findings.append(
            "delegation graph edges missing in tree: "
            + ", ".join(f"{left}->{right}" for left, right in missing_graph_edges_in_tree)
        )
    if not meta_tool_any_skill_access:
        global_findings.append(
            "topology missing explicit any-skill reusable meta-tool statement for codex-exec-sub-agent"
        )
    if missing_graph_edge_docs:
        global_findings.append(
            "delegation graph edges missing explicit source-skill documentation: "
            + ", ".join(sorted(missing_graph_edge_docs))
        )
    if missing_sub_agent_doc_skills:
        global_findings.append(
            "skills with graph-declared sub-agent edges but no codex-exec-sub-agent reference in SKILL.md: "
            + ", ".join(sorted(missing_sub_agent_doc_skills))
        )
    if weak_sub_agent_doc_skills:
        global_findings.append(
            "skills with graph-declared sub-agent edges but weak scenario guidance in SKILL.md: "
            + ", ".join(sorted(weak_sub_agent_doc_skills))
        )
    if overlap_candidates:
        global_findings.append(
            (
                "responsibility-overlap candidates without explicit cross-skill delegation/reference: "
                + ", ".join(f"{row['skills'][0]}<->{row['skills'][1]}" for row in overlap_candidates)
            )
        )

    needs_fix = sorted(name for name, row in per_skill.items() if row["status"] == "needs-fix")
    return {
        "scanned_count": len(installed_names),
        "scanned_skill_names": installed_names,
        "global_findings": global_findings,
        "topology_drift": {
            "missing_in_role_map": missing_in_role_map,
            "extra_in_role_map": extra_in_role_map,
            "missing_in_layers": missing_in_layers,
            "missing_in_graph": missing_in_graph,
            "missing_in_tree": missing_in_tree,
            "missing_graph_edges_in_tree": [
                f"{left}->{right}" for left, right in missing_graph_edges_in_tree
            ],
        },
        "meta_tool_any_skill_access": meta_tool_any_skill_access,
        "required_graph_doc_edges": [f"{source}->{target}" for source, target in sorted(required_graph_doc_edges)],
        "missing_graph_edge_docs": sorted(missing_graph_edge_docs),
        "sub_agent_graph_requirements": sorted(required_sub_agent_doc_skills),
        "sub_agent_doc_missing": sorted(missing_sub_agent_doc_skills),
        "sub_agent_doc_weak": sorted(weak_sub_agent_doc_skills),
        "responsibility_overlap_candidates": overlap_candidates,
        "needs_fix_count": len(needs_fix),
        "needs_fix_skills": needs_fix,
        "per_skill": per_skill,
    }


def print_human(result: dict) -> None:
    print(f"SCANNED={result['scanned_count']}")
    print(f"NEEDS_FIX_COUNT={result['needs_fix_count']}")
    if result["global_findings"]:
        print("GLOBAL_FINDINGS")
        for finding in result["global_findings"]:
            print(f"- {finding}")
    if result["responsibility_overlap_candidates"]:
        print("RESPONSIBILITY_OVERLAP")
        for row in result["responsibility_overlap_candidates"]:
            left, right = row["skills"]
            print(
                (
                    f"- {left}<->{right}\t"
                    f"similarity={row['similarity']}\t"
                    f"shared={row['shared_token_count']}\t"
                    f"tokens={','.join(row['shared_tokens_preview'])}"
                )
            )
    print("PER_SKILL")
    for name in result["scanned_skill_names"]:
        row = result["per_skill"][name]
        if row["issues"]:
            reason = "; ".join(row["issues"])
        else:
            reason = (
                f"refs={len(row['references'])}, "
                f"delegation={len(row['delegation_keywords'])}, "
                f"standalone={row['standalone_markers']}"
            )
        print(f"{name}\t{row['role']}\t{row['status']}\t{reason}")


def main() -> int:
    args = parse_args()
    skills = load_skills(args.skills_root)
    if not skills:
        print("No SKILL.md files found.", file=sys.stderr)
        return 2

    topology_text = args.topology.read_text(encoding="utf-8")
    role_map = parse_role_map(topology_text)
    result = audit(skills=skills, role_map=role_map, topology_text=topology_text)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)

    return 1 if result["needs_fix_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
