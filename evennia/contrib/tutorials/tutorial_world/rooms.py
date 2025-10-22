"""
Room Typeclasses for Neo Eden, the Cyberpunk City.

This defines the basic room types, commands, and interactive
systems for your new world. It mirrors Evennia's tutorial_world
structure while re-theming everything for a futuristic, neon-drenched
megacity called Neo Eden.

Drop this into:
    mygame/typeclasses/neoeden_rooms.py
"""

import random
from django.conf import settings
from evennia import (
    TICKER_HANDLER,
    CmdSet,
    Command,
    DefaultRoom,
    DefaultExit,
    default_cmds,
    search_object,
    syscmdkeys,
    utils,
)

# -------------------------------------------------------------
# Utility
# -------------------------------------------------------------

_SEARCH_AT_RESULT = utils.object_from_module(settings.SEARCH_AT_RESULT)


# =============================================================
# Base Commands for Neo Eden
# =============================================================

class CmdScan(Command):
    """
    Scan for environmental data or local intel.

    Usage:
      scan [target]

    Cybernetic overlay command. Reads the local info grid
    for relevant descriptions and hints.
    """

    key = "scan"
    aliases = ["ping", "analyze"]
    locks = "cmd:all()"
    help_category = "Neo Eden"

    def func(self):
        caller = self.caller

        target = self.obj if not self.args else caller.search(self.args.strip())
        if not target:
            return

        intel = target.db.intel or ""
        if intel:
            caller.msg(f"|G[Datafeed]:|n {intel}")
        else:
            caller.msg("|RNo accessible data-node at this location.|n")


class CmdHack(Command):
    """
    Hack nearby devices or terminals.

    Usage:
        hack <target>

    Used to breach local systems or gain temporary access.
    """

    key = "hack"
    locks = "cmd:all()"
    help_category = "Neo Eden"

    def func(self):
        caller = self.caller
        if not self.args:
            caller.msg("Hack what?")
            return
        target = caller.search(self.args.strip())
        if not target:
            return
        caller.msg(
            f"You jack into {target.key}'s datastream. |yCode-strings cascade across your HUD.|n"
        )
        target.msg_contents(f"{caller.key} connects cables and starts typing rapidly.", exclude=caller)


class CmdScanLook(default_cmds.CmdLook):
    """
    Look command extended with 'details' and scanning integration.

    Usage:
        look [obj]
        look <room detail>
    """

    help_category = "Neo Eden"

    def func(self):
        caller = self.caller
        args = self.args
        if args:
            looking_at_obj = caller.search(
                args,
                candidates=caller.location.contents + caller.contents,
                use_nicks=True,
                quiet=True,
            )
            if len(looking_at_obj) != 1:
                detail = self.obj.return_detail(args)
                if detail:
                    self.caller.msg(detail)
                    return
                _SEARCH_AT_RESULT(looking_at_obj, caller, args)
                return
            else:
                looking_at_obj = looking_at_obj[0]
        else:
            looking_at_obj = caller.location
            if not looking_at_obj:
                caller.msg("You have no location to look at!")
                return
        if not hasattr(looking_at_obj, "return_appearance"):
            looking_at_obj = looking_at_obj.character
        if not looking_at_obj.access(caller, "view"):
            caller.msg("Could not find '%s'." % args)
            return
        caller.msg(looking_at_obj.return_appearance(caller))
        looking_at_obj.at_desc(looker=caller)


class CmdRetreat(default_cmds.MuxCommand):
    """
    Exit Neo Eden simulation.

    Usage:
        retreat
    """

    key = "retreat"
    aliases = ["logout", "abort"]
    locks = "cmd:all()"
    help_category = "Neo Eden"

    def func(self):
        from .neoeden_rooms import ExitHubRoom
        hub = ExitHubRoom.objects.all()
        if not hub:
            self.caller.msg("Signal lost — cannot retreat. Contact an admin.")
            return
        self.caller.msg("|rDisengaging neural uplink...|n")
        self.caller.move_to(hub[0], move_type="teleport")


# =============================================================
# CmdSets
# =============================================================

class NeoEdenCmdSet(CmdSet):
    """Commands available in all Neo Eden rooms."""

    key = "neoeden_cmdset"
    priority = 1

    def at_cmdset_creation(self):
        self.add(CmdScan())
        self.add(CmdHack())
        self.add(CmdScanLook())
        self.add(CmdRetreat())


# =============================================================
# Base Room
# =============================================================

class NeoEdenRoom(DefaultRoom):
    """
    Base room typeclass for all areas in Neo Eden.
    """

    def at_object_creation(self):
        self.db.intel = (
            "Generic city sector node. Use |wscan|n to pull local environment data."
        )
        self.cmdset.add_default(NeoEdenCmdSet)

    def return_detail(self, detailkey):
        details = self.db.details
        if details:
            return details.get(detailkey.lower(), None)

    def set_detail(self, detailkey, description):
        if self.db.details:
            self.db.details[detailkey.lower()] = description
        else:
            self.db.details = {detailkey.lower(): description}


