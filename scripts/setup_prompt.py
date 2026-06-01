import os
import sys

ENV_FILE = "/app/env/.env"


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, flush=True, **kwargs)


def uinput(prompt=""):
    """Write prompt to stderr so it's visible, not captured by $()."""
    if prompt:
        sys.stderr.write(prompt)
        sys.stderr.flush()
    return input()


def load_env():
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k] = v
    return env


def save_env(existing, key, value):
    existing[key] = value
    with open(ENV_FILE, "w") as f:
        for k, v in existing.items():
            f.write(f"export {k}={v}\n")


def prompt_required(var_name, instructions, hint=""):
    existing = os.environ.get(var_name, "") or ""
    if existing.strip():
        return existing.strip()
    eprint("")
    eprint("=" * 40)
    eprint(f"STEP: {var_name} (required)")
    eprint("=" * 40)
    eprint(instructions)
    eprint("")
    suffix = f" ({hint})" if hint else ""
    while True:
        try:
            val = uinput(f"Paste your {var_name}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            eprint("\nSetup cancelled.")
            sys.exit(1)
        if val:
            return val
        eprint(f"{var_name} is required.")


def prompt_optional(var_name, instructions):
    existing = os.environ.get(var_name, "") or ""
    if existing.strip():
        return existing.strip()
    eprint("")
    eprint("=" * 40)
    eprint(f"STEP: {var_name} (optional)")
    eprint("=" * 40)
    eprint(instructions)
    eprint("")
    try:
        val = uinput(f"Paste your {var_name} (or press Enter to skip): ").strip()
    except (EOFError, KeyboardInterrupt):
        val = ""
    return val


def main():
    eprint("")
    eprint("=" * 50)
    eprint("  Clinical Data Intelligence — Setup")
    eprint("=" * 50)
    eprint("")

    existing = load_env()

    # ── GROQ_API_KEY ──
    val = prompt_required(
        "GROQ_API_KEY",
        "We need an API key from Groq to run the AI models.\n"
        "Getting one is free and takes 2 minutes:\n"
        "  1. Go to https://console.groq.com\n"
        "  2. Sign up for a free account\n"
        "  3. Go to API Keys section\n"
        "  4. Click 'Create API Key'\n"
        "  5. Copy the key (it starts with 'gsk_')",
        hint="gsk_..."
    )
    save_env(existing, "GROQ_API_KEY", val)

    # ── GITHUB_CLIENT_ID ──
    val = prompt_required(
        "GITHUB_CLIENT_ID",
        "You need a GitHub OAuth app so you can log in.\n"
        "Create one (it takes 3 minutes):\n"
        "  1. Go to https://github.com/settings/developers\n"
        "  2. Click 'New OAuth App'\n"
        "  3. Application name: Clinical AI (or anything)\n"
        "  4. Homepage URL: http://localhost:8000\n"
        "  5. Callback URL: http://localhost:8000/api/auth/github/callback\n"
        "  6. Click 'Register application'\n"
        "  7. Copy the Client ID from the next page"
    )
    save_env(existing, "GITHUB_CLIENT_ID", val)

    # ── GITHUB_CLIENT_SECRET ──
    val = prompt_required(
        "GITHUB_CLIENT_SECRET",
        "Generate a Client Secret for the same OAuth app:\n"
        "  1. On the same page, click 'Generate a new client secret'\n"
        "  2. Copy the secret key shown"
    )
    save_env(existing, "GITHUB_CLIENT_SECRET", val)

    # ── LANGFUSE (optional) ──
    secret = prompt_optional(
        "LANGFUSE_SECRET_KEY",
        "Langfuse tracks AI queries for the Analytics dashboard.\n"
        "You can skip this if you don't need analytics.\n\n"
        "  To get keys (if you want):\n"
        "    1. Go to https://cloud.langfuse.com\n"
        "    2. Sign up (free tier)\n"
        "    3. Create a project\n"
        "    4. Go to Project Settings -> API Keys"
    )
    if secret:
        save_env(existing, "LANGFUSE_SECRET_KEY", secret)
        public = prompt_required(
            "LANGFUSE_PUBLIC_KEY",
            "Copy the Public Key from the same Langfuse page."
        )
        save_env(existing, "LANGFUSE_PUBLIC_KEY", public)

    # ── JWT_SECRET (auto-generate) ──
    if not existing.get("JWT_SECRET"):
        import secrets
        jwt = secrets.token_urlsafe(32)
        save_env(existing, "JWT_SECRET", jwt)
        eprint("  JWT_SECRET auto-generated.")

    # ── Defaults ──
    for key, default in [
        ("ENV", "local"),
        ("DEBUG", "true"),
        ("FRONTEND_URL", "http://localhost:8000"),
        ("AI_PROVIDER", "groq"),
        ("AI_MODEL", "llama-3.3-70b-versatile"),
        ("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    ]:
        val = existing.get(key) or default
        save_env(existing, key, val)

    eprint("")
    eprint("=" * 50)
    eprint("  Setup complete! Starting server...")
    eprint("=" * 50)
    eprint("")


if __name__ == "__main__":
    main()
