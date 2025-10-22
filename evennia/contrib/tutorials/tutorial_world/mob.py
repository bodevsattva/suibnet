"""
Neo Eden NPC AIs — Mobile Agents and Aggressive Enforcers
Cyberpunk re-theme of the Evennia tutorial mobs.

Implements a basic autonomous drone / enforcer unit with a
rudimentary state machine controlling patrol, pursuit, and combat.
"""

import random
from evennia import TICKER_HANDLER, CmdSet, Command, logger, search_object
from . import objects as tut_objects


# ------------------------------------------------------------
# Administrative toggle commands
# ------------------------------------------------------------

class CmdMobOnOff(Command):
    """
    Activate/deactivate a drone or AI mob.

    Usage:
        mobon <unit>
        moboff <unit>

    Turns a mobile unit online (active) or offline (dormant).
    """

    key = "mobon"
    aliases = "moboff"
    locks = "cmd:superuser()"

    def func(self):
        if not self.args:
            self.caller.msg("Usage: mobon||moboff <unit>")
            return
        mob = self.caller.search(self.args)
        if not mob:
            return
        if self.cmdstring == "mobon":
            mob.set_alive()
        else:
            mob.set_dead()


class MobCmdSet(CmdSet):
    """Holds the admin command controlling the drone."""
    def at_cmdset_creation(self):
        self.add(CmdMobOnOff())


# ------------------------------------------------------------
# Mobile NPC class
# ------------------------------------------------------------

