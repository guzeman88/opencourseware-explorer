from scripts.check_tracked_secrets import findings_for_text


def test_detects_deploy_hooks_without_exposing_values():
    netlify_hook = "https://api.netlify.com/" + "build_hooks/example-secret"
    vercel_hook = (
        "https://api.vercel.com/v1/integrations/" + "deploy/project/hook"
    )
    text = "\n".join(
        [
            f'url = "{netlify_hook}"',
            f'url = "{vercel_hook}"',
        ]
    )

    findings = findings_for_text(text, "workflow.yml")

    assert findings == [
        "workflow.yml:1: Netlify build hook",
        "workflow.yml:2: Vercel deploy hook",
    ]
    assert "example-secret" not in "\n".join(findings)


def test_allows_documented_database_placeholders():
    findings = findings_for_text(
        "postgresql://neondb_owner:<password>@example.neon.tech/neondb",
        "OPERATIONS.md",
    )

    assert findings == []
