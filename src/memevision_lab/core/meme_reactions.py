from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MemeReaction:
    id: str
    name: str
    triggers: tuple[str, ...]
    asset: str
    sound: str
    input_type: str
    cooldown_seconds: float
    category: str


@dataclass(frozen=True)
class ActiveMemeReaction:
    meme: MemeReaction
    started_at: float
    expires_at: float

    @property
    def name(self) -> str:
        return self.meme.name


class MemeReactionEngine:
    def __init__(
        self,
        memes: list[MemeReaction],
        display_seconds: float = 0.95,
        active_input_type: str = "hand",
        allowed_meme_ids: set[str] | None = None,
        min_cooldown_seconds: float = 0.8,
    ) -> None:
        self.memes = memes
        self.display_seconds = display_seconds
        self.active_input_type = active_input_type
        self.allowed_meme_ids = allowed_meme_ids
        self.min_cooldown_seconds = min_cooldown_seconds
        self.last_triggered_at: dict[str, float] = {}
        self.active: ActiveMemeReaction | None = None
        self.active_many: list[ActiveMemeReaction] = []

    @classmethod
    def from_config(cls, config_path: Path) -> MemeReactionEngine:
        if not config_path.exists():
            return cls([])

        if config_path.is_dir():
            raw_memes = []
            for file_path in sorted(config_path.rglob("*.json")):
                trigger_from_file = file_path.stem
                for item in json.loads(file_path.read_text(encoding="utf-8")):
                    if "triggers" not in item:
                        item["triggers"] = [trigger_from_file]
                    raw_memes.append(item)
        else:
            raw_memes = json.loads(config_path.read_text(encoding="utf-8"))
        memes = [
            MemeReaction(
                id=str(item.get("id", "unknown")),
                name=str(item.get("name", "Unnamed Meme")),
                triggers=tuple(str(trigger) for trigger in item.get("triggers", [])),
                asset=str(item.get("asset") or ""),
                sound=str(item.get("sound") or ""),
                input_type=str(item.get("input_type") or cls._infer_input_type(item)),
                cooldown_seconds=float(item.get("cooldown_seconds", 3)),
                category=str(item.get("category", "reaction")),
            )
            for item in raw_memes
        ]
        return cls(memes)

    @staticmethod
    def _infer_input_type(item: dict[str, object]) -> str:
        face_triggers = {
            "serious_face",
            "open_mouth",
            "surprised_face",
            "smile",
            "blank_stare",
            "head_tilt",
            "looking_down",
            "closed_eyes",
            "look_side",
            "still_face",
            "wide_open_mouth",
            "calm_face",
            "angry_face",
            "confident_pose",
            "neutral_face",
            "sad_face",
            "big_smile",
        }
        triggers = {str(trigger) for trigger in item.get("triggers", [])}
        return "face" if triggers.intersection(face_triggers) else "hand"

    def update(self, gesture: str, now: float | None = None) -> ActiveMemeReaction | None:
        now = now if now is not None else time.monotonic()
        meme = self._find_meme_for_gesture(gesture)
        if meme is None:
            if self.active is not None and now <= self.active.expires_at:
                return self.active
            self.active = None
            return None

        if self.active is not None and now <= self.active.expires_at and self.active.meme.id == meme.id:
            return self.active

        last_triggered = self.last_triggered_at.get(meme.id)
        effective_cooldown = min(meme.cooldown_seconds, self.min_cooldown_seconds)
        if last_triggered is not None and now - last_triggered < effective_cooldown:
            self.active = None
            return None

        self.last_triggered_at[meme.id] = now
        self.active = ActiveMemeReaction(
            meme=meme,
            started_at=now,
            expires_at=now + self.display_seconds,
        )
        return self.active

    def update_many(
        self,
        gesture: str,
        limit: int,
        now: float | None = None,
    ) -> list[ActiveMemeReaction]:
        now = now if now is not None else time.monotonic()
        candidates = self._matching_memes_for_gesture(gesture)
        if not candidates:
            if self.active_many and now <= max(reaction.expires_at for reaction in self.active_many):
                return self.active_many
            self.active_many = []
            return []

        candidates = candidates[:]
        random.shuffle(candidates)

        active_by_id = {reaction.meme.id: reaction for reaction in self.active_many if now <= reaction.expires_at}
        reactions: list[ActiveMemeReaction] = []
        for meme in candidates[:limit]:
            if meme.id in active_by_id:
                reactions.append(active_by_id[meme.id])
                continue

            last_triggered = self.last_triggered_at.get(meme.id)
            effective_cooldown = min(meme.cooldown_seconds, self.min_cooldown_seconds)
            if last_triggered is not None and now - last_triggered < effective_cooldown:
                continue

            self.last_triggered_at[meme.id] = now
            reactions.append(
                ActiveMemeReaction(
                    meme=meme,
                    started_at=now,
                    expires_at=now + self.display_seconds,
                )
            )

        if reactions:
            self.active_many = reactions
            return reactions
        if self.active_many and now <= max(reaction.expires_at for reaction in self.active_many):
            return self.active_many
        self.active_many = []
        return []

    def _find_meme_for_gesture(self, gesture: str) -> MemeReaction | None:
        candidates = self._matching_memes_for_gesture(gesture)
        if not candidates:
            return None
        return random.choice(candidates)

    def _matching_memes_for_gesture(self, gesture: str) -> list[MemeReaction]:
        if gesture in {"none", "unknown", "unavailable", "hand_detected"}:
            return []

        aliases = {
            "peace": {"peace", "two_fingers"},
            "open_palm": {"open_palm", "both_palms"},
        }
        accepted = aliases.get(gesture, {gesture})

        candidates: list[MemeReaction] = []
        for meme in self.memes:
            if self.allowed_meme_ids is not None and meme.id not in self.allowed_meme_ids:
                continue
            if self.active_input_type != "mixed" and meme.input_type != self.active_input_type:
                continue
            if accepted.intersection(meme.triggers):
                candidates.append(meme)
        return candidates
