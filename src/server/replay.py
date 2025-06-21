from typing import TypeAlias

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None

def validateReplayJson(replayFile: JSON) -> bool:
    if not isinstance(replayFile, dict):
        return False
    return all([ 
        validateReplayBlock(replayFile, "player", ["uid", "nickname"]), 
        validateReplayBlock(replayFile, "info", ["level_id", "score", "time"]), 
        "replay" in replayFile,
        isinstance(replayFile['replay'], list)
    ])

def validateReplayBlock(replayFile: JSON, blockName: str, keys: list[str]) -> bool:
    if not isinstance(replayFile, dict):
        return False
    if blockName not in replayFile:
        return False
    block = replayFile[blockName]
    if not isinstance(block, dict):
        return False
    return all(key in block for key in keys)
