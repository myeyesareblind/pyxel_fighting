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

    def intersects(self, other):
        return Rect.one_dimension_intersects([self.x, self.w], [other.x, other.w]) and\
        Rect.one_dimension_intersects([self.y, self.h], [other.y, other.h])

    @staticmethod
    def one_dimension_intersects(x1, x2):
        left = x1
        right = x2
        if right[0] < left[0]:
            t = left
            left = right
            right = t
        return (left[0] + left[1]) >= right[0]
    
    def move(self, x = None, y = None):
        if x is not None:
            self.x += x
        if y is not None:
            self.y += y
    
    def __str__(self) -> str:
        return "[{}-{},{}x{}]".format(self.x,self.y,self.w,self.h)

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
        self.invis_systems = []

        p1 = Player(SIZE - PLAYER_SIZE, 0, 13, PLAYER_SIZE, "Kiril")

        p2 = Player(0, 0, PLAYER_SIZE, PLAYER_SIZE, "Max")

        self.players.append(p1)
        self.players.append(p2)
        p1_mover = Mover(p1, pyxel.KEY_LEFT, pyxel.KEY_RIGHT, pyxel.KEY_UP, pyxel.KEY_DOWN, HorizontalDirection.LEFT)
        self.movers.append(p1_mover)
        p2_mover = Mover(p2, pyxel.KEY_A, pyxel.KEY_D, pyxel.KEY_W, pyxel.KEY_S, HorizontalDirection.RIGHT)
        self.movers.append(p2_mover)

        p1_painter = StaticPlayerPainter(p1, p1_mover, Rect(0,0,13,16))
        p2_painter = StaticPlayerPainter(p2, p2_mover, Rect(0,16,16,16))
        p1_sword_frame_calc = SwordFrameCalculator(p1, p1_mover, Point(13, 13), Rect(13, 2, 3, 14), Point(0, 11), Rect(29,11, 15, 5), Point(0, 3))
        p1_sword = SwordSystem(p1, p1_mover, p1_sword_frame_calc, pyxel.KEY_L)
        p1_sword_painter = SwordPainter(p1, p1_mover, p1_sword, p1_sword_frame_calc, Rect(13, 2, 3, 14), Rect(29,11, 15, 5))
        p1_invis = InvisSystem(p1, pyxel.KEY_K)
        self.invis_systems.append(p1_invis)
        self.painters.append(p1_painter)
        self.painters.append(p2_painter)
        self.painters.append(p1_sword_painter)

        # self.shot_producers.append(ShotProducer(p1, p1_mover, pyxel.KEY_1))
        self.shot_producers.append(ShotProducer(p2, p2_mover, pyxel.KEY_1))

        self.sword_systems.append(p1_sword)

    def update(self):
        for shot_producer in self.shot_producers:
            bullet = shot_producer.check_bullet()
            if bullet is not None:
                self.bullets.append(bullet)

        for mover in self.movers:
            mover.update()
        
        for i in self.invis_systems:
            i.update()

        for b in self.bullets:
            b.update()
            hit_player = b.check_hit(self.players)
            if hit_player is not None:
                self.players.remove(hit_player)
                return EndScene(self.players[0])
        
        self.bullets = [b for b in self.bullets if VIEWPORT.contains(b.bounds())]

        for s in self.sword_systems:
            s.update()
            self.bullets = [b for b in self.bullets if not s.hits(b.bounds())]
            for p in self.players:
                if p == s.player:
                    continue
                if s.hits(p.bounds()):
                    self.players.remove(p)
                    return EndScene(self.players[0])

        return self
    
    def draw(self):
        for b in self.bullets:
            b.draw()

        for painter in self.painters:
            painter.draw()
class InvisState(Enum):
    NONE = 1
    INVIS = 2
class InvisSystem:
    def __init__(self, player, key) -> None:
        self.player = player
        self.key = key
        self.state = InvisState.NONE
        self.delay = 30
        self.last = -1000000
        self.length = 20

    def update(self):
        match self.state:
            case InvisState.NONE:
                self.player.hidden = False
                if pyxel.btn(self.key) and pyxel.frame_count - self.last > self.delay:
                    self.state = InvisState.INVIS
                    self.start_frame = 0
            case InvisState.INVIS:
                self.player.hidden = True
                self.start_frame += 1
                if self.start_frame >= self.length:
                    self.state = InvisState.NONE
                    self.last = pyxel.frame_count

class SwordSystem:
    def __init__(self, player, mover, frame_calculator, key) -> None:
        self.player = player
        self.mover = mover
        self.frame_calculator = frame_calculator
        self.key = key
        self.state = SwordState.NONE
        self.delay = 30
        self.last = -1000000
        self.length = 15
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
    
    def hits(self, frame):
        match self.state:
            case SwordState.NONE:
                return False
            case SwordState.HITTING:
                start = self.frame_calculator.getNormalFrame()
                end = self.frame_calculator.getHitFrame()
                sword_rect = Rect(
                    min(start.x, end.x),
                    min(start.y, end.y),
                    max(start.w, end.w),
                    max(start.h, end.h)
                )
                return sword_rect.intersects(frame)

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

