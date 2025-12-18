from __future__ import division
import sys
import math
import random
import time
import os
import structures
from collections import deque
import pyglet 
from pyglet import image
from pyglet.gl import *
from pyglet.graphics import TextureGroup
from pyglet.window import key, mouse

TICKS_PER_SEC = 60
SECTOR_SIZE = 16
WALKING_SPEED = 5
FLYING_SPEED = 15
GRAVITY = 20.0
MAX_JUMP_HEIGHT = 2
JUMP_SPEED = math.sqrt(2 * GRAVITY * MAX_JUMP_HEIGHT)
TERMINAL_VELOCITY = 50
PLAYER_HEIGHT = 2

if sys.version_info[0] >= 3:
    xrange = range

def cube_vertices(x, y, z, n):
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,  # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,  # bottom
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,  # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,  # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,  # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,  # back
    ]

def tex_coord(x, y, n=4):
    m = 1.0 / n
    dx = x * m
    dy = y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m

def tex_coords(top, bottom, side):
    top = tex_coord(*top)
    bottom = tex_coord(*bottom)
    side = tex_coord(*side)
    result = []
    result.extend(top)
    result.extend(bottom)
    result.extend(side * 4)
    return result

script_dir = os.path.dirname(os.path.abspath(__file__))
TEXTURE_PATH = os.path.join(script_dir, 'texture.png')

GRASS = tex_coords((1, 0), (0, 1), (0, 0))
SAND = tex_coords((1, 1), (1, 1), (1, 1))
BRICK = tex_coords((2, 0), (2, 0), (2, 0))
STONE = tex_coords((2, 1), (2, 1), (2, 1))

FACES = [(0, 1, 0), (0, -1, 0), (-1, 0, 0), (1, 0, 0), (0, 0, 1), (0, 0, -1)]

def normalize(position):
    x, y, z = position
    return (int(round(x)), int(round(y)), int(round(z)))

def sectorize(position):
    x, y, z = normalize(position)
    return (x // SECTOR_SIZE, 0, z // SECTOR_SIZE)

class Model(object):
    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        self.group = TextureGroup(image.load(TEXTURE_PATH).get_texture())
        self.world = {}
        self.shown = {}
        self._shown = {}
        self.sectors = {}
        self.queue = deque()
        self._initialize()

    def _initialize(self):
        builder = structures.StructureBuilder(self)
        n, s, y = 80, 1, 0
        
        # Terreno base
        for x in xrange(-n, n + 1, s):
            for z in xrange(-n, n + 1, s):
                self.add_block((x, y - 2, z), GRASS, immediate=False)
                self.add_block((x, y - 3, z), STONE, immediate=False)
                if x in (-n, n) or z in (-n, n):
                    for dy in xrange(-2, 3):
                        self.add_block((x, y + dy, z), STONE, immediate=False)

        # Morros
        o = n - 10
        for _ in xrange(120):
            a, b, c = random.randint(-o, o), random.randint(-o, o), -1
            h, s = random.randint(1, 6), random.randint(4, 8)
            t = random.choice([GRASS, SAND, BRICK])
            for y_hill in xrange(c, c + h):
                for x_hill in xrange(a - s, a + s + 1):
                    for z_hill in xrange(b - s, b + s + 1):
                        if (x_hill - a) ** 2 + (z_hill - b) ** 2 > (s + 1) ** 2: continue
                        if (x_hill) ** 2 + (z_hill) ** 2 < 25: continue
                        self.add_block((x_hill, y_hill, z_hill), t, immediate=False)
                s -= 1

        # Estruturas
        house_m = {0: STONE, 1: BRICK, 2: GRASS}
        light_m = {0: STONE, 1: STONE, 2: SAND}
        maze_m = {0: SAND, 1: GRASS, 2: STONE}

        builder.build((10, 0, 10), structures.SIMPLE_HOUSE, house_m)
        builder.build((-15, 0, -10), structures.SIMPLE_HOUSE, house_m)
        builder.build((-20, 0, 20), structures.LIGHTHOUSE, light_m)
        builder.build((20, 0, -20), structures.MAZE, maze_m)

    def hit_test(self, position, vector, max_distance=8):
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in xrange(max_distance * m):
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        return None, None

    def exposed(self, position):
        x, y, z = position
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
        return False

    def add_block(self, position, texture, immediate=True):
        if position in self.world:
            self.remove_block(position, immediate)
        self.world[position] = texture
        self.sectors.setdefault(sectorize(position), []).append(position)
        if immediate:
            if self.exposed(position):
                self.show_block(position)
            self.check_neighbors(position)

    def remove_block(self, position, immediate=True):
        del self.world[position]
        self.sectors[sectorize(position)].remove(position)
        if immediate:
            if position in self.shown:
                self.hide_block(position)
            self.check_neighbors(position)

    def check_neighbors(self, position):
        x, y, z = position
        for dx, dy, dz in FACES:
            key = (x + dx, y + dy, z + dz)
            if key not in self.world: continue
            if self.exposed(key):
                if key not in self.shown: self.show_block(key)
            elif key in self.shown:
                self.hide_block(key)

    def show_block(self, position, immediate=True):
        texture = self.world[position]
        self.shown[position] = texture
        if immediate:
            self._show_block(position, texture)
        else:
            self._enqueue(self._show_block, position, texture)

    def _show_block(self, position, texture):
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, 0.5)
        self._shown[position] = self.batch.add(24, GL_QUADS, self.group,
            ('v3f/static', vertex_data),
            ('t2f/static', list(texture)))

    def hide_block(self, position, immediate=True):
        self.shown.pop(position)
        if immediate:
            self._hide_block(position)
        else:
            self._enqueue(self._hide_block, position)

    def _hide_block(self, position):
        self._shown.pop(position).delete()

    def show_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position not in self.shown and self.exposed(position):
                self.show_block(position, False)

    def hide_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position in self.shown:
                self.hide_block(position, False)

    def change_sectors(self, before, after):
        before_set, after_set, pad = set(), set(), 4
        for dx in xrange(-pad, pad + 1):
            for dy in [0]:
                for dz in xrange(-pad, pad + 1):
                    if dx ** 2 + dy ** 2 + dz ** 2 > (pad + 1) ** 2: continue
                    if before: before_set.add((before[0] + dx, before[1] + dy, before[2] + dz))
                    if after: after_set.add((after[0] + dx, after[1] + dy, after[2] + dz))
        
        for sector in (after_set - before_set): self.show_sector(sector)
        for sector in (before_set - after_set): self.hide_sector(sector)

    def _enqueue(self, func, *args):
        self.queue.append((func, args))

    def _dequeue(self):
        func, args = self.queue.popleft()
        func(*args)

    def process_queue(self):
        start = time.perf_counter()
        while self.queue and time.perf_counter() - start < 1.0 / TICKS_PER_SEC:
            self._dequeue()

    def process_entire_queue(self):
        while self.queue: self._dequeue()

