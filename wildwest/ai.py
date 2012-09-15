import random
from operator import itemgetter
from vector import v
import pyglet
from geom import Segment, Rect
from wild import RIGHT, LEFT
from wild import Outlaw, Crate
from physics import StaticBody


class AI(object):
    MIN_DISTANCE = 500
    DESTINATION_REACHED = 100

    def __init__(self, char):
        self.char = char
        self.world = char.world
        self.strategy = None
        self.strategy_time = 0
        self.jumping_over = None
        self.shot = False

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
        if abs(self.char.pos.distance_to(pos)) < AI.DESTINATION_REACHED:
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

    def is_outlaw_shootable(self):
        hitlist = self.char.hitlist
        if hitlist and isinstance(hitlist[0][1], Outlaw):
            return True
        return False

    def shoot_bullet(self, dt):
        self.char.shoot()

    def shoot(self):
        if self.is_outlaw_shootable():  # and self.strategy_time % 5 == 0:
            pyglet.clock.schedule_once(self.shoot_bullet, 0.3)

    def crouch_later(self, dt):
        self.char.crouch()

    def crouch(self):
        pyglet.clock.schedule_once(self.crouch_later, 0.1)

    def objects_in_direction(self, direction):
        p1 = self.char.body.pos + v(50 * direction, 50)
        p2 = p1 + v(1000, 0) * direction
        seg = Segment(p1, p2)
        hit = self.world.physics.ray_query(seg)
        return hit

    def all_objects_in_range(self, range=1000):
        objects_left = self.objects_in_direction(LEFT)
        objects_right = self.objects_in_direction(RIGHT)
        all_objects = objects_left + objects_right
        filtered_objects = [(obj, dist) for dist, obj in all_objects if abs(dist) < range]
        # print 'filtered_objects:', filtered_objects
        return sorted(filtered_objects, key=itemgetter(1))

    def find_hideable_objects(self):
        hideable = []
        for obj, dist in self.all_objects_in_range():
            if not isinstance(obj, Outlaw):  # or isinstance(obj, Table):
                # print obj, dir(obj)
                if isinstance(obj, Rect):
                    obj._pos = obj.points[0]
                if hasattr(obj, 'body'):
                    obj._pos = obj.body.pos
                hideable.append((obj, abs(dist)))
        return sorted(hideable, key=itemgetter(1))

    def jump_over_object(self, pos, w):
        dir = self.direction_to(pos)
        if dir == RIGHT:
            destination = pos + v(w + 100, 0)
        else:
            destination = pos - v(60, 0)
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
            if choice < 0.1:
                self.strategy = self.strategy_shoot_first
            elif choice < 0.3:
                self.strategy = self.strategy_lie_in_wait
            elif choice < 0.6:
                self.strategy = self.strategy_shoot_and_duct
            elif choice < 0.75:
                self.strategy = self.strategy_reactive_defense
            else:
                self.strategy = self.strategy_hide
            # print 'strategy picked:', self.strategy
            # self.strategy = self.strategy_reactive_defense

    def update(self, dt):
        """Update method called at AI refresh rate"""
        if self.world.hero.dead or self.char.dead:
            return
        self.target = self.world.hero
        self.target_pos = self.target.pos
        self.pos = self.char.pos
        self.pick_strategy()

    def update_frame(self, dt):
        """Update method called every frame"""
        if self.char.dead:
            return
        if not self.strategy or self.strategy_time < 1 or self.target.dead:
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
        if not self.target.crouching:
            self.crouch()
        # 2. Jump if hero is crouching
        elif self.target.crouching:
            self.char.jump()
        # 3. Shoot from time to time
        if self.strategy_time % 10 == 0:
            self.shoot()

    def strategy_shoot_first(self):
        """A simple attack strategy - keep shooting"""
        self.face_towards(self.target_pos)
        # Attack:
        # 1. If hero is in direct range shoot
        if not self.target.crouching and not self.target.jumping:
            if self.strategy_time % 4 == 0:
                self.shoot()

    def strategy_shoot_and_duct(self):
        self.face_towards(self.target_pos)
        if self.shot:
            self.crouch()
            if self.strategy_time > 10:
                self.shot = False
        if not self.target.crouching and not self.target.jumping:
            if self.char.crouching:
                return
            self.shoot()
            self.shot = True

    def strategy_lie_in_wait(self):
        self.face_towards(self.target_pos)
        hitlist = self.char.hitlist
        if not hitlist:
            return
        if isinstance(hitlist[0][1], Outlaw):
            if self.strategy_time % 4 == 0:
                self.shoot()
            else:
                self.crouch()
        else:
            self.crouch()

    def object_width(self, obj):
        w = None
        if hasattr(obj, 'body'):
            w = obj.body.rect.w
        if isinstance(obj, Rect):
            w = obj.w
        return w

    def object_left(self, obj):
        """Get a point to the left of the object"""

    def strategy_hide(self):
        """Defensive strategy to hide behind something blocking"""
        # Find the nearest hide-able object and hide
        hideable = self.find_hideable_objects()
        # print 'hideable objects:', hideable
        if not hideable:
            self.pick_strategy()
            return
        obj, dist = hideable[0]
        if self.is_close_by(obj._pos):
            # print 'object is close by', obj
            w = self.object_width(obj)
            if not w:
                w = 100

            if self.direction_to(obj._pos) !=\
                    self.direction_to(self.target.pos):
                # print 'obj close_by but need to jump. w=', w
                self.jump_over_object(obj._pos, w)
                self.jumping_over = obj
            else:
                # print 'obj close by: crouching'
                self.crouch()
                self.face_towards(self.target_pos)
                self.jumping_over = None
                self.strategy = self.strategy_lie_in_wait
        else:
            if self.jumping_over:
                obj = self.jumping_over
            # print 'run towards obj:', obj
            self.run_towards(obj._pos)