class SwordFrameCalculator:
    def __init__(self, player, mover,
            player_sword_joint_point,
            sword_rect_normal, sword_joint_norlam_point,
            sword_rect_hit, sword_joint_hit_point) -> None:
        self.player = player
        self.mover = mover
        self.player_sword_joint_point = player_sword_joint_point
        self.sword_rect_normal = sword_rect_normal
        self.sword_joint_norlam_point = sword_joint_norlam_point
        self.sword_rect_hit = sword_rect_hit
        self.sword_joint_hit_point = sword_joint_hit_point

    def right_offset(self):
        return 0 if self.mover.horizontal_direction == HorizontalDirection.RIGHT else self.player.bounds().w

    def getNormalX(self):
        sword_offset = \
        0 if self.mover.horizontal_direction == HorizontalDirection.RIGHT \
        else self.sword_rect_normal.w - self.sword_joint_norlam_point.x
        
        x = self.player.x\
        + self.player_sword_joint_point.x - self.right_offset()\
        - self.sword_joint_norlam_point.x - sword_offset
        return x
    
    def getNormalFrame(self):
        return Rect(self.getNormalX(), self.getNormalY(), self.sword_rect_normal.w, self.sword_rect_normal.h)
    
    def getNormalY(self):
        return self.player.y + self.player_sword_joint_point.y - self.sword_joint_norlam_point.y
    
    def getHitX(self):
        sword_offset = \
        0 if self.mover.horizontal_direction == HorizontalDirection.RIGHT \
        else self.sword_rect_hit.w - self.sword_joint_hit_point.x

        return self.player.x\
            + self.player_sword_joint_point.x - self.right_offset()\
            - self.sword_joint_hit_point.x  - sword_offset

    def getHitY(self):
        return self.player.y + self.player_sword_joint_point.y - self.sword_joint_hit_point.y

    def getHitFrame(self):
        return Rect(self.getHitX(), self.getHitY(), self.sword_rect_hit.w, self.sword_rect_hit.h)

class SwordPainter:
    def __init__(self, player, mover, sword_system,
            sword_frame_calculator,
            sword_rect_normal,
            sword_rect_hit) -> None:
        self.player = player
        self.mover = mover
        self.sword_system = sword_system
        self.sword_frame_calculator = sword_frame_calculator
        self.sword_rect_normal = sword_rect_normal
        self.sword_rect_hit = sword_rect_hit
    
    def draw(self):
        if not self.player.hidden:
            match self.sword_system.state:
                case SwordState.NONE:
                    self.draw_normal_sword()
                case SwordState.HITTING:
                    pyxel.dither(0.5)
                    if self.sword_system.hit_frame % 2 == 0:
                        self.draw_hit_sword()
                        self.draw_normal_sword()
                    else:
                        self.draw_normal_sword()
                        self.draw_hit_sword()
            pyxel.dither(1)
    
    def draw_normal_sword(self):
        pyxel.blt(
            self.sword_frame_calculator.getNormalX(),
            self.sword_frame_calculator.getNormalY(),
            0,
            self.sword_rect_normal.x, self.sword_rect_normal.y, 
            self.sword_rect_normal.w if self.mover.horizontal_direction == HorizontalDirection.RIGHT else -self.sword_rect_normal.w,
            self.sword_rect_normal.h)
    
    def draw_hit_sword(self):
        pyxel.blt(
            self.sword_frame_calculator.getHitX(),
            self.sword_frame_calculator.getHitY(),
            0,
            self.sword_rect_hit.x, self.sword_rect_hit.y, 
            self.sword_rect_hit.w if self.mover.horizontal_direction == HorizontalDirection.RIGHT else -self.sword_rect_hit.w,
            self.sword_rect_hit.h)


class StaticPlayerPainter:
    def __init__(self, player, mover, player_rect) -> None:
        self.player = player
        self.mover = mover
        self.player_rect = player_rect
    
    def draw(self):
        if not self.player.hidden:
            pyxel.blt(self.player.x, self.player.y, 
                    0,
                    self.player_rect.x, self.player_rect.y, 
                    self.player_rect.w if self.mover.horizontal_direction == HorizontalDirection.RIGHT else -self.player_rect.w,
                    self.player_rect.h)

class Player:
    def __init__(self, x, y, w, h, name) -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.name = name
        self.hidden = False
    
    def bounds(self):
        return Rect(self.x, self.y, self.w, self.h)

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
# invis
# trees