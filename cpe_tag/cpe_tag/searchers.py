#!/usr/bin/env python3

import asyncio
import logging
from re import search, sub
from shlex import quote


def get_cpe_uri_from_json_line(json_line: str) -> str:
    no_key = ":".join(json_line.split(":")[1:])
    no_white_chars = no_key.strip()
    no_quotes = no_white_chars.replace('"', "")
    no_trailing_comma = sub(r",$", "", no_quotes)
    final = no_trailing_comma
    return final


def log_error(quasi_cpe: str, stderr: bytes) -> None:
    err = stderr.decode("utf-8")
    if len(err) > 0:
        logging.error(f"[{quasi_cpe}] {err}")


async def get_feed(feed_loc: str, quasi_cpe: str) -> str:
    shell_escaped_path = quote(feed_loc)
    shell_escaped_keyword = quote(quasi_cpe)
    proc = await asyncio.create_subprocess_shell(
        f"/bin/zcat {shell_escaped_path} | /bin/grep -E {shell_escaped_keyword}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    log_error(quasi_cpe, stderr)
    return stdout.decode("utf-8").splitlines()


async def query_cpe_match(hub, quasi_cpe: str, feed=None) -> list:
    matches = []

    pattern = hub.cpe_tag.generators.convert_quasi_cpe_to_regex(quasi_cpe)

    if feed is None:
        feed_loc = hub.OPT.cpe_tag.cpe_match_feed
        feed = await get_feed(feed_loc, pattern)

    for line in feed:
        s = search(pattern, line)
        if s is not None:
            matches.append(get_cpe_uri_from_json_line(s.string))
    return list(set(matches))
