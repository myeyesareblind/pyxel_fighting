import pyxel
from enum import Enum

SIZE = 256
PLAYER_SIZE = 16

class Point:
    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y

class Rect:
    def __init__(self, x, y, w, h) -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def contains(self, other):
        return self.x <= other.x \
            and self.y <= other.y \
            and self.w + self.x >= other.x + other.w \
            and self.y + self.h >= other.y + other.h
    
    def move(self, x = None, y = None):
        if x is not None:
            self.x += x
        if y is not None:
            self.y += y

VIEWPORT = Rect(0, 0, SIZE, SIZE)

class Direction(Enum):
    LEFT = 1
    RIGHT = 2
    TOP = 3
    BOTTOM = 4

class SwordState(Enum):
    NONE = 1
    HITTING = 2

class HorizontalDirection(Enum):
    LEFT = 1
    RIGHT = 2

class Scene:
    def update(self):
        return self

    def draw(self):
        pass

class SceneRouter:
    def __init__(self, scene) -> None:
        self.scene = scene

    def update(self):
        self.scene = self.scene.update()
    
    def draw(self):
        self.scene.draw()

class EndScene:
    def __init__(self, winner) -> None:
        self.winner = winner
    
    def update(self):
        if pyxel.btn(pyxel.KEY_R):
            return GameScene()
        return self

    def draw(self):
        pyxel.text(SIZE / 2, SIZE / 2, "{} is winner!".format(self.winner.name), pyxel.COLOR_PINK)
        pyxel.text(SIZE / 2, SIZE / 2 + 10, "press r to restart", pyxel.COLOR_PINK)

class GameScene:
    def __init__(self) -> None:
        self.players = []
        self.bullets = []
        self.shot_producers = []
        self.movers = []
        self.painters = []
        self.sword_systems = []

        p1 = Player(0, 0, 
                    "Kiril")

        p2 = Player(SIZE - PLAYER_SIZE, 0, 
                    "Max")

        self.players.append(p1)
        self.players.append(p2)
        p1_mover = Mover(p1, pyxel.KEY_A, pyxel.KEY_D, pyxel.KEY_W, pyxel.KEY_S, HorizontalDirection.RIGHT)
        p1_sword = SwordSystem(p1, p1_mover, pyxel.KEY_1)
        self.movers.append(p1_mover)
        p2_mover = Mover(p2, pyxel.KEY_LEFT, pyxel.KEY_RIGHT, pyxel.KEY_UP, pyxel.KEY_DOWN, HorizontalDirection.LEFT)
        self.movers.append(p2_mover)

        p1_painter = StaticPlayerPainter(p1, p1_mover, Rect(0,0,14,16))
        p2_painter = StaticPlayerPainter(p2, p2_mover, Rect(0,16,16,16))
        p1_sword_painter = SwordPainter(p1, p1_mover, p1_sword, Point(13, 13), Rect(13, 2, 3, 14), Point(0, 11), Rect(29,11, 15, 5), Point(0, 3))
        self.painters.append(p1_painter)
        #self.painters.append(p2_painter)
        #self.painters.append(p1_sword_painter)

        # self.shot_producers.append(ShotProducer(p1, p1_mover, pyxel.KEY_1))
        self.shot_producers.append(ShotProducer(p2, p2_mover, pyxel.KEY_RETURN))

        self.sword_systems.append(p1_sword)

    def update(self):
        for shot_producer in self.shot_producers:
            bullet = shot_producer.check_bullet()
            if bullet is not None:
                self.bullets.append(bullet)

        for mover in self.movers:
            mover.update()

        for b in self.bullets:
            b.update()
            hit_player = b.check_hit(self.players)
            if hit_player is not None:
                self.players.remove(hit_player)
                return EndScene(self.players[0])
        
        self.bullets = [b for b in self.bullets if VIEWPORT.contains(b.bounds())]

        return self
    
    def draw(self):
        for b in self.bullets:
            b.draw()

        for painter in self.painters:
            painter.draw()

class SwordSystem:
    def __init__(self, player, mover, key) -> None:
        self.player = player
        self.mover = mover
        self.key = key
        self.state = SwordState.NONE
        self.delay = 20
        self.last = -1000000
        self.length = 10
        self.hit_frame = 0
    
    def update(self):
        match self.state:
            case SwordState.NONE:
                if pyxel.btn(self.key) and pyxel.frame_count - self.last > self.delay:
                    self.state = SwordState.HITTING
                    self.hit_frame = 0
            case SwordState.HITTING:
                self.hit_frame += 1
                if self.hit_frame >= self.length:
                    self.state = SwordState.NONE
                    self.last = pyxel.frame_count

