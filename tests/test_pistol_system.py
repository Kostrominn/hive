import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from pistol_system import PistolSystem


def test_parse_pistol_request():
    ps = PistolSystem()
    ps.available_pistols = 1
    assert ps.parse_pistol_request("Alice", "я Хочу пистолет")
    assert "Alice" in ps.pistol_requests


def test_resolve_duel():
    ps = PistolSystem()
    ps.pistol_owners.update({"Alice", "Bob"})
    msg = ps.resolve_duel({"challenger": "Alice", "target": "Bob"})
    assert "убили" in msg
    assert "Alice" in ps.dead_players
    assert "Bob" in ps.dead_players