# =============================================================
# Ambient Weather (Ticker-Based)
# =============================================================

CITY_WEATHER = (
    "A drone swarm buzzes overhead, cameras flickering in the acid rain.",
    "Neon advertisements glitch and stutter, painting the street in pixelated color.",
    "A rumbling mag-train passes beneath your feet.",
    "You hear the faint hum of powerlines and the hiss of coolant leaking somewhere.",
    "The smog thickens, refracting light like a dirty prism.",
    "A siren wails in the distance — another rebellion crushed.",
    "A crackle of thunder arcs between two nearby towers, lighting the smog pink.",
)


class CityWeatherRoom(NeoEdenRoom):
    """
    A Neo Eden room with periodic atmospheric updates.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.interval = random.randint(50, 70)
        TICKER_HANDLER.add(
            interval=self.db.interval, callback=self.update_weather, idstring="neoeden"
        )
        self.db.intel = (
            "Environmental node: weather data active. Expect dynamic updates."
        )

    def update_weather(self, *args, **kwargs):
        if random.random() < 0.25:
            self.msg_contents("|w%s|n" % random.choice(CITY_WEATHER))


# =============================================================
# Entry / Exit Rooms
# =============================================================

class EntryRoom(NeoEdenRoom):
    """
    Entry hub — players awaken in the megacity.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.intel = (
            "Welcome to |cNeo Eden|n — the last free megacity on Earth. "
            "Cybernetic interface boot sequence complete."
        )

    def at_object_receive(self, character, source_location, **kwargs):
        if character.has_account:
            character.msg(
                "|yNeural uplink stabilized. You are now connected to the Neo Eden grid.|n"
            )
            character.db.hp = 100
            character.db.credits = 50


class ExitHubRoom(NeoEdenRoom):
    """
    Safe zone where characters disconnect from the network.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.intel = (
            "The disconnection lounge hums softly with static. "
            "You feel the digital noise fading."
        )

    def at_object_receive(self, character, source_location, **kwargs):
        if character.has_account:
            del character.db.hp
            del character.db.credits
            character.msg("|cAll implants powered down.|n You feel human again.")
            if character.account:
                character.account.execute_cmd("unquell")


# =============================================================
# Restricted / Hacked Zone
# =============================================================

GLITCH_FEED = (
    "A flicker of light reveals a figure frozen mid-motion.",
    "Your HUD glitches; reality tears into digital fragments.",
    "A whisper: 'They’re watching.'",
    "Your vision overlays static — code signatures too heavy for your firewall.",
)


class GlitchZone(NeoEdenRoom):
    """
    Glitched area with random sensory overload messages.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.intel = (
            "Warning: Data corruption detected. Proceed at your own risk."
        )
        self.db.interval = random.randint(40, 60)
        TICKER_HANDLER.add(
            interval=self.db.interval, callback=self.corrupt_feed, idstring="neoeden"
        )

    def corrupt_feed(self, *args, **kwargs):
        if random.random() < 0.3:
            self.msg_contents("|r%s|n" % random.choice(GLITCH_FEED))


# =============================================================
# Locked Corporate Sector (Teleport Puzzle Example)
# =============================================================

class CorpVaultRoom(NeoEdenRoom):
    """
    Corporate data-vault that checks for access key on entry.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.access_key = "omega-clearance"
        self.db.success_msg = "Access granted. Welcome, executive."
        self.db.failure_msg = "ACCESS DENIED — security drones deployed."
        self.db.failure_teleport_to = "detention_cell"
        self.db.success_teleport_to = "executive_lounge"

    def at_object_receive(self, character, source_location, **kwargs):
        if not character.has_account:
            return

        success = str(character.db.access_code) == str(self.db.access_key)
        target = (
            self.db.success_teleport_to if success else self.db.failure_teleport_to
        )
        results = search_object(target)
        if not results:
            character.msg("Target node not found — contact admin.")
            return

        if success:
            character.msg(f"|g{self.db.success_msg}|n")
        else:
            character.msg(f"|r{self.db.failure_msg}|n")

        character.move_to(results[0], quiet=True, move_type="teleport")
        results[0].at_object_receive(character, self)


# =============================================================
# Exit (adds intro command, like TutorialStartExit)
# =============================================================

class EntryStartExit(DefaultExit):
    """
    Gateway exit into Neo Eden simulation.
    """

    def at_object_creation(self):
        self.cmdset.add(CmdSetNeoEdenIntro, persistent=True)


class CmdNeoEdenIntro(Command):
    """
    Begin the Neo Eden startup sequence.

    Usage:
        begin
    """

    key = "begin"

    def func(self):
        caller = self.caller
        caller.msg(
            "|cInitializing neural handshake...|n\n"
            "Welcome to Neo Eden.\nType |wscan|n to analyze your surroundings."
        )


class CmdSetNeoEdenIntro(CmdSet):
    key = "Neo Eden Intro Set"

    def at_cmdset_creation(self):
        self.add(CmdNeoEdenIntro())


# =============================================================
# End of Neo Eden Rooms
# =============================================================
