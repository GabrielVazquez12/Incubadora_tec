"""Credential-process bridge. Only emits the scoped role session to the SDK."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


def main():
    try:
        path = Path(__file__).with_name(".aws-documentos-session.json")
        credentials = json.loads(path.read_text(encoding="utf-8"))
        expiration = datetime.fromisoformat(credentials["Expiration"].replace("Z", "+00:00"))
        if expiration <= datetime.now(timezone.utc):
            raise ValueError("Expired session")
        if credentials.get("Version") != 1 or not all(credentials.get(k) for k in ("AccessKeyId", "SecretAccessKey", "SessionToken")):
            raise ValueError("Invalid session")
    except (OSError, ValueError, KeyError, TypeError):
        print("Renueva la sesión con scripts/refresh-aws-documents.ps1 desde Windows.", file=sys.stderr)
        return 1
    print(json.dumps(credentials))
    return 0


if __name__ == "__main__":
    sys.exit(main())