class Mob(tut_objects.TutorialObject):
    """
    Autonomous mobile NPC for Neo Eden.

    Core behaviors (all optional flags):

        patrolling: Moves randomly between connected zones.
        aggressive: Attacks nearby players with its equipped weapon.
        hunting:    Pursues fleeing targets between rooms.
        immortal:   Cannot take damage (for cinematic encounters).

    Visual feedback and messages have been re-themed to fit
    cyberpunk drones and enforcer archetypes.
    """

    # ---------------------------------------
    # Init and Creation
    # ---------------------------------------

    def at_init(self):
        """Restore runtime AI state after reboot."""
        self.ndb.is_patrolling = self.db.patrolling and not self.db.is_dead
        self.ndb.is_attacking = False
        self.ndb.is_hunting = False
        self.ndb.is_immortal = self.db.immortal or self.db.is_dead

    def at_object_creation(self):
        """Called once when created."""
        self.cmdset.add(MobCmdSet, persistent=True)

        # Behavioral flags
        self.db.patrolling = True
        self.db.aggressive = True
        self.db.immortal = False
        self.db.is_dead = True

        # Damage resistance (non-plasma weapons)
        self.db.damage_resistance = 100.0

        # Timings (seconds per tick)
        self.db.patrolling_pace = 6
        self.db.aggressive_pace = 2
        self.db.hunting_pace = 1
        self.db.death_pace = 90

        # Track last ticker to allow smooth state transitions
        self.db.last_ticker_interval = None

        # Descriptions for states
        self.db.desc_alive = (
            "A hovering |csecurity drone|n hums here, its optics glowing faint blue."
        )
        self.db.desc_dead = "A heap of burnt circuitry and shattered plating."

        # Health
        self.db.full_health = 25
        self.db.health = 25

        # defeat behavior
        self.db.send_defeated_to = "recovery_bay"
        self.db.defeat_msg = "|rSYSTEM FAILURE:|n Your HUD flickers and fades as you collapse."
        self.db.defeat_msg_room = "%s’s neural link overloads and they drop to the ground."
        self.db.weapon_ineffective_msg = (
            "Your weapon’s rounds spark harmlessly off reinforced plating!"
        )

        # messages
        self.db.death_msg = f"{self.key} sparks violently, collapsing into a pool of molten alloy."
        self.db.hit_msg = f"{self.key} jerks as bullets ricochet off its chassis!"
        self.db.irregular_msgs = [
            "The drone scans the area with a crimson beam.",
            "A low servo whine echoes from the drone.",
            "The drone repositions, whirring softly.",
        ]

        self.db.tutorial_info = (
            "This is a cybernetic drone AI — it patrols, hunts, and engages intruders autonomously."
        )

    # ---------------------------------------
    # Ticker / State helpers
    # ---------------------------------------

    def _set_ticker(self, interval, hook_key, stop=False):
        idstring = "neoeden_mob"
        last_interval = self.db.last_ticker_interval
        last_hook_key = self.db.last_hook_key

        if last_interval and last_hook_key:
            TICKER_HANDLER.remove(
                interval=last_interval, callback=getattr(self, last_hook_key), idstring=idstring
            )

        self.db.last_ticker_interval = interval
        self.db.last_hook_key = hook_key

        if not stop and interval and hook_key:
            TICKER_HANDLER.add(
                interval=interval, callback=getattr(self, hook_key), idstring=idstring
            )

    def _find_target(self, location):
        """Return first non-superuser Character in room."""
        targets = [
            obj for obj in location.contents_get(exclude=self)
            if obj.has_account and not obj.is_superuser
        ]
        return targets[0] if targets else None

    # ---------------------------------------
    # State setters
    # ---------------------------------------

    def set_alive(self, *args, **kwargs):
        """Boot online."""
        self.db.health = self.db.full_health
        self.db.is_dead = False
        self.db.desc = self.db.desc_alive
        self.ndb.is_immortal = self.db.immortal
        self.ndb.is_patrolling = self.db.patrolling
        if not self.location:
            self.move_to(self.home)
        if self.db.patrolling:
            self.start_patrolling()

    def set_dead(self):
        """Shutdown unit; schedule reboot."""
        self.db.is_dead = True
        self.location = None
        self.ndb.is_patrolling = False
        self.ndb.is_attacking = False
        self.ndb.is_hunting = False
        self.ndb.is_immortal = True
        self._set_ticker(self.db.death_pace, "set_alive")

    def start_idle(self):
        self._set_ticker(None, None, stop=True)

    def start_patrolling(self):
        """Begin idle patrol loop."""
        if not self.db.patrolling:
            self.start_idle()
            return
        self._set_ticker(self.db.patrolling_pace, "do_patrol")
        self.ndb.is_patrolling = True
        self.ndb.is_hunting = False
        self.ndb.is_attacking = False
        self.db.health = self.db.full_health

    def start_hunting(self):
        if not self.db.hunting:
            self.start_patrolling()
            return
        self._set_ticker(self.db.hunting_pace, "do_hunt")
        self.ndb.is_patrolling = False
        self.ndb.is_hunting = True
        self.ndb.is_attacking = False

    def start_attacking(self):
        if not self.db.aggressive:
            self.start_hunting()
            return
        self._set_ticker(self.db.aggressive_pace, "do_attack")
        self.ndb.is_patrolling = False
        self.ndb.is_hunting = False
        self.ndb.is_attacking = True

    # ---------------------------------------
    # Behavior loops
    # ---------------------------------------

    def do_patrol(self, *args, **kwargs):
        """Patrol state tick."""
        if random.random() < 0.02 and self.db.irregular_msgs:
            self.location.msg_contents(random.choice(self.db.irregular_msgs))

        if self.db.aggressive:
            target = self._find_target(self.location)
            if target:
                self.start_attacking()
                return

        exits = [exi for exi in self.location.exits if exi.access(self, "traverse")]
        if exits:
            exit = random.choice(exits)
            self.move_to(exit.destination)
        else:
            self.move_to(self.home)

    def do_hunt(self, *args, **kwargs):
        """Pursue visible enemies into adjacent rooms."""
        if random.random() < 0.02 and self.db.irregular_msgs:
            self.location.msg_contents(random.choice(self.db.irregular_msgs))
        if self.db.aggressive:
            target = self._find_target(self.location)
            if target:
                self.start_attacking()
                return

        exits = [exi for exi in self.location.exits if exi.access(self, "traverse")]
        if exits:
            for exit in exits:
                target = self._find_target(exit.destination)
                if target:
                    self.move_to(exit.destination)
                    return
            self.start_patrolling()
        else:
            self.move_to(self.home)

    def do_attack(self, *args, **kwargs):
        """Attack loop."""
        if random.random() < 0.02 and self.db.irregular_msgs:
            self.location.msg_contents(random.choice(self.db.irregular_msgs))

        target = self._find_target(self.location)
        if not target:
            self.start_hunting()
            return

        # choose a random combat verb
        attack_cmd = random.choice(("burst", "slice", "slash", "pierce", "blast"))
        self.execute_cmd(f"{attack_cmd} {target}")

        if target.db.health <= 0:
            target.msg(self.db.defeat_msg)
            self.location.msg_contents(self.db.defeat_msg_room % target.key, exclude=target)
            send_defeated_to = search_object(self.db.send_defeated_to)
            if send_defeated_to:
                target.move_to(send_defeated_to[0], quiet=True)
            else:
                logger.log_err(f"Mob: send_defeated_to not found: {self.db.send_defeated_to}")

    # ---------------------------------------
    # Reaction hooks
    # ---------------------------------------

    def at_hit(self, weapon, attacker, damage):
        """Respond to being hit."""
        if self.db.health is None:
            attacker.msg(self.db.weapon_ineffective_msg)
            return

        if not self.ndb.is_immortal:
            if not weapon.db.magic:
                damage /= self.db.damage_resistance
                attacker.msg(self.db.weapon_ineffective_msg)
            else:
                self.location.msg_contents(self.db.hit_msg)
            self.db.health -= damage

        if self.db.health <= 0:
            attacker.msg(self.db.death_msg)
            self.set_dead()
        else:
            if self.db.aggressive and not self.ndb.is_attacking:
                self.start_attacking()

    def at_new_arrival(self, new_character):
        """React immediately to arrivals."""
        if self.db.aggressive and not self.ndb.is_attacking:
            self.start_attacking()