class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        self.inventory_names = ["Tijolo", "Grama", "Areia"]
        self.label = pyglet.text.Label('', font_name='Arial', font_size=18, x=10, y=10, 
                                     anchor_x='left', anchor_y='top', color=(0, 0, 0, 255))
        super(Window, self).__init__(*args, **kwargs)
        self.exclusive = False
        self.flying = False
        self.strafe = [0, 0]
        self.position = (0, 0, 0)
        self.rotation = (0, 0)
        self.sector = None
        self.reticle = None
        self.dy = 0
        self.inventory = [BRICK, GRASS, SAND]
        self.block = self.inventory[0]
        self.num_keys = [key._1, key._2, key._3, key._4, key._5, key._6, key._7, key._8, key._9, key._0]
        self.model = Model()
        self.label.y = self.height - 10
        pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)

    def set_exclusive_mouse(self, exclusive):
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive

    def get_sight_vector(self):
        x, y = self.rotation
        m = math.cos(math.radians(y))
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)

    def get_motion_vector(self):
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            y_angle, x_angle = math.radians(y), math.radians(x + strafe)
            if self.flying:
                m = 1 if self.strafe[1] else math.cos(y_angle)
                dy = 0.0 if self.strafe[1] else math.sin(y_angle)
                if self.strafe[0] > 0: dy *= -1
                dx, dz = math.cos(x_angle) * m, math.sin(x_angle) * m
            else:
                dy, dx, dz = 0.0, math.cos(x_angle), math.sin(x_angle)
        else:
            dx = dy = dz = 0.0
        return (dx, dy, dz)

    def update(self, dt):
        self.model.process_queue()
        sector = sectorize(self.position)
        if sector != self.sector:
            self.model.change_sectors(self.sector, sector)
            if self.sector is None: self.model.process_entire_queue()
            self.sector = sector
        dt = min(dt, 0.2)
        for _ in xrange(8): self._update(dt / 8)

    def _update(self, dt):
        speed = FLYING_SPEED if self.flying else WALKING_SPEED
        d = dt * speed
        dx, dy, dz = self.get_motion_vector()
        dx, dy, dz = dx * d, dy * d, dz * d
        if not self.flying:
            self.dy -= dt * GRAVITY
            self.dy = max(self.dy, -TERMINAL_VELOCITY)
            dy += self.dy * dt
        self.position = self.collide((self.position[0] + dx, self.position[1] + dy, self.position[2] + dz), PLAYER_HEIGHT)

    def collide(self, position, height):
        pad, p, np = 0.25, list(position), normalize(position)
        for face in FACES:
            for i in xrange(3):
                if not face[i]: continue
                d = (p[i] - np[i]) * face[i]
                if d < pad: continue
                for dy in xrange(height):
                    op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    if tuple(op) not in self.model.world: continue
                    p[i] -= (d - pad) * face[i]
                    if face[1]: self.dy = 0
                    break
        return tuple(p)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.exclusive:
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            if (button == mouse.RIGHT) or (button == mouse.LEFT and modifiers & key.MOD_CTRL):
                if previous: self.model.add_block(previous, self.block)
            elif button == mouse.LEFT and block:
                if self.model.world[block] != STONE: self.model.remove_block(block)
        else:
            self.set_exclusive_mouse(True)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.exclusive:
            rx, ry = self.rotation
            rx, ry = rx + dx * 0.15, ry + dy * 0.15
            self.rotation = (rx, max(-90, min(90, ry)))

    def on_key_press(self, symbol, modifiers):
        if symbol == key.W: self.strafe[0] -= 1
        elif symbol == key.S: self.strafe[0] += 1
        elif symbol == key.A: self.strafe[1] -= 1
        elif symbol == key.D: self.strafe[1] += 1
        elif symbol == key.SPACE and self.dy == 0: self.dy = JUMP_SPEED
        elif symbol == key.ESCAPE: self.set_exclusive_mouse(False)
        elif symbol == key.TAB: self.flying = not self.flying
        elif symbol in self.num_keys:
            self.block = self.inventory[(symbol - self.num_keys[0]) % len(self.inventory)]

    def on_key_release(self, symbol, modifiers):
        if symbol == key.W: self.strafe[0] += 1
        elif symbol == key.S: self.strafe[0] -= 1
        elif symbol == key.A: self.strafe[1] += 1
        elif symbol == key.D: self.strafe[1] -= 1

    def on_resize(self, width, height):
        self.label.y = height - 10
        if self.reticle: self.reticle.delete()
        x, y, n = width // 2, height // 2, 10
        self.reticle = pyglet.graphics.vertex_list(4, ('v2i', (x - n, y, x + n, y, x, y - n, x, y + n)))

    def set_2d(self):
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        glViewport(0, 0, *self.get_viewport_size())
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, max(1, width), 0, max(1, height), -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def set_3d(self):
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, *self.get_viewport_size())
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        glTranslatef(*[-pos for pos in self.position])

    def on_draw(self):
        self.clear()
        self.set_3d()
        glColor3d(1, 1, 1)
        self.model.batch.draw()
        self.draw_focused_block()
        self.set_2d()
        self.draw_label()
        self.draw_reticle()

    def draw_focused_block(self):
        block = self.model.hit_test(self.position, self.get_sight_vector())[0]
        if block:
            vertex_data = cube_vertices(block[0], block[1], block[2], 0.51)
            glColor3d(0, 0, 0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', vertex_data))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def draw_label(self):
        x, y, z = self.position
        self.label.text = '%02d (%.2f, %.2f, %.2f) %d / %d' % (
            pyglet.clock.get_fps(), x, y, z, len(self.model._shown), len(self.model.world))
        self.label.draw()

    def draw_reticle(self):
        if self.reticle:
            glColor3d(0, 0, 0)
            self.reticle.draw(GL_LINES)

def setup_fog():
    glEnable(GL_FOG)
    glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.5, 0.69, 1.0, 1))
    glHint(GL_FOG_HINT, GL_DONT_CARE)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, 20.0)
    glFogf(GL_FOG_END, 60.0)

def setup():
    glClearColor(0.5, 0.69, 1.0, 1)
    glEnable(GL_CULL_FACE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    setup_fog()

def main():
    window = Window(width=800, height=600, caption='Pyglet', resizable=True)
    window.set_exclusive_mouse(True)
    setup()
    pyglet.app.run()

if __name__ == '__main__':
    main()