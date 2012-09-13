import random


class AI(object):
    MIN_DISTANCE = 700

    def __init__(self, char):
        self.char = char
        self.world = char.world

    def update(self, dt):
        hero = self.world.hero

        # If hero is not in range, move towards him
        if random.random() < 0.5:
            self.defend(hero, self.char)
        else:
            self.attack(hero, self.char)

    def defend(self, hero, lawman):
        """A simple defensive strategy"""
        # locate the hero: distance, vector
        hero_pos = hero.pos
        hero_hitlist = hero.hitlist
        self_pos = lawman.pos
        distance = self_pos.distance_to(hero_pos)

        # Face the right direction
        if (self_pos - hero_pos).x > 0:
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
        hero_pos = hero.pos
        # hero_hitlist = hero.hitlist
        self_pos = lawman.pos
        # distance = self_pos.distance_to(hero_pos)
        # Face the right direction
        if (self_pos - hero_pos).x > 0:
            # Hero is on the left
            lawman.face_left()
        else:
            # Hero is on the right
            lawman.face_right()

        # Attack:
        # 1. If hero is in direct range shoot
        # hitlist = lawman.hitlist
        lawman.shoot()

    def move(self, hero, lawman):
        # Motion:
        # 1. If an object is blocking, go past it
        # 2. Shoot and hide if hero is right in front
        return

