from typing import TypeAlias


JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None

def validateReplayJson(replayFile: JSON) -> bool:
    return all([
        validateReplayBlock(replayFile, "player", ["uid", "nickname"]), 
        validateReplayBlock(replayFile, "info", ["level_id", "score", "time"]), 
        "replay" in replayFile
    ])

def validateReplayBlock(replayFile: JSON, blockName: str, keys: list[str]) -> bool:
    if blockName not in replayFile:
        return False
    return all(key in replayFile[blockName] for key in keys)
