import random
import pyglet
from operator import itemgetter
from vector import v
from wild import RIGHT, LEFT
from wild import Outlaw, Crate
from game import FPS


class AI(object):
    MIN_DISTANCE = 500
    DESTINATION_REACHED = 70

    def __init__(self, char):
        self.char = char
        self.world = char.world
        self.strategy = None
        self.strategy_time = 0

    def direction_to(self, pos):
        if (self.char.pos - pos).x > 0:
            return LEFT
        else:
            return RIGHT

    def face_towards(self, pos):
        """Face towards a target"""
        if self.direction_to(pos) == LEFT:
            # Hero is on the left
            self.char.face_left()
        else:
            # Hero is on the right
            self.char.face_right()

    def is_close_by(self, pos):
        if self.char.pos.distance_to(pos) < AI.DESTINATION_REACHED:
            return True
        else:
            return False

    def run_towards(self, pos):
        if not self.is_close_by(pos):
            if self.direction_to(pos) == LEFT:
                self.char.left()
            else:
                self.char.right()

    def run_from(self, pos):
        if self.direction_to(pos) == LEFT:
            self.char.right()
        else:
            self.char.left()

    def find_hideable_objects(self):
        hideable = []
        for obj in self.world.objects:
            if isinstance(obj, Crate):  # or isinstance(obj, Table):
                d = self.pos.distance_to(obj.body.pos)
                hideable.append((obj, d))
        return sorted(hideable, key=itemgetter(1))

    def jump_over_object(self, obj):
        dir = self.direction_to(obj.body.pos)
        if dir == RIGHT:
            destination = obj.body.pos + v(obj.body.rect.w + 100, 0)
        else:
            destination = obj.body.pos - v(60, 0)
        self.char.jump()
        self.run_towards(destination)

    def pick_strategy(self):
        """Choose a strategy based on changing circumstances"""
        self.distance = self.pos.distance_to(self.target_pos)

        # Don't act until hero is in range
        if self.distance > self.MIN_DISTANCE or\
                not isinstance(self.target, Outlaw):
            self.strategy = None
            self.strategy_time = 0
            return

        # If we don't have a previously chosen strategy choose one
        if not self.strategy or self.strategy_time % 30 == 0:
            self.strategy_time = 1
            choice = random.random()
            if choice < 0.3:
                self.strategy = self.strategy_shoot_first
            elif choice < 0.5:
                self.strategy = self.strategy_reactive_defense
            else:
                self.strategy = self.strategy_hide

    def update(self, dt):
        """Update method called at AI refresh rate"""
        self.target = self.world.hero
        self.target_pos = self.target.pos
        self.pos = self.char.pos
        self.pick_strategy()

    def update_frame(self, dt):
        """Update method called every frame"""
        if not self.strategy or self.strategy_time < 1:
            return
        self.target_pos = self.target.pos
        self.pos = self.char.pos
        self.strategy()
        self.strategy_time += 1

    def strategy_reactive_defense(self):
        """Defensive strategy to react to opponent's actions"""
        self.face_towards(self.target_pos)

        # Defence: if direct line of shooting
        # 1. Crouch if hero is standing or jumping and preparing to shoot
        if self.target.jumping:
            self.char.crouch()
        # 2. Jump if hero is crouching
        elif self.target.crouching:
            self.char.jump()

    def strategy_shoot_first(self):
        """A simple attack strategy - keep shooting"""
        self.face_towards(self.target_pos)
        # Attack:
        # 1. If hero is in direct range shoot
        if not self.target.crouching and not self.target.jumping:
            self.char.shoot()

    def strategy_hide(self):
        """Defensive strategy to hide behind something blocking"""
        # Find the nearest hide-able object and hide
        hideable = self.find_hideable_objects()
        if not hideable:
            self.pick_strategy()
            return
        obj, dist = hideable[0]
        if self.is_close_by(obj.body.pos):
            if self.direction_to(obj.body.pos) !=\
                    self.direction_to(self.target.pos):
                self.jump_over_object(obj)
            else:
                self.char.crouch()
                # objective reached, clear strategy
                # self.strategy = None
        else:
            self.run_towards(obj.body.pos)

