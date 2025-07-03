import re
import random
from typing import Dict, List, Optional, Set


class PistolSystem:
    """Manage pistol ownership and duels."""

    def __init__(self) -> None:
        self.pistol_owners: Set[str] = set()
        self.dead_players: Set[str] = set()
        self.duel_history: List[Dict[str, str]] = []
        self.available_pistols: int = 0
        self.pistol_requests: Dict[str, Dict[str, float]] = {}
        self.current_president: Optional[str] = None

    def spawn_pistols(self, round_num: int) -> str:
        """Spawn a random number of pistols for this round."""
        self.available_pistols = random.randint(1, 3)
        self.pistol_requests = {}
        return (
            f"\U0001f52b \u0412 \u0433\u043e\u0440\u043e\u0434\u0435 \u043f\u043e\u044f\u0432\u0438\u043b\u043e\u0441\u044c {self.available_pistols} \u043f\u0438\u0441\u0442\u043e\u043b\u0435\u0442(\u043e\u0432)!"
        )

    def parse_pistol_request(self, name: str, text: str) -> bool:
        """Detect a pistol request in the text."""
        if self.available_pistols <= 0:
            return False
        if re.search(r"хочу\s+пистолет", text, re.IGNORECASE):
            self.pistol_requests[name] = {
                "intensity": random.random(),
                "reason": "request",
            }
            return True
        return False

    def parse_duel_challenge(self, name: str, text: str) -> Optional[Dict[str, str]]:
        """Return challenger/target if a duel is requested."""
        m = re.search(r"вызываю\s+на\s+дуэль\s+([\w\s-]+)", text, re.IGNORECASE)
        if m:
            target = m.group(1).strip()
            if target and target != name:
                return {"challenger": name, "target": target}
        return None

    def distribute_pistols(self) -> Optional[str]:
        if not self.pistol_requests:
            return None
        sorted_requests = sorted(
            self.pistol_requests.items(),
            key=lambda kv: kv[1]["intensity"],
            reverse=True,
        )
        winners = []
        for person, data in sorted_requests[: self.available_pistols]:
            self.pistol_owners.add(person)
            winners.append(f"{person} ({data.get('reason', '')})")
        self.available_pistols = max(self.available_pistols - len(winners), 0)
        if winners:
            return (
                f"\U0001f3af \u041f\u0438\u0441\u0442\u043e\u043b\u0435\u0442\u044b \u043f\u043e\u043b\u0443\u0447\u0438\u043b\u0438: {', '.join(winners)}"
            )
        return None

    def resolve_duel(self, duel: Dict[str, str]) -> str:
        challenger = duel["challenger"]
        target = duel["target"]
        if challenger in self.dead_players or target in self.dead_players:
            return ""
        challenger_armed = challenger in self.pistol_owners
        target_armed = target in self.pistol_owners
        if challenger_armed and target_armed:
            self.dead_players.update({challenger, target})
            self.pistol_owners.discard(challenger)
            self.pistol_owners.discard(target)
            msg = f"\u2694\ufe0f {challenger} \u0438 {target} \u0443\u0431\u0438\u043b\u0438 \u0434\u0440\u0443\u0433 \u0434\u0440\u0443\u0433\u0430!"
        elif challenger_armed and not target_armed:
            self.dead_players.add(target)
            msg = f"\u2694\ufe0f {challenger} \u0437\u0430\u0441\u0442\u0440\u0435\u043b\u0438\u043b {target}!"
        elif not challenger_armed and target_armed:
            self.dead_players.add(challenger)
            msg = f"\u2694\ufe0f {target} \u0437\u0430\u0441\u0442\u0440\u0435\u043b\u0438\u043b {challenger} \u0432 \u0441\u0430\u043c\u043e\u043e\u0431\u043e\u0440\u043e\u043d\u0435!"
        else:
            msg = f"\ud83d\udc4a {challenger} \u0438 {target} \u043f\u043e\u0434\u0440\u0430\u043b\u0438\u0441\u044c, \u043d\u043e \u043d\u0438\u043a\u0442\u043e \u043d\u0435 \u0443\u043c\u0435\u0440."
        self.duel_history.append({"challenger": challenger, "target": target, "message": msg})
        return msg

    def handle_presidency(self, new_president: str) -> str:
        self.current_president = new_president
        if new_president in self.pistol_owners:
            self.pistol_owners.remove(new_president)
            return f"\U0001f3dc\ufe0f {new_president} \u0441\u0442\u0430\u043b \u043f\u0440\u0435\u0437\u0438\u0434\u0435\u043d\u0442\u043e\u043c \u0438 \u043e\u0442\u0434\u0430\u043b \u043f\u0438\u0441\u0442\u043e\u043b\u0435\u0442!"
        return f"\U0001f3dc\ufe0f {new_president} \u0441\u0442\u0430\u043b \u043f\u0440\u0435\u0437\u0438\u0434\u0435\u043d\u0442\u043e\u043c."

    def get_status_for_prompt(self) -> str:
        owners = ", ".join(self.pistol_owners) if self.pistol_owners else "никто"
        dead = ", ".join(self.dead_players) if self.dead_players else "никого"
        prez = self.current_president or "нет"
        status = (
            "\n\U0001f52b \u041f\u0438\u0441\u0442\u043e\u043b\u0435\u0442\u044b:\n"
            f"- \u0412\u043e\u043e\u0440\u0443\u0436\u0435\u043d\u044b: {owners}\n"
            f"- \u041c\u0435\u0440\u0442\u0432\u044b\u0435: {dead}\n"
            f"- \u041f\u0440\u0435\u0437\u0438\u0434\u0435\u043d\u0442: {prez}\n"
            f"- \u0414\u043e\u0441\u0442\u0443\u043f\u043d\u043e \u043f\u0438\u0441\u0442\u043e\u043b\u0435\u0442\u043e\u0432: {self.available_pistols}\n"
        )
        if self.duel_history:
            status += "\n\U0001f5de\ufe0f \u041d\u0435\u0434\u0430\u0432\u043d\u0438\u0435 \u0434\u0443\u044d\u043b\u0438:\n"
            for event in self.duel_history[-3:]:
                status += f"- {event['message']}\n"
        return status
