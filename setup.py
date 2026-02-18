#!/usr/bin/env python3
"""
hybrid-rag — Interactive Setup Wizard
======================================
Guides the user through:
  1. Installing Python dependencies
  2. Optionally installing ragas
  3. Configuring .env (LLM, embeddings, Supabase, etc.)
  4. Initializing Supabase tables & functions
"""

import os
import sys
import subprocess
import shutil
import getpass
import textwrap
from settings import load_settings, Settings

# ── Colour helpers (ANSI 256) ────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"

# ── Pretty-print helpers ─────────────────────────────────────────────────────

BANNER = rf"""
{RESET}{DIM}{CYAN}{BOLD}  Interactive Setup Wizard{RESET}
"""

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def header(title: str) -> None:
    width = 60
    print(f"\n{CYAN}{BOLD}{'─' * width}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{BOLD}{'─' * width}{RESET}\n")


def success(msg: str) -> None:
    print(f"  {GREEN}✔{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}⚠{RESET} {msg}")


def error(msg: str) -> None:
    print(f"  {RED}✖{RESET} {msg}")


def info(msg: str) -> None:
    print(f"  {BLUE}ℹ{RESET} {msg}")


def ask(prompt: str, default: str = "", secret: bool = False) -> str:
    """Prompt the user for input. Shows [default] if provided."""
    suffix = f" [{DIM}{default}{RESET}]" if default else ""
    full_prompt = f"  {MAGENTA}▸{RESET} {prompt}{suffix}: "
    if secret:
        value = getpass.getpass(full_prompt)
    else:
        value = input(full_prompt)
    return value.strip() or default


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    reply = ask(f"{prompt} [{hint}]").lower()
    if not reply:
        return default
    return reply in ("y", "yes")


def ask_choice(prompt: str, options: list[str], default_index: int = 0) -> str:
    """Show a numbered list and return the selected option."""
    print(f"\n  {MAGENTA}▸{RESET} {prompt}")
    for i, opt in enumerate(options):
        marker = f"{GREEN}▸{RESET}" if i == default_index else " "
        print(f"    {marker} {i + 1}) {opt}")
    raw = ask("Elige una opción", str(default_index + 1))
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except ValueError:
        pass
    return options[default_index]


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Install dependencies
# ═══════════════════════════════════════════════════════════════════════════════

def step_install_dependencies() -> bool:
    header("Step 1 · Install dependencies")
    info("Installing packages from requirements.txt …")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=PROJECT_DIR,
    )
    if result.returncode == 0:
        success("Dependencies installed correctly.")
        return True
    else:
        error("There were errors installing dependencies.")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Optional ragas
# ═══════════════════════════════════════════════════════════════════════════════

def step_install_ragas() -> None:
    header("Step 2 · Ragas (RAG evaluation)")
    info("Ragas allows you to evaluate the quality of the RAG system.")
    if ask_yes_no("Do you want to install ragas?", default=False):
        info("Installing ragas …")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "ragas"],
        )
        if result.returncode != 0:
            warn("Could not install rag_eval in editable mode. You can install it later with: pip install -e .")
            return
        success("ragas installed correctly.")
        info("Running ragas quickstart rag_eval")
        ragas_path = os.path.join(os.path.dirname(sys.executable), "ragas")
        result = subprocess.run(
            [ragas_path, "quickstart", "rag_eval"],
        )
        if result.returncode != 0:
            warn("Could not run ragas quickstart rag_eval. You can run it later with: ragas quickstart rag_eval")
            return

        success("ragas quickstart rag_eval completed successfully.")
        info("Installing Ragas dependencies ...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            cwd=os.path.join(PROJECT_DIR, "rag_eval"),
        )
        if result.returncode == 0:
            success("Ragas dependencies installed correctly.")
        else:
            warn("Ragas dependencies could not be installed. You can install them later with: pip install -e .")
            return
    else:
        info("Skipping ragas installation.")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Configuration wizard → .env
# ═══════════════════════════════════════════════════════════════════════════════

