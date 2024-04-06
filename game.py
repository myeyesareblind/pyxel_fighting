import pyxel
from enum import Enum

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

SIZE = 256
PLAYER_SIZE = 16
VIEWPORT = Rect(0, 0, SIZE, SIZE)

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

        p1 = Player(0, 0, 
                    "Kiril",
                    Mover(pyxel.KEY_A, pyxel.KEY_D, pyxel.KEY_W, pyxel.KEY_S, HorizontalDirection.RIGHT), 
                    PlayerTile(0, 0))
        p2 = Player(SIZE - PLAYER_SIZE, 0, 
                    "Max",
                    Mover(pyxel.KEY_LEFT, pyxel.KEY_RIGHT, pyxel.KEY_UP, pyxel.KEY_DOWN, HorizontalDirection.LEFT), 
                    PlayerTile(0, PLAYER_SIZE))

        self.install_player(p1)
        self.install_player(p2)
        self.install_shot_producer(ShotProducer(p1, pyxel.KEY_1))
        self.install_shot_producer(ShotProducer(p2, pyxel.KEY_RETURN))

    def install_player(self, player):
        self.players.append(player)

    def install_bullet(self, bullet):
        self.bullets.append(bullet)

    def install_shot_producer(self, shot_producer):
        self.shot_producers.append(shot_producer)
    
    def update(self):
        for shot_producer in self.shot_producers:
            bullet = shot_producer.check_bullet()
            if bullet is not None:
                self.bullets.append(bullet)

        for b in self.bullets:
            b.update()
            hit_player = b.check_hit(self.players)
            if hit_player is not None:
                self.players.remove(hit_player)
                return EndScene(self.players[0])
        
        self.bullets = [b for b in self.bullets if VIEWPORT.contains(b.bounds())]

        for p in self.players:
            p.update()

        return self
    
    def draw(self):
        for b in self.bullets:
            b.draw()

        for p in self.players:
            p.draw()

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

class Direction(Enum):
    LEFT = 1
    RIGHT = 2
    TOP = 3
    BOTTOM = 4

class HorizontalDirection(Enum):
    LEFT = 1
    RIGHT = 2

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
    def __init__(self, player, key) -> None:
        self.delay = 20
        self.last = -1000000
        self.player = player
        self.key = key

    def check_bullet(self):
        if pyxel.btn(self.key) and pyxel.frame_count - self.last > self.delay:
            self.last = pyxel.frame_count
            return Bullet(self.player, self.player.mover.direction)
        return None

class Mover:
    def __init__(self, left, right, top, bottom, horizontal_direction) -> None:
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.horizontal_direction = horizontal_direction
        self.direction = Direction.RIGHT if horizontal_direction == HorizontalDirection.RIGHT else Direction.LEFT

    def update(self):
        rect = self.target.bounds()
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
            self.target.x = rect.x
            self.target.y = rect.y

class PlayerTile:
    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y
    
    def draw(self, x, y, horizontal_direction):
        pyxel.blt(x, y, 
                  0,
                  self.x, self.y, 
                  PLAYER_SIZE if horizontal_direction == HorizontalDirection.RIGHT else -PLAYER_SIZE,
                  PLAYER_SIZE)

class Player:
    def __init__(self, x, y, name, mover, tile) -> None:
        self.x = x
        self.y = y
        self.name = name
        self.mover = mover
        self.mover.target = self
        self.tile = tile
    
    def bounds(self):
        return Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)
    
    def update(self):
        self.mover.update()
    
    def draw(self):
        self.tile.draw(self.x, self.y, self.mover.horizontal_direction)

App()

# TODO:
# refactor player - P1 looks to the wrong side
# look in different directions
# shot in different directions
# draw sword slice