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
        return self

    def draw(self):
        pyxel.text(SIZE / 2, SIZE / 2, "{} is winner!".format(self.winner.name), pyxel.COLOR_PINK)

class GameScene:
    players = []
    bullets = []
    shot_producers = []

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
                print("make {}", bullet)
                self.bullets.append(bullet)

        for b in self.bullets:
            b.update()
            hit_player = b.check_hit(self.players)
            if hit_player is not None:
                print("hit {}", hit_player)
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
        k = Kiril()
        m = Max()
        self.game_scene = GameScene()
        self.game_scene.install_player(k)
        self.game_scene.install_player(m)
        self.game_scene.install_shot_producer(k.shot_producer)
        self.game_scene.install_shot_producer(m.shot_producer)
        self.scene_router = SceneRouter(self.game_scene)
        pyxel.run(self.update, self.draw)

    def update(self):
        self.scene_router.update()

    def draw(self):
        pyxel.cls(0)
        self.scene_router.draw()

class Direction(Enum):
    LEFT = 1
    RIGHT = 2

class Bullet:
    def __init__(self, player, direction) -> None:
        self.x = player.x - 1 if direction == Direction.LEFT else player.x + PLAYER_SIZE
        self.y = player.y + PLAYER_SIZE / 2
        self.direction = direction
        self.player = player
    
    def update(self):
        self.x += -1 if self.direction == Direction.LEFT else 1
    
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
    delay = 20
    last = -1000000
    def __init__(self, player, key, direction) -> None:
        self.player = player
        self.key = key
        self.direction = direction

    def check_bullet(self):
        if pyxel.btn(self.key) and pyxel.frame_count - self.last > self.delay:
            self.last = pyxel.frame_count
            return Bullet(self.player, self.direction)
        return None

class Mover:
    def __init__(self, target, left, right, top, bottom) -> None:
        self.target = target
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom

    def update(self):
        rect = self.target.bounds()
        if pyxel.btn(self.left):
            rect.move(x = -1)
        if pyxel.btn(self.right) and self.target.y < SIZE - 1:
            rect.move(x = 1)
        if pyxel.btn(self.top) and self.target.y > 0:
            rect.move(y = -1)
        if pyxel.btn(self.bottom) and self.target.y < SIZE - 1:
            rect.move(y = 1)
        if VIEWPORT.contains(rect):
            self.target.x = rect.x
            self.target.y = rect.y

class Player:
    x = 0
    y = 0
    def __init__(self, x, y, mover) -> None:
        self.x = x
        self.y = y
        self.mover = mover
    
    def bounds(self):
        return Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)
    
    def update(self):
        self.mover.update()
    
    def draw(self):
        pass

class Kiril(Player):
    name = "Kiril"
    def __init__(self) -> None:
        self.shot_producer = ShotProducer(self, pyxel.KEY_1, Direction.RIGHT)
        super().__init__(0, SIZE-PLAYER_SIZE, 
                         Mover(self, pyxel.KEY_A, pyxel.KEY_D, pyxel.KEY_W, pyxel.KEY_S))

    def draw(self):
        super().draw()
        pyxel.blt(self.x, self.y, 0, 0, 0, PLAYER_SIZE, PLAYER_SIZE)

class Max(Player):
    name = "Max"
    def __init__(self) -> None:
        self.shot_producer = ShotProducer(self, pyxel.KEY_0, Direction.LEFT)
        super().__init__(SIZE-PLAYER_SIZE, SIZE-PLAYER_SIZE, 
                        Mover(self, pyxel.KEY_LEFT, pyxel.KEY_RIGHT, pyxel.KEY_UP, pyxel.KEY_DOWN))

    def draw(self):
        super().draw()
        pyxel.blt(self.x, self.y, 0, 0, PLAYER_SIZE, -PLAYER_SIZE, PLAYER_SIZE)


App()

# TODO:
# collision detection for bullet
# draw sword slice