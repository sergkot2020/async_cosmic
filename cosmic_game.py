import time
import curses
import asyncio
import random
from curses_tools import draw_frame, fire, read_controls, get_frame_size
from itertools import cycle

TIMES = 1000
STARS = 300


def read_frame():
    with open('frames/rocket_frame_1.txt') as frame_1, open('frames/rocket_frame_2.txt') as frame_2:
        return frame_1.read(), frame_2.read()


class Blink:
    """ Starry sky """
    # star twinkling period
    A_DIM_TIC = 20
    DEFAULT_TIC = 3
    A_BOLD_TIC = 5
    DEFAULT2_TIC = 3

    SPEED = 3  # the most fast speed is 1
    SYMBOLS = ['+', '*', '.', ':']

    def __init__(self, canvas, row=None, column=None, symbol='*', start_tic=1, is_random=True):
        self.cycle = sum([self.A_DIM_TIC, self.DEFAULT_TIC, self.A_BOLD_TIC, self.DEFAULT2_TIC])
        self.max_y, self.max_x = canvas.getmaxyx()
        if is_random:
            row = random.randint(2, self.max_y - 2)
            column = random.randint(2, self.max_x - 2)
            symbol = random.choice(self.SYMBOLS)
            start_tic = random.randint(1, self.cycle)

        self.canvas = canvas
        self.row = row
        self.column = column
        self.symbol = symbol
        self.start_tic = start_tic
        self.left_dim, self.right_dim = (0, self.A_DIM_TIC)
        self.left_bold = self.A_DIM_TIC + self.DEFAULT_TIC
        self.right_bold = self.A_DIM_TIC + self.DEFAULT_TIC + self.A_BOLD_TIC

    async def run(self):
        start = self.start_tic
        count_tic = 0
        while True:
            for i in range(start, self.cycle):
                count_tic += 1
                args = [self.row, self.column, self.symbol]
                if self.left_dim < i <= self.right_dim:
                    args.append(curses.A_DIM)
                elif self.left_bold < i <= self.right_bold:
                    args.append(curses.A_BOLD)
                self.canvas.addstr(*args)

                await asyncio.sleep(0)

                self.canvas.addstr(self.row, self.column, ' ')

                if count_tic % self.SPEED == 0:
                    self.row += 1
                    if self.row == (self.max_y - 1):
                        self.row = 1

            start = 1


class Spaceship:

    def __init__(self, canvas, frame_1, frame_2, speed=1):
        self.row, self.columns = get_frame_size(frame_1)
        self.max_x, self.max_y = canvas.getmaxyx()
        self.left_border = self.top_border = 0 + 1
        self.right_border = self.max_y - 1
        self.bottom_border = self.max_x - 1
        self.x = self.current_x = int(self.max_x / 2)
        self.y = self.current_y = int(self.max_y / 2)
        self.canvas = canvas
        self.canvas.nodelay(True)
        self.inf_frame_loop = cycle([frame_1, frame_2])
        self.previous = None
        self.speed = speed

    def set_x_y(self):
        delta_x, delta_y, space = read_controls(self.canvas)
        new_x = self.current_x + delta_x * self.speed
        new_y = self.current_y + delta_y * self.speed
        self.current_x = max(min(self.bottom_border - self.row, new_x), self.top_border)
        self.current_y = max(min(self.right_border - self.columns, new_y), self.left_border)

    async def run(self):
        for frame in self.inf_frame_loop:
            if self.previous:
                draw_frame(self.canvas, self.current_x, self.current_y, self.previous, negative=True)
            self.set_x_y()
            draw_frame(self.canvas, self.current_x, self.current_y, frame)
            self.previous = frame
            await asyncio.sleep(0)


def draw(canvas):
    frame_1, frame_2 = read_frame()
    max_y, max_x = canvas.getmaxyx()
    coroutines = [
        Blink(canvas, is_random=True).run() for _ in range(STARS)
    ]
    coroutines.extend([
        fire(canvas, int(max_y / 2), int(max_x / 2)),
        Spaceship(canvas, frame_1, frame_2, speed=3).run(),
    ])
    while True:
        canvas.border()
        for i, coroutine in enumerate(coroutines):
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.pop(i)
        canvas.refresh()
        time.sleep(0.1)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
    curses.curs_set(0)
