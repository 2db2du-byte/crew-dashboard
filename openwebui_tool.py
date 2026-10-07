"""
title: Rabbid's Knowledge
description: News feeds, offline library (Wikipedia, WikiMed, iFixit, Stack Exchange, survival guides), Rabbid's SecondBrain notes, the time, and a calculator. All local, works with no internet.
author: Claude for Rabbid
version: 1.2
"""
# Installed into Open WebUI by Claude (2026-10-06). Source of truth: ~/Projects/crew-dashboard/openwebui_tool.py
# Everything goes through Mission Control's /api/kb/* (kb.py), the same knowledge Joshua uses.
import json
import urllib.request
from urllib.parse import quote

KB = "http://127.0.0.1:8899/api/kb/"


def _kb(what: str, q: str = "", timeout: int = 60) -> dict:
    req = urllib.request.Request(f"{KB}{what}?q={quote(q)}", headers={"X-Crew": "1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


class Tools:
    def search_offline_library(self, query: str) -> str:
        """
        Look up facts in Rabbid's offline library: all of English Wikipedia, WikiMed (medicine), iFixit repair guides,
        Stack Exchange (Linux, Ubuntu, computers, electronics, DIY, cars, cooking, gardening, money, outdoors) and
        survival guides. Use it for any factual question instead of guessing. Works with no internet.
        :param query: A short topic to look up, like "heat pump" or "bowline knot" (not a full sentence).
        """
        try:
            r = _kb("library", query)
        except Exception as e:
            return f"The offline library didn't answer ({e})."
        if r.get("error") or not r.get("results"):
            return r.get("error") or f"Nothing found in the offline library for '{query}'."
        return "\n\n".join(f"[{a['source']}: {a['title']}]\n{a['text']}" for a in r["results"])

    def search_my_notes(self, query: str) -> str:
        """
        Search Rabbid's own notes (his SecondBrain: to-do list, projects, home lab, devices, plans, daily notes).
        Use it whenever Rabbid asks about himself, his stuff, his plans, or says "my".
        :param query: What to look for, like "to-do list" or "backup drive".
        """
        try:
            r = _kb("notes", query)
        except Exception as e:
            return f"Couldn't search the notes ({e})."
        return "\n\n".join(f"[Note: {n['note']}]\n{n['text']}" for n in r["results"]) or "No matching notes."

    def search_news(self, query: str) -> str:
        """
        Search Rabbid's news feeds from the last 30 days (world news, science, tech and AI, Linux and Omarchy).
        Use it for anything recent: "what's happening with...", "latest news on...", "any news about...".
        :param query: The topic, like "Mars mission" or "Omarchy update".
        """
        try:
            r = _kb("news", query)
        except Exception as e:
            return f"Couldn't search the news ({e})."
        return "\n\n".join(f"[{a['feed']}, {a['date']}] {a['title']}\n{a['text']}\n{a['link']}" for a in r["results"]) or "No matching news."

    def linux_command_help(self, question: str) -> str:
        """
        Plain-English examples for Linux terminal commands (tldr pages, offline). Use it whenever Rabbid asks how to use
        a terminal command, like "how do I unzip a tar file" or "what does grep do".
        :param question: The question, including the command name if known, like "tar extract" or "git commit".
        """
        try:
            r = _kb("command", question)
        except Exception as e:
            return f"Couldn't look that up ({e})."
        return "\n\n".join(c["text"] for c in r["results"]) or "No cheat sheet found for that command."

    def get_current_time(self) -> str:
        """
        Get the current date and time on Rabbid's laptop.
        """
        return _kb("now")["now"]

    def calculator(self, expression: str) -> str:
        """
        Do exact math. Use it for any arithmetic instead of working it out in your head.
        :param expression: A math expression like "15/100*80" or "sqrt(144) + 2**3".
        """
        try:
            return str(_kb("calc", expression)["answer"])
        except Exception as e:
            return f"Couldn't calculate that ({e})."
