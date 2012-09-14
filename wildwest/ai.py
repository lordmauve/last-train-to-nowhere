import random


class AI(object):
    MIN_DISTANCE = 500

    def __init__(self, char):
        self.char = char
        self.world = char.world

    def update(self, dt):
        hero = self.world.hero
        self.hero_pos = hero.pos
        # locate the hero: distance, vector
        self.hero_hitlist = hero.hitlist

        self.pos = self.char.pos
        self.distance = self.pos.distance_to(self.hero_pos)

        # Don't act until hero is in range
        if self.distance > self.MIN_DISTANCE:
            return

        # If hero is not in range, move towards him
        if random.random() < 0.8:
            self.defend(hero, self.char)
        else:
            self.attack(hero, self.char)

    def defend(self, hero, lawman):
        """A simple defensive strategy"""

        # Face the right direction
        if (self.pos - self.hero_pos).x > 0:
            # Hero is on the left
            lawman.face_left()
        else:
            # Hero is on the right
            lawman.face_right()

        # Defence: if direct line of shooting
        # 1. Crouch if hero is standing or jumping and preparing to shoot
        if hero.jumping:
            lawman.crouch()
        # 2. Jump if hero is crouching
        elif hero.crouching:
            lawman.jump()

    def attack(self, hero, lawman):
        """A simple attack strategy"""
        # Face the right direction
        if (self.pos - self.hero_pos).x > 0:
            # Hero is on the left
            lawman.face_left()
        else:
            # Hero is on the right
            lawman.face_right()

        # Attack:
        # 1. If hero is in direct range shoot
        # hitlist = lawman.hitlist
        if not hero.crouching and not hero.jumping:
            lawman.shoot()

    def move(self, hero, lawman):
        # Motion:
        # 1. If an object is blocking, go past it
        # 2. Shoot and hide if hero is right in front
        return

