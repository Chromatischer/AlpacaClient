import asyncio
import curses
import math
from typing import AsyncIterator

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


async def get_input(win) -> str:
    """
    Get input from the user
    """
    win.addstr("-> ")
    win.refresh()
    curses.echo()
    capture = win.getstr().decode("utf-8")
    curses.noecho()
    return capture


async def draw_chat(win, lines):
    win.clear()
    height, width = win.getmaxyx()
    start_line = max(0, len(lines) - (height - 2))
    for idx, line in enumerate(lines[start_line:], start=1):
        win.addstr(idx, 0, line)
    win.refresh()


async def draw_ai_interface(iterator: AsyncIterator[ChatResponse]):
    stdscr = await init_curses()
    height, width = stdscr.getmaxyx()
    output_win = stdscr.subwin(height - 2, width, 0, 0)
    input_win = stdscr.subwin(1, width, height - 1, 0)
    input_win.addstr("-> ")
    input_win.refresh()

    lines = []
    loop = asyncio.get_event_loop()
    async def ai_task():
        async for response in iterator:
            lines.append(response.message.content)
            await draw_chat(output_win, lines)
            await asyncio.sleep(0.1)

    async def input_task():
        while True:
            user_input = await loop.run_in_executor(None, get_input, input_win)
            if user_input == "q":
                break

    await asyncio.gather(ai_task(), input_task())
    curses.endwin()


