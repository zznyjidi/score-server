import asyncio
import concurrent.futures
from typing import Literal
from argon2 import PasswordHasher

HasherProcessPool = concurrent.futures.ProcessPoolExecutor()
Hasher = PasswordHasher()

async def hash(password: str | bytes) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(HasherProcessPool, Hasher.hash, password)

async def verify(hash: str, password: str | bytes) -> Literal[True]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(HasherProcessPool, Hasher.verify, hash, password)

async def check_needs_rehash(hash: str) -> bool:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(HasherProcessPool, Hasher.check_needs_rehash, hash)