class Bullet:
    def __init__(self, player, direction) -> None:
        match direction:
            case Direction.LEFT:
                self.x = player.x - 1
                self.y = player.y + PLAYER_SIZE / 2
            case Direction.RIGHT:
                self.x = player.x + PLAYER_SIZE
                self.y = player.y + PLAYER_SIZE / 2
            case Direction.TOP:
                self.x = player.x + PLAYER_SIZE / 2
                self.y = player.y - 1
            case Direction.BOTTOM:
                self.x = player.x + PLAYER_SIZE / 2
                self.y = player.y + PLAYER_SIZE
        self.direction = direction
        self.player = player
    
    def update(self):
        match self.direction:
            case Direction.LEFT:
                self.x -= 1
            case Direction.RIGHT:
                self.x += 1
            case Direction.TOP:
                self.y -= 1
            case Direction.BOTTOM:
                self.y += 1
    
    def bounds(self):
        return Rect(self.x, self.y, 1, 1)

    def check_hit(self, players):
        for p in players:
            if p.bounds().contains(self.bounds()):
                return p
        return None
    
    def draw(self):
        pyxel.pset(self.x, self.y, pyxel.COLOR_GREEN)

class ShotProducer:
    def __init__(self, player, mover, key) -> None:
        self.delay = 20
        self.last = -1000000
        self.mover = mover
        self.player = player
        self.key = key

    def check_bullet(self):
        if pyxel.btn(self.key) and pyxel.frame_count - self.last > self.delay:
            self.last = pyxel.frame_count
            return Bullet(self.player, self.mover.direction)
        return None

class Mover:
    def __init__(self, player, left, right, top, bottom, horizontal_direction) -> None:
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.horizontal_direction = horizontal_direction
        self.direction = Direction.RIGHT if horizontal_direction == HorizontalDirection.RIGHT else Direction.LEFT
        self.player = player
        self.player.looking_horizontal_dir = horizontal_direction

    def update(self):
        rect = self.player.bounds()
        dir = None
        if pyxel.btn(self.left):
            dir = Direction.LEFT
            self.horizontal_direction = HorizontalDirection.LEFT
            rect.move(x = -1)
        if pyxel.btn(self.right):
            dir = Direction.RIGHT
            self.horizontal_direction = HorizontalDirection.RIGHT
            rect.move(x = 1)
        if pyxel.btn(self.top):
            dir = Direction.TOP
            rect.move(y = -1)
        if pyxel.btn(self.bottom):
            dir = Direction.BOTTOM
            rect.move(y = 1)
        if VIEWPORT.contains(rect) and dir is not None:
            self.direction = dir
            self.player.x = rect.x
            self.player.y = rect.y

class SwordPainter:
    def __init__( \
            self, player, mover, sword_system, \
            player_sword_joint_point, \
            sword_rect_normal, sword_joint_norlam_point, \
            sword_rect_hit, sword_joint_hit_point) -> None:
        self.player = player
        self.mover = mover
        self.sword_system = sword_system
        self.player_sword_joint_point = player_sword_joint_point
        self.sword_rect_normal = sword_rect_normal
        self.sword_joint_norlam_point = sword_joint_norlam_point
        self.sword_rect_hit = sword_rect_hit
        self.sword_joint_hit_point = sword_joint_hit_point
    
    def draw(self):
        match self.sword_system.state:
            case SwordState.NONE:
                pyxel.blt(self.player.x + self.player_sword_joint_point.x - self.sword_joint_norlam_point.x, 
                          self.player.y + self.player_sword_joint_point.y - self.sword_joint_norlam_point.y,
                          0,
                          self.sword_rect_normal.x, self.sword_rect_normal.y, 
                          self.sword_rect_normal.w if self.mover.horizontal_direction == HorizontalDirection.RIGHT else -self.sword_rect_normal.w,
                          self.sword_rect_normal.y)
            case SwordState.HITTING:
                pass

class StaticPlayerPainter:
    def __init__(self, player, mover, player_rect) -> None:
        self.player = player
        self.mover = mover
        self.player_rect = player_rect
    
    def draw(self):
        pyxel.blt(self.player.x, self.player.y, 
                  0,
                  self.player_rect.x, self.player_rect.y, 
                  self.player_rect.w if self.mover.horizontal_direction == HorizontalDirection.RIGHT else -self.player_rect.w,
                  self.player_rect.y)

class Player:
    def __init__(self, x, y, name) -> None:
        self.x = x
        self.y = y
        self.name = name
    
    def bounds(self):
        return Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)

class App:
    def __init__(self):
        pyxel.init(SIZE, SIZE)
        pyxel.load("assets/players.pyxres")
        game_scene = GameScene()
        self.scene_router = SceneRouter(game_scene)
        pyxel.run(self.update, self.draw)

    def update(self):
        self.scene_router.update()

    def draw(self):
        pyxel.cls(0)
        self.scene_router.draw()

App()

# TODO:
# draw sword slice
# hit with sword