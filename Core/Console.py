import asyncio
import curses
import math
import threading
from typing import AsyncIterator, Coroutine

from ollama import ChatResponse


async def init_curses():
    """
    Initialize the curses library
    """
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    return stdscr


def get_input(win) -> str:
    """
    Get input from the user
    """
    win.addstr("-> ")
    win.refresh()
    curses.echo()
    capture = win.getstr().decode("utf-8")
    curses.noecho()
    return capture


async def draw_chat(win, lines, current_line="", *args):
    print("Drawing chat")
    win.clear()
    height, width = win.getmaxyx()
    win.addstr(0, 0, f"h: {height}, w: {width}")

    display_lines = lines[:]

    if current_line:
        display_lines.append(current_line)

    start_line = max(0, len(display_lines) - (height - 2))
    for idx, line in enumerate(display_lines[start_line:], start=1):
        win.addstr(idx + 1, 0, line)
    win.refresh()

async def ai_task(iterator):
    print("AI Task")
    lines = []
    current_line = ""
    async for part in (await iterator()):
        text = part["response"]
        if "\n" in text:
            parts = text.split("\n")
            lines.append(current_line + parts[0])
            lines.extend(parts[1:-1])
            current_line = parts[-1]
        else:
            current_line += text
        # await draw_chat(output_win, lines, current_line, height, width)
        # await asyncio.sleep(0.1)

async def draw_ai_interface(iterator):
    stdscr = await init_curses()
    height, width = stdscr.getmaxyx()
    output_win = stdscr.subwin(height -2, width, 0, 0)
    input_win = stdscr.subwin(1, width, height - 1, 0)
    input_win.refresh()

    loop = asyncio.get_event_loop()
    task = asyncio.create_task(ai_task(iterator))

    while True:
        print("Drawing ai interface")
        user_input = get_input(input_win)
        if user_input == "q":
            break

    curses.endwin()