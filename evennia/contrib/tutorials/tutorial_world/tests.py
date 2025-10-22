"""
Tests for Neo Eden tutorial replacements.
"""

from mock import patch
from twisted.internet.base import DelayedCall
from twisted.trial.unittest import TestCase as TwistedTestCase

from evennia.commands.default.tests import BaseEvenniaCommandTest
from evennia.utils.create import create_object
from evennia.utils.test_resources import BaseEvenniaTest, mockdeferLater, mockdelay

# updated imports for your theme
from . import mob
from . import objects as tutobjects
from . import rooms as tutrooms


class TestNeoEdenMob(BaseEvenniaTest):
    def test_mob(self):
        mobobj = create_object(mob.Mob, key="drone")
        self.assertTrue(mobobj.db.is_dead)
        mobobj.set_alive()
        self.assertFalse(mobobj.db.is_dead)
        mobobj.set_dead()
        self.assertTrue(mobobj.db.is_dead)
        mobobj._set_ticker(0, "foo", stop=True)


DelayedCall.debug = True


class TestNeoEdenObjects(TwistedTestCase, BaseEvenniaCommandTest):
    def tearDown(self):
        self.char1.delete()
        super(BaseEvenniaCommandTest, self).tearDown()

    def test_tutorialobj(self):
        obj1 = create_object(tutobjects.TutorialObject, key="obj")
        obj1.reset()
        self.assertEqual(obj1.location, obj1.home)

    def test_readable(self):
        readable = create_object(tutobjects.TutorialReadable, key="terminal", location=self.room1)
        readable.db.readable_text = "Encrypted data recovered."
        self.call(tutobjects.CmdRead(), "terminal", "Accessing terminal", obj=readable)

    def test_climbable(self):
        climbable = create_object(tutobjects.TutorialClimbable, key="ladder", location=self.room1)
        self.call(tutobjects.CmdClimb(), "ladder", "You scale", obj=climbable)
        self.assertEqual(
            self.char1.tags.get("neoeden_climbed", category="tutorial_world"),
            "neoeden_climbed",
        )

    def test_obelisk(self):
        obelisk = create_object(tutobjects.Obelisk, key="holo-totem", location=self.room1)
        result = obelisk.return_appearance(self.char1)
        self.assertIn("holographic", result)

    @patch("typeclasses.neoeden_objects.delay", mockdelay)
    @patch("evennia.scripts.taskhandler.deferLater", mockdeferLater)
    def test_lightsource(self):
        light = create_object(tutobjects.LightSource, key="glowstick", location=self.room1)
        self.call(tutobjects.CmdLight(), "", "activates", obj=light)
        self.assertFalse(light.pk)

    @patch("typeclasses.neoeden_objects.delay", mockdelay)
    @patch("evennia.scripts.taskhandler.deferLater", mockdeferLater)
    def test_gate(self):
        gate = create_object(tutobjects.CrumblingWall, key="gate", location=self.room1)
        gate.db.destination = self.room2.dbref
        self.call(tutobjects.CmdHack(), "gate", "ACCESS", obj=gate)
        self.assertIn("ACCESS", self.char1.msgs[-1]) if hasattr(self.char1, "msgs") else None

    def test_weapon(self):
        weapon = create_object(tutobjects.TutorialWeapon, key="blade", location=self.char1)
        self.call(tutobjects.CmdAttack(), "Char", "You", obj=weapon, cmdstring="blast")

    def test_weaponrack(self):
        rack = create_object(tutobjects.TutorialWeaponRack, key="dispenser", location=self.room1)
        rack.db.available_weapons = ["energy_blade"]
        self.call(tutobjects.CmdGetWeapon(), "", "Energy Blade", obj=rack)


class TestNeoEdenRooms(BaseEvenniaCommandTest):
    def test_cmdtutorial(self):
        room = create_object(tutrooms.TutorialRoom, key="tutorial node")
        self.char1.location = room
        self.call(tutrooms.CmdTutorial(), "", "Sorry, there is no tutorial help available here.")
