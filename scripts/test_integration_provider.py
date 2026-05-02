#!/usr/bin/env python3
import os


def main() -> None:
    provider = os.environ.get("AI_PROVIDER", "opencode")
    op_key = os.environ.get("OPENCODE_API_KEY")
    op_base = os.environ.get("OPENCODE_BASE_URL")

    opencode_configured = (
        provider == "opencode" and bool(op_key) and bool(op_base)
    )

    print(f"AI_PROVIDER: {provider}")
    print(f"OPENCODE_API_KEY present: {bool(op_key)}")
    print(f"OPENCODE_BASE_URL present: {bool(op_base)}")
    print(f"Opencode configured: {'YES' if opencode_configured else 'NO'}")

    if provider != "opencode":
        print("Note: current run is configured to use a non-Opencode provider.")


if __name__ == "__main__":
    main()
