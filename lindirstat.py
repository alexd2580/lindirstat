import sys
import pygame
import pathlib
import functools
from hurry.filesize import size, alternative


def render_text(text, font, surface, x, y):
    lines = text.split('\n')
    line_sizes = [font.size(line) for line in lines]
    text_width, text_height = functools.reduce(
        lambda t_size, l_size:
            (max(t_size[0], l_size[0]), t_size[1] + l_size[1]),
        line_sizes,
    )

    target_width, target_height = surface.get_size()
    frame_width, frame_height = text_width + 11, text_height + 10
    expected_frame_x, expected_frame_y = x - 5, y - 5
    frame_x = min(max(0, expected_frame_x), target_width - frame_width)
    frame_y = min(max(0, expected_frame_y), target_height - frame_height)
    text_pos = x - expected_frame_x + frame_x, y - expected_frame_y + frame_y
    frame_rect = frame_x, frame_y, frame_width, frame_height

    surface.fill(pygame.Color(20, 20, 20, 255), frame_rect)
    for line, line_size in zip(lines, line_sizes):
        text_surface = font.render(line, True, pygame.Color(255, 255, 255, 255))
        surface.blit(text_surface, dest=text_pos)
        text_pos = text_pos[0], text_pos[1] + line_size[1]


class Directory:
    def __init__(self, path, parent=None, size_bytes=0, directories=[]):
        self.path = path
        self.parent = parent
        self.size_bytes = size_bytes
        self.directories = directories

        self.rect = None


def is_pos_in_rect(pos, rect):
    x, y, w, h = rect
    pos_x, pos_y = pos
    return x <= pos_x <= x + w and y <= pos_y <= y + h


def get_info_string_at_pos(base_directory, pos):
    for directory in base_directory.directories:
        if directory.rect and is_pos_in_rect(pos, directory.rect):
            return get_info_string_at_pos(directory, pos)
    return "Path: {path}\nSize: {size}".format(
        path=str(base_directory.path),
        size=size(base_directory.size_bytes, system=alternative),
    )


def analyze_directory(path, parent=None):
    """Analyze and create a `Directory`."""
    base_directory = Directory(path)
    sub_directories = []
    for child in path.iterdir():
        if child.is_dir() and not child.is_symlink():
            sub_directories.append(analyze_directory(child, parent=base_directory))
        elif child.is_file():
            sub_directories.append(
                Directory(child, parent=base_directory, size_bytes=child.stat().st_size)
            )
        else:
            pass

    return Directory(
        path,
        parent=parent,
        size_bytes=sum([d.size_bytes for d in sub_directories]),
        directories=sorted(sub_directories, key=lambda directory: -directory.size_bytes),
    )


def test_row_layout(row, row_bytes, rect_size, remaining_rect_bytes):
    rect_w, rect_h = rect_size
    percent_h = row_bytes / remaining_rect_bytes
    absolute_h = round(percent_h * rect_h)

    remaining_row_bytes = row_bytes
    remaining_w = rect_w

    item_widths = []
    for item in row:
        percent_w = item.size_bytes / remaining_row_bytes
        absolute_w = round(percent_w * remaining_w)
        item_widths.append(absolute_w)

        remaining_row_bytes = remaining_row_bytes - item.size_bytes
        remaining_w = remaining_w - absolute_w

        # We do not want items to be taller than wide.
        if absolute_h > absolute_w > 0:
            return None, None

    return absolute_h, zip(row, item_widths)

    # If all items had suitable layouts, continue the recursion.
    # item_x = base_x
    # for item in row:
    #     item_rect = item_x + 2, base_y + 2, item.absolute_w - 4, absolute_h - 4
    #     if item_rect[2] > 4 and item_rect[3] > 4:
    #         compute_layout(item, item_rect)
    #     item_x = item_x + item.absolute_w
    #
    # return (base_x, base_y + absolute_h, base_w, remaining_h),


def compute_layout(base_directory, base_rect):
    """Renders the `directory` in the `rect` with `base_color`."""
    base_x, base_y, base_w, base_h = base_rect

    # Should not be rendered at all.
    if base_w <= 0 or base_h <= 0:
        base_directory.rect = None
        return

    base_directory.rect = base_rect
    # Should not be rendered recursively.
    if base_w <= 4 or base_h <= 4:
        return

    if base_directory.directories:
        remaining_bytes = base_directory.size_bytes

        rows = []
        remaining_h = base_h

        row = []
        processed_row = []
        row_bytes = 0
        row_h = None

        for directory in base_directory.directories:
            if directory.size_bytes > 0:
                row_with_item = [*row, directory]
                height, new_processed_row = test_row_layout(
                    row_with_item,
                    row_bytes + directory.size_bytes,
                    (base_w, remaining_h),
                    remaining_bytes,
                )

                if height is not None:
                    row = row_with_item
                    processed_row = new_processed_row
                    row_bytes = row_bytes + directory.size_bytes
                    row_h = height
                    continue

                # Layout didn't fit, so we push the previous row configuration.
                rows.append((processed_row, row_h))
                remaining_bytes = remaining_bytes - row_bytes
                remaining_h = remaining_h - row_h

                # Reset the loop variables.
                row = [directory]
                row_bytes = directory.size_bytes
                row_h, processed_row = test_row_layout(
                    row, row_bytes, (base_w, remaining_h), remaining_bytes
                )

        # Push the last stuff into the vector.
        if row_h is not None:
            rows.append((processed_row, row_h))
            remaining_bytes = remaining_bytes - row_bytes
            remaining_h = remaining_h - row_h

        assert remaining_bytes == 0
        assert remaining_h == 0

        # Now render compute the rects and call `compute_layout` recursively.
        row_y = base_y
        for row, row_h in rows:
            item_x = base_x
            for item, item_w in row:
                item_rect = item_x + 2, row_y + 2, item_w - 4, row_h - 4
                compute_layout(item, item_rect)
                item_x = item_x + item_w
            row_y = row_y + row_h


def handle_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        # elif event.type == pygame.MOUSEMOTION:
        #     print(event)


def render_directory(screen, base_color, color_factor, base_directory):
    """Renders the `directory` in the `rect` with `base_color`."""
    screen.fill(base_color, base_directory.rect)
    for index, directory in enumerate(base_directory.directories):
        if directory.rect:
            sub_hue = pygame.Color(0, 0, 0, 0)
            sub_hue.hsva = 360 * index / len(base_directory.directories), 100, 100, 100
            sub_color = pygame.Color(*[
                round((base_v + color_factor * sub_hue_v) / (1 + color_factor))
                for base_v, sub_hue_v in zip(base_color, sub_hue)
            ])
            render_directory(screen, sub_color, color_factor * 0.95, directory)


pygame.init()

font = pygame.font.SysFont('dejavusansmono', 12)

window_size = width, height = 1440, 900
root_rect = 0, 0, width, height

black = 0, 0, 0
red = 255, 0, 0
white = pygame.Color(255, 255, 255, 255)

screen = pygame.display.set_mode(window_size)
base_directory = analyze_directory(pathlib.Path('/home'))
compute_layout(base_directory, root_rect)

clock = pygame.time.Clock()

while True:
    clock.tick(30)
    handle_events()
    render_directory(screen, white, 1.0, base_directory)
    pos = pygame.mouse.get_pos()
    info_string = get_info_string_at_pos(base_directory, pos)
    if info_string:
        render_text(info_string, font, screen, pos[0], pos[1] + 20)

    pygame.display.flip()