# Available embedding models (mirrors settings.py)
EMBEDDING_MODELS = {
    "snowflake-arctic-embed2": {"dimensions": 1024, "max_tokens": 8191},
    "nomic-embed-text-v2-moe": {"dimensions": 768, "max_tokens": 512},
}


def step_configure_env() -> dict[str, str]:
    header("Step 3 · Environment configuration (.env)")
    settings = load_settings()

    env: dict[str, str] = {}

    # ── Supabase ──────────────────────────────────────────────────────────
    print(f"\n  {BOLD}Supabase{RESET}")
    env["SUPABASE_URL"] = ask("URL of Supabase (e.g: https://xxxx.supabase.co)")
    env["SUPABASE_KEY"] = ask("Service-role key of Supabase", secret=True)

    # ── LLM ───────────────────────────────────────────────────────────────
    print(f"\n  {BOLD}LLM (Language model){RESET}")
    llm_local = ask_yes_no("¿Use a local LLM (Ollama)? Make sure to have ollama running", default=False)
    env["LLM_LOCAL"] = str(llm_local)

    if llm_local:
        env["LLM_MODEL"] = ask("Local LLM model")
        env["LLM_BASE_URL"] = ask("Base URL of Ollama", settings.llm_base_url)
        env["LLM_API_KEY"] = ""
    else:
        env["LLM_MODEL"] = ask("Model name", settings.llm_model)
        env["LLM_API_KEY"] = ask("API Key", secret=True)
        env["LLM_BASE_URL"] = ask("Base URL of provider if needed", "")

    # ── Embeddings ────────────────────────────────────────────────────────
    print(f"\n  {BOLD}Embeddings{RESET}")

    embed_local = ask_yes_no("¿Use a local LLM (Ollama)? Make sure to have ollama running", default=False)
    env["EMBEDDING_LOCAL"] = str(embed_local)
    if embed_local:
        env["EMBEDDING_BASE_URL"] = ask("Base URL of Ollama for embeddings", settings.embedding_base_url)
        env["EMBEDDING_API_KEY"] = ""
        
        model_names = list(settings.embedding_models.keys())
        chosen_model = ask_choice("Modelo de embeddings", model_names, default_index=0)
        model_info = settings.embedding_models[chosen_model]
        env["EMBEDDING_MODEL"] = chosen_model
        env["EMBEDDING_DIMENSIONS"] = str(model_info['dimensions'])
        info(f"Dimensiones: {model_info['dimensions']}  |  Max tokens: {model_info['max_tokens']}")
    else:
        env["EMBEDDING_BASE_URL"] = ask("Base URL of embeddings provider", "")
        env["EMBEDDING_API_KEY"] = ask("API Key de embeddings", secret=True)

    # ── Search defaults ───────────────────────────────────────────────────
    print(f"\n  {BOLD}Search defaults{RESET}")
    env["DEFAULT_MATCH_COUNT"] = ask("Results per search (default)", settings.default_match_count)
    env["MAX_MATCH_COUNT"] = ask("Maximum results", settings.max_match_count)

    # ── Reranking ─────────────────────────────────────────────────────────
    print(f"\n  {BOLD}Reranking{RESET}")
    rerank = ask_yes_no("Enable reranking?", default=False)
    env["RERANK_ENABLED"] = str(rerank)
    if rerank:
        env["RERANK_MODEL"] = ask("Reranking model", settings.rerank_model)
        env["RERANK_TOP_K"] = ask("Top-K after reranking", settings.rerank_top_k)

    # ── Google Drive ──────────────────────────────────────────────────────
    print(f"\n  {BOLD}Google Drive (optional){RESET}")
    if ask_yes_no("Configure ingestion from Google Drive?", default=False):
        env["GDRIVE_CREDENTIALS_FILE"] = ask("Path to credentials file", "credentials.json")
        env["GDRIVE_FOLDER_ID"] = ask("Google Drive folder ID")

    # ── Tracing ───────────────────────────────────────────────────────────
    print(f"\n  {BOLD}Tracing / Observability (optional){RESET}")
    if ask_yes_no("¿Configure tracing (e.g: OpenAI Tracing, Langsmith, etc.)?", default=False):
        env["TRACING_API_KEY"] = ask("Tracing API Key", secret=True)

    # ── Write .env ────────────────────────────────────────────────────────
    _write_env_file(env)
    return env


