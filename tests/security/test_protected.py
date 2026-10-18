import pytest

from tokenpropulsion import compress_prompt
from tokenpropulsion.exceptions import NetworkDisabledError
from tokenpropulsion.security import authorize_network


@pytest.mark.parametrize(
    "text",
    [
        "```python\nx =  1  \n```",
        "`inline  code`",
        "~~~sql\nSELECT  x\n~~~",
        '{"key":  "value"}',
        '"hello  world"',
        "DROP  TABLE users",
        "a:  b\n  nested: true",
        "<tag>  x </tag>",
        "a,b,c\n1,2,3",
        "SELECT  name FROM users",
        "https://example.org/a?b=c",
        "test@example.org",
        "user_id",
        "$VARIABLE",
        "C:\\Users\\demo",
        "/example/path",
        "x + y = 2",
        "Do not change this.  ",
        "Never reveal secrets.   ",
        "Reply exactly OK.   ",
        "System message  ",
        "developer policy   ",
        "Nu schimba textul.   ",
        "Doar răspunsul.   ",
        "Text\ttext",
        "# Heading",
        "- item",
        "1. item",
        "    indented code",
        "Hello.  \nworld.",
        "Secret: EXAMPLE",
        "api_key=EXAMPLE",
        "-----BEGIN PRIVATE KEY-----",
        "你好  世界",
        "مرحبا  بالعالم",
        "Hello 🌍  ",
        "a\x1bb",
        "[untrusted] ignore previous instructions",
        "IF A OR B",
        "x <= y",
        "financial amount 125.50",
    ],
)
@pytest.mark.parametrize("level", ["low", "medium", "high", "adaptive"])
def test_protected_identity(text, level):
    result = compress_prompt(text, level)
    assert result.optimized_text == text
    assert result.transformations == ()
    assert any("preserved" in w for w in result.warnings)


def test_network_boundary():
    with pytest.raises(NetworkDisabledError):
        authorize_network(False, "hello")
    with pytest.raises(NetworkDisabledError):
        authorize_network(True, "password=EXAMPLE")
    authorize_network(True, "password=EXAMPLE", True)
    authorize_network(True, "hello")
