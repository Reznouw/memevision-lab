from __future__ import annotations

import json

from memevision_lab.core.meme_reactions import MemeReactionEngine


def test_loads_nested_trigger_configs_and_infers_missing_trigger(tmp_path):
    config_dir = tmp_path / "configs" / "memes" / "by_trigger"
    config_dir.mkdir(parents=True)
    (config_dir / "thumbs_up.json").write_text(
        json.dumps([
            {
                "id": "thumb",
                "name": "Thumb",
                "asset": "local_assets/memes/hands/thumb.gif",
                "input_type": "hand",
            }
        ]),
        encoding="utf-8",
    )

    engine = MemeReactionEngine.from_config(tmp_path / "configs" / "memes")

    assert len(engine.memes) == 1
    assert engine.memes[0].triggers == ("thumbs_up",)


def test_update_many_respects_mode_allowed_ids_and_limit(monkeypatch):
    memes = [
        _meme("hand_one", "thumbs_up", "hand"),
        _meme("hand_two", "thumbs_up", "hand"),
        _meme("face_one", "thumbs_up", "face"),
    ]
    engine = MemeReactionEngine(
        memes,
        active_input_type="hand",
        allowed_meme_ids={"hand_one", "hand_two", "face_one"},
    )
    monkeypatch.setattr("memevision_lab.core.meme_reactions.random.shuffle", lambda _items: None)

    reactions = engine.update_many("thumbs_up", limit=1, now=10.0)

    assert [reaction.meme.id for reaction in reactions] == ["hand_one"]


def test_update_many_randomizes_candidates_for_same_trigger(monkeypatch):
    memes = [
        _meme("hand_one", "open_palm", "hand"),
        _meme("hand_two", "open_palm", "hand"),
    ]
    engine = MemeReactionEngine(memes, active_input_type="hand")

    def reverse_candidates(candidates):
        candidates.reverse()

    monkeypatch.setattr("memevision_lab.core.meme_reactions.random.shuffle", reverse_candidates)

    reactions = engine.update_many("open_palm", limit=1, now=10.0)

    assert [reaction.meme.id for reaction in reactions] == ["hand_two"]


def _meme(meme_id: str, trigger: str, input_type: str):
    from memevision_lab.core.meme_reactions import MemeReaction

    return MemeReaction(
        id=meme_id,
        name=meme_id,
        triggers=(trigger,),
        asset=f"local_assets/{meme_id}.gif",
        sound="",
        input_type=input_type,
        cooldown_seconds=1.0,
        category="test",
    )