def _write_env_file(env: dict[str, str]) -> None:
    """Write the .env file, backing up any existing one."""
    project_dir = os.path.dirname(os.path.abspath(__file__)) or "."
    env_path = os.path.join(project_dir, ".env")

    if os.path.exists(env_path):
        backup = env_path + ".backup"
        shutil.copy2(env_path, backup)
        warn(f"Backup created: {backup}")

    lines: list[str] = []
    # Group variables with comments for readability
    groups = [
        ("# ── Supabase", ["SUPABASE_URL", "SUPABASE_KEY"]),
        ("# ── LLM", ["LLM_LOCAL", "LLM_MODEL", "LLM_API_KEY", "LLM_BASE_URL"]),
        ("# ── Embeddings", ["EMBEDDING_MODEL", "EMBEDDING_DIMENSIONS", "EMBEDDING_BASE_URL", "EMBEDDING_API_KEY"]),
        ("# ── Search", ["DEFAULT_MATCH_COUNT", "MAX_MATCH_COUNT"]),
        ("# ── Reranking", ["RERANK_ENABLED", "RERANK_MODEL", "RERANK_TOP_K"]),
        ("# ── Google Drive", ["GDRIVE_CREDENTIALS_FILE", "GDRIVE_FOLDER_ID"]),
        ("# ── Tracing", ["TRACING_API_KEY"]),
    ]

    for comment, keys in groups:
        group_lines = []
        for k in keys:
            if k in env:
                group_lines.append(f"{k}={env[k]}")
        if group_lines:
            lines.append(comment)
            lines.extend(group_lines)
            lines.append("")

    with open(env_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    success(f".env generated at {env_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Initialize Supabase tables
# ═══════════════════════════════════════════════════════════════════════════════

def _get_embedding_dimensions(env: dict[str, str]) -> int:
    """Return the embedding dimensions from the env config."""
    return int(env.get("EMBEDDING_DIMENSIONS", "1024"))


def _build_init_sql(dimensions: int) -> str:
    """Return the full SQL script to initialise Supabase tables & functions."""
    return textwrap.dedent(f"""\
        -- Enable pgvector extension
        CREATE EXTENSION IF NOT EXISTS vector
          WITH SCHEMA extensions;

        -- Documents table
        CREATE TABLE IF NOT EXISTS documents (
          id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          title       text NOT NULL,
          source      text,
          content     text,
          metadata    jsonb DEFAULT '{{}}'::jsonb,
          created_at  timestamptz DEFAULT now()
        );

        -- Document chunks table (with FTS generated column)
        CREATE TABLE IF NOT EXISTS document_chunks (
          id            bigserial PRIMARY KEY,
          document_id   uuid REFERENCES documents(id) ON DELETE CASCADE,
          content       text NOT NULL,
          embedding     vector({dimensions}),
          chunk_index   int,
          metadata      jsonb DEFAULT '{{}}'::jsonb,
          token_count   int,
          created_at    timestamptz DEFAULT now(),
          fts           tsvector GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED
        );

        -- HNSW index for semantic search (cosine distance)
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding
          ON document_chunks
          USING hnsw (embedding vector_cosine_ops)
          WITH (m = 16, ef_construction = 64);

        -- Hybrid search RPC (semantic + full-text + RRF)
        CREATE OR REPLACE FUNCTION hybrid_search(
          query_text text,
          query_embedding vector({dimensions}),
          match_count int DEFAULT 10,
          full_text_weight float DEFAULT 1.0,
          semantic_weight float DEFAULT 1.0,
          rrf_k int DEFAULT 60
        )
        RETURNS TABLE (
          chunk_id bigint,
          document_id uuid,
          content text,
          similarity float,
          metadata jsonb,
          document_title text,
          document_source text
        )
        LANGUAGE sql STABLE
        AS $$
        WITH full_text AS (
          SELECT
            dc.id,
            row_number() OVER (
              ORDER BY ts_rank(dc.fts, websearch_to_tsquery(query_text)) DESC
            ) AS rank_ix
          FROM document_chunks dc
          WHERE dc.fts @@ websearch_to_tsquery(query_text)
          ORDER BY rank_ix
          LIMIT least(match_count, 30) * 2
        ),
        semantic AS (
          SELECT
            dc.id,
            row_number() OVER (
              ORDER BY dc.embedding <=> query_embedding
            ) AS rank_ix
          FROM document_chunks dc
          ORDER BY rank_ix
          LIMIT least(match_count, 30) * 2
        )
        SELECT
          dc.id AS chunk_id,
          dc.document_id,
          dc.content,
          (
            coalesce(1.0 / (rrf_k + full_text.rank_ix), 0.0) * full_text_weight +
            coalesce(1.0 / (rrf_k + semantic.rank_ix), 0.0) * semantic_weight
          ) AS similarity,
          dc.metadata,
          d.title AS document_title,
          d.source AS document_source
        FROM
          full_text
          FULL OUTER JOIN semantic ON full_text.id = semantic.id
          JOIN document_chunks dc ON coalesce(full_text.id, semantic.id) = dc.id
          JOIN documents d ON dc.document_id = d.id
        ORDER BY similarity DESC
        LIMIT least(match_count, 30);
        $$;

        -- Agent session tables (conversation persistence)
        CREATE TABLE IF NOT EXISTS agent_sessions (
          session_id TEXT PRIMARY KEY,
          created_at TIMESTAMPTZ DEFAULT now(),
          updated_at TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS agent_messages (
          id BIGSERIAL PRIMARY KEY,
          session_id TEXT NOT NULL REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
          message_data JSONB NOT NULL,
          created_at TIMESTAMPTZ DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_agent_messages_session_id
          ON agent_messages(session_id, id);
    """)


def step_init_supabase(env: dict[str, str]) -> None:
    header("Step 4 · Initialize tables in Supabase")

    url = env.get("SUPABASE_URL", "")
    key = env.get("SUPABASE_KEY", "")

    if not url or not key:
        error("No found SUPABASE_URL and SUPABASE_KEY. Omitting initialization.")
        return

    dimensions = _get_embedding_dimensions(env)
    sql = _build_init_sql(dimensions)

    info(f"Using embedding dimensions: {dimensions}")
    info("Connecting to Supabase and running initialization SQL …")

    try:
        from supabase import create_client
        client = create_client(url, key)

        # Split SQL into individual statements and execute each
        statements = [s.strip() for s in sql.split(";") if s.strip()]

        sql_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)) or ".", "init_supabase.sql"
        )
        with open(sql_file, "w") as f:
            f.write(sql + "\n")

        warn("Could not execute SQL directly against Supabase.")
        info(f"Generated file: {BOLD}init_supabase.sql{RESET}")
        info("Copy and paste its content into the Supabase SQL Editor:")
        info(f"  {DIM}https://supabase.com/dashboard → SQL Editor → New Query{RESET}")
        print()

    except ImportError:
        error("The 'supabase' package is not installed or API and URL are not configured properly.")

    success("SQL initialization file generated successfully.")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print(BANNER)

    try:
        ok = step_install_dependencies()
        if not ok:
            print(f"\n{DIM}Setup canceled.{RESET}")
            sys.exit(1)

        step_install_ragas()

        env = step_configure_env()

        step_init_supabase(env)

        success("The .env file has been configured.")
        header("Setup completed!")
        print()

    except KeyboardInterrupt:
        print(f"\n\n{DIM}Setup canceled by user.{RESET}\n")
        sys.exit(130)


if __name__ == "__main__":
    main()
