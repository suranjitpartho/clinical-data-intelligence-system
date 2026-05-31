import os
import sys

ENV_FILE = "/app/env/.env"


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, flush=True, **kwargs)


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
            f.write(f"{k}={v}\n")


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
            val = input(f"Paste your {var_name}{suffix}: ").strip()
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
        val = input(f"Paste your {var_name} (or press Enter to skip): ").strip()
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
    exports = []

    for k, v in existing.items():
        if v and k not in os.environ:
            exports.append(f"export {k}='{v}'")

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
    if val != existing.get("GROQ_API_KEY"):
        save_env(existing, "GROQ_API_KEY", val)
    os.environ["GROQ_API_KEY"] = val
    exports.append(f"export GROQ_API_KEY='{val}'")

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
    if val != existing.get("GITHUB_CLIENT_ID"):
        save_env(existing, "GITHUB_CLIENT_ID", val)
    os.environ["GITHUB_CLIENT_ID"] = val
    exports.append(f"export GITHUB_CLIENT_ID='{val}'")

    # ── GITHUB_CLIENT_SECRET ──
    val = prompt_required(
        "GITHUB_CLIENT_SECRET",
        "Generate a Client Secret for the same OAuth app:\n"
        "  1. On the same page, click 'Generate a new client secret'\n"
        "  2. Copy the secret key shown"
    )
    if val != existing.get("GITHUB_CLIENT_SECRET"):
        save_env(existing, "GITHUB_CLIENT_SECRET", val)
    os.environ["GITHUB_CLIENT_SECRET"] = val
    exports.append(f"export GITHUB_CLIENT_SECRET='{val}'")

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
        if secret != existing.get("LANGFUSE_SECRET_KEY"):
            save_env(existing, "LANGFUSE_SECRET_KEY", secret)
        os.environ["LANGFUSE_SECRET_KEY"] = secret
        exports.append(f"export LANGFUSE_SECRET_KEY='{secret}'")

        public = prompt_required(
            "LANGFUSE_PUBLIC_KEY",
            "Copy the Public Key from the same Langfuse page."
        )
        if public != existing.get("LANGFUSE_PUBLIC_KEY"):
            save_env(existing, "LANGFUSE_PUBLIC_KEY", public)
        os.environ["LANGFUSE_PUBLIC_KEY"] = public
        exports.append(f"export LANGFUSE_PUBLIC_KEY='{public}'")

    # ── JWT_SECRET (auto-generate) ──
    if not os.environ.get("JWT_SECRET"):
        import secrets
        jwt = secrets.token_urlsafe(32)
        if jwt != existing.get("JWT_SECRET"):
            save_env(existing, "JWT_SECRET", jwt)
        os.environ["JWT_SECRET"] = jwt
        exports.append(f"export JWT_SECRET='{jwt}'")
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
        val = os.environ.get(key) or default
        if val != existing.get(key):
            save_env(existing, key, val)
        os.environ[key] = val
        exports.append(f"export {key}='{val}'")

    eprint("")
    eprint("=" * 50)
    eprint("  Setup complete! Starting server...")
    eprint("=" * 50)
    eprint("")

    # Only exports go to stdout for the shell to eval
    print("\n".join(exports))


if __name__ == "__main__":
    main()
