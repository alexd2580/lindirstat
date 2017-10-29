import sys
import pygame
import pathlib


def render_text(text, font, surface, x, y):
    width, height = font.size(text)
    surface.fill(pygame.Color(20, 20, 20, 255), (x - 5, y - 5, width + 11, height + 10))
    text_surface = font.render(text, True, pygame.Color(255, 255, 255, 255))
    surface.blit(text_surface, dest=(x, y))


class File:
    def __init__(self, path, size_bytes, rect):
        self.path = path
        self.size_bytes = size_bytes

        self.rect = rect


class Directory:
    def __init__(self, path, size_bytes, directories, files, rect):
        self.path = path
        self.size_bytes = size_bytes
        self.directories = directories
        self.files = files

        self.rect = rect


def is_pos_in_rect(pos, rect):
    x, y, w, h = rect
    pos_x, pos_y = pos
    return x <= pos_x <= x + w and y <= pos_y <= y + h


def get_info_string_at_pos(base_directory, pos):
    if is_pos_in_rect(pos, base_directory.rect):
        for directory in base_directory.directories:
            if is_pos_in_rect(pos, directory.rect):
                return get_info_string_at_pos(pos, directory)
        for file in base_directory.files:
            if is_pos_in_rect(pos, file.rect):
                return file.name


def analyze_directory(path):
    """Analyze and create a `Directory`."""
    directories = []
    files = []
    for child in path.iterdir():
        if child.is_dir() and not child.is_symlink():
            directories.append(analyze_directory(child))
        elif child.is_file():
            files.append(File(child, child.stat().st_size, None))
        else:
            print("Unused file: {file}".format(file=str(child)))

    total_size = sum([f.size_bytes for f in files]) + sum([d.size_bytes for d in directories])
    directories = sorted(directories, key=lambda directory: -directory.size_bytes)
    files = sorted(files, key=lambda file: -file.size_bytes)
    return Directory(path, total_size, directories, files, None)


def handle_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        # elif event.type == pygame.MOUSEMOTION:
        #     print(event)


def render_directory(screen, rect, base_color, color_factor, base_directory):
    """Renders the `directory` in the `rect` with `base_color`."""
    base_directory.rect = rect
    x, y, w, h = rect
    for index, directory in enumerate(base_directory.directories):
        sub_rect = None
        size_percent = 1 if base_directory.size_bytes == 0 \
            else directory.size_bytes / base_directory.size_bytes
        if w > h:
            sub_w = round(w * size_percent)
            sub_rect = x, y, sub_w, h
            x = x + sub_w
            w = w - sub_w
        else:
            sub_h = round(h * size_percent)
            sub_rect = x, y, w, sub_h
            y = y + sub_h
            h = h - sub_h

        sub_hue = pygame.Color(0, 0, 0, 0)
        sub_hue.hsva = 360 * index / len(base_directory.directories), 100, 100, 100
        sub_color = pygame.Color(*[
            round((base_v + color_factor * sub_hue_v) / (1 + color_factor))
            for base_v, sub_hue_v in zip(base_color, sub_hue)
        ])

        screen.fill(sub_color, sub_rect)
        sub_x, sub_y, sub_w, sub_h = sub_rect
        if sub_w > 4 and sub_h > 4:
            sub_rect = sub_x + 2, sub_y + 2, sub_w - 4, sub_h - 4
            render_directory(screen, sub_rect, sub_color, color_factor * 0.95, directory)

    for index, file in enumerate(base_directory.files):
        sub_rect = None
        size_percent = 1 if file.size_bytes == 0 else file.size_bytes / base_directory.size_bytes
        if w > h:
            sub_w = round(w * size_percent)
            sub_rect = x, y, sub_w, h
            x = x + sub_w
            w = w - sub_w
        else:
            sub_h = round(h * size_percent)
            sub_rect = x, y, w, sub_h
            y = y + sub_h
            h = h - sub_h

        file.rect = rect

        sub_hue = pygame.Color(0, 0, 0, 0)
        sub_hue.hsva = 360 * index / len(base_directory.files), 100, 100, 100
        sub_color = pygame.Color(*[
            round((base_v + color_factor * sub_hue_v) / (1 + color_factor))
            for base_v, sub_hue_v in zip(base_color, sub_hue)
        ])

        screen.fill(sub_color, sub_rect)
        # sub_x, sub_y, sub_w, sub_h = sub_rect
        # if sub_w > 2 and sub_h > 2:
        #     sub_rect = sub_x + 1, sub_y + 1, sub_w - 2, sub_h - 2
        #     screen.fill(base_color, sub_rect)


pygame.init()

font = pygame.font.SysFont('dejavusansmono', 12)

size = width, height = 1440, 900
root_rect = 0, 0, width, height

black = 0, 0, 0
red = 255, 0, 0
white = pygame.Color(255, 255, 255, 255)

screen = pygame.display.set_mode(size)
base_directory = analyze_directory(pathlib.Path('/home/sascha/Downloads'))

# for directory in base_directory.directories:
#     print('{name}\r\t\t\t\t{size}'.format(name=directory.path.name, size=directory.size_bytes))
# for file in base_directory.files:
#     print('{name}\r\t\t\t\t{size}'.format(name=file.path.name, size=file.size_bytes))

while True:
    handle_events()
    print("Rendering")
    render_directory(screen, root_rect, white, 1.0, base_directory)
    pos = pygame.mouse.get_pos()
    info_string = get_info_string_at_pos(base_directory, pos)
    render_text('ADASD', font, screen, 100, 100)

    pygame.display.flip()


