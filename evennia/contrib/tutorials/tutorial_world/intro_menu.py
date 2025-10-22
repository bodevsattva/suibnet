"""
Neural-Link Boot Tutorial — Neo Eden Starter Menu
Cyberpunk re-theme of the Evennia intro wizard.

Players connect through a neural interface to learn
basic world commands, cybernetic communication, and navigation
within the megacity simulation.

Drop-in replacement for:
evennia/contrib/tutorials/tutorial_world/intro_menu.py
"""

from evennia import CmdSet, create_object
from evennia.utils.evmenu import EvMenu, parse_menu_template

# ============================================================
# Helper callbacks
# ============================================================


def do_nothing(caller, raw_string, **kwargs):
    """Re-runs the current node (used for idle clicks)."""
    return None


def send_testing_tagged(caller, raw_string, **kwargs):
    """Sends a tagged packet to the 'testing' webclient pane."""
    caller.msg(
        (
            (
                f"Transmitting packet to |ctag:'testing'|n.\n"
                f"Payload contents: '{raw_string}'"
            ),
            {"type": "testing"},
        )
    )
    return None


# ============================================================
# Command demos
# ============================================================


class DemoCommandSetHelp(CmdSet):
    """Demo the help interface."""

    key = "Help Demo Set"
    priority = 2

    def at_cmdset_creation(self):
        from evennia import default_cmds

        self.add(default_cmds.CmdHelp())
        self.add(default_cmds.CmdChannel())


def goto_command_demo_help(caller, raw_string, **kwargs):
    """Prep and go to help demo."""
    _maintain_demo_room(caller, delete=True)
    caller.cmdset.remove(DemoCommandSetRoom)
    caller.cmdset.remove(DemoCommandSetComms)
    caller.cmdset.add(DemoCommandSetHelp)
    return kwargs.get("gotonode") or "command_demo_help"


class DemoCommandSetComms(CmdSet):
    """Demo comms / color."""

    key = "Comms Demo Set"
    priority = 2
    no_exits = True
    no_objs = True

    def at_cmdset_creation(self):
        from evennia import default_cmds

        self.add(default_cmds.CmdHelp())
        self.add(default_cmds.CmdSay())
        self.add(default_cmds.CmdPose())
        self.add(default_cmds.CmdPage())
        self.add(default_cmds.CmdColorTest())


def goto_command_demo_comms(caller, raw_string, **kwargs):
    """Setup and go to color demo node."""
    caller.cmdset.remove(DemoCommandSetHelp)
    caller.cmdset.remove(DemoCommandSetRoom)
    caller.cmdset.add(DemoCommandSetComms)
    return kwargs.get("gotonode") or "comms_demo_start"


# ============================================================
# Environment demo (holo-room)
# ============================================================

_ROOM_DESC = """
You materialize inside a small |ytraining pod|n. Holo-lights pulse through the
plating, projecting a simulation of a tight neon alleyway. Energy hums in the air.
Try |wlook sign|n to scan the neon notice by the console.
"""

_SIGN_DESC = """
The flickering sign reads:

    Welcome, operative. Neo Eden thanks you for logging in.

    Try '|wlook small|n' — you’ll notice the interface reports multiple matches.
    Choose which hologram to analyze, e.g. '|wlook small-2|n' or '|wlook alley|n'.

    Even text shortcuts work here. Experiment with partial identifiers!

    When done, |wlook door|n to continue.
"""

_DOOR_DESC_OUT = """
A reinforced bulkhead door, rimmed with holo-locks. A glowing line reads:

    |wEXIT|n — neural gate to the outer simulation.
    Type '|wdoor|n' to breach the boundary field.
"""

_DOOR_DESC_IN = """
The bulkhead door leading back into the training pod. Carved code reads:

    Access: '|wdoor|n' or '|win|n' to re-enter calibration space.
"""

_MEADOW_DESC = """
The world flickers — your environment shifts to a wide digital boulevard
bathed in neon rain. Holographic billboards scroll data endlessly.
A faint hum from overhead drones fills the void.

Try |wlook datapad|n.
"""

_STONE_DESC = """
A cracked |mdatapad|n lies on the asphalt, its screen looping an old tutorial:

    Use |wget datapad|n to pick it up.
    |winventory|n or |wi|n lists what you carry.
    |wdrop datapad|n discards it.

Type |wnext|n when you’re ready to proceed.
"""


def _maintain_demo_room(caller, delete=False):
    """
    Creates or removes the temporary holo-training environment.
    """
    roomdata = caller.db.neoeden_demo_room_data
    if delete:
        if roomdata:
            prev_loc, pod, sign, street, pad, door_out, door_in = roomdata
            caller.location = prev_loc
            sign.delete()
            pad.delete()
            door_out.delete()
            door_in.delete()
            pod.delete()
            street.delete()
            del caller.db.neoeden_demo_room_data
    elif not roomdata:
        pod = create_object("evennia.objects.objects.DefaultRoom", key="Training Pod-01")
        pod.db.desc = _ROOM_DESC.lstrip()
        sign = create_object(
            "evennia.objects.objects.DefaultObject",
            key="flickering neon sign",
            location=pod,
        )
        sign.db.desc = _SIGN_DESC.strip()
        sign.locks.add("get:false()")
        sign.db.get_err_msg = "The sign is bolted to the console."

        street = create_object("evennia.objects.objects.DefaultRoom", key="Neon Alleyway")
        street.db.desc = _MEADOW_DESC.lstrip()
        pad = create_object(
            "evennia.objects.objects.DefaultObject", key="cracked datapad", location=street
        )
        pad.db.desc = _STONE_DESC.strip()

        door_out = create_object(
            "evennia.objects.objects.DefaultExit",
            key="Door",
            location=pod,
            destination=street,
            locks=["get:false()"],
        )
        door_out.db.desc = _DOOR_DESC_OUT.strip()
        door_in = create_object(
            "evennia.objects.objects.DefaultExit",
            key="holo-door entrance",
            aliases=["door", "in", "entrance"],
            location=street,
            destination=pod,
            locks=["get:false()"],
        )
        door_in.db.desc = _DOOR_DESC_IN.strip()

        caller.db.neoeden_demo_room_data = (
            caller.location,
            pod,
            sign,
            street,
            pad,
            door_out,
            door_in,
        )
        caller.location = pod


class DemoCommandSetRoom(CmdSet):
    """Demo exploration commands."""

    key = "Room Demo Set"
    priority = 2
    no_exits = False
    no_objs = False

    def at_cmdset_creation(self):
        from evennia import default_cmds

        self.add(default_cmds.CmdHelp())
        self.add(default_cmds.CmdLook())
        self.add(default_cmds.CmdGet())
        self.add(default_cmds.CmdDrop())
        self.add(default_cmds.CmdInventory())
        self.add(default_cmds.CmdExamine())
        self.add(default_cmds.CmdPy())


def goto_command_demo_room(caller, raw_string, **kwargs):
    _maintain_demo_room(caller)
    caller.cmdset.remove(DemoCommandSetHelp)
    caller.cmdset.remove(DemoCommandSetComms)
    caller.cmdset.add(DemoCommandSetRoom)
    return "command_demo_room"


def goto_cleanup_cmdsets(caller, raw_strings, **kwargs):
    caller.cmdset.remove(DemoCommandSetHelp)
    caller.cmdset.remove(DemoCommandSetComms)
    caller.cmdset.remove(DemoCommandSetRoom)
    return kwargs.get("gotonode")


# ============================================================
# Menu Callables Registry
# ============================================================

GOTO_CALLABLES = {
    "send_testing_tagged": send_testing_tagged,
    "do_nothing": do_nothing,
    "goto_command_demo_help": goto_command_demo_help,
    "goto_command_demo_comms": goto_command_demo_comms,
    "goto_command_demo_room": goto_command_demo_room,
    "goto_cleanup_cmdsets": goto_cleanup_cmdsets,
}


# ============================================================
# MENU TEMPLATE — The Cyberpunk Tutorial Flow
# ============================================================

MENU_TEMPLATE = """

## NODE start

|g** Neo Eden Neural Boot Tutorial **|n

Welcome, operative. This neural wizard will orient your synaptic link to the
city’s interface systems. You can exit at any time with '|yquit|n'.

Press |y<return>|n or type |ynext|n to begin.

## OPTIONS
1: What is Neo Eden? -> about_city
2: System Interface Basics -> about_interface
3: Communication Protocols -> goto_command_demo_help()
4: Color Channels & Feedback -> goto_command_demo_comms(gotonode='testing_colors')
5: Movement Training -> goto_command_demo_room()
6: Final Sync & Logout -> conclusions
>: about_city

# ------------------------------------------------------------------

## NODE about_city

|g** About Neo Eden **|n

Neo Eden — last free megacity on Earth. A million kilometers of circuitry,
a billion lives wired together. Here, power flows through data, and survival
means bandwidth.

Your neural-link lets you |whack reality|n, override perception, and
shape the Grid. Everything responds to text input — your thoughts rendered as code.

## OPTIONS
next;n: About the Interface -> about_interface
back to start;start: start
>: about_interface

# ------------------------------------------------------------------

## NODE about_interface

|g** System Interface Basics **|n

All interaction happens through typed commands. Every action — movement,
communication, combat — begins with language. Type a command, get feedback.

Common verbs:
- |wlook|n — examine your surroundings.
- |wget|n / |wdrop|n — manipulate objects.
- |wsay|n / |wpose|n — communicate or emote.
- |whelp|n — access support matrix.

Evennia interprets these commands and routes them through your link. Shortcuts,
aliases, and partial matches all work — efficiency keeps you alive.

## OPTIONS
next;n: Communication Protocols -> goto_command_demo_help()
back;b: About Neo Eden -> about_city
>: goto_command_demo_help()

# ------------------------------------------------------------------

## NODE command_demo_help

|g** Communication Protocols **|n

Neo Eden networks rely on command channels. Try |whelp|n to see what functions
are live on your implant. For targeted info, use |whelp <topic>|n.

Soon you’ll have |wsay|n and |wpage|n activated — standard interpersonal relays.
Let’s bring those online.

## OPTIONS
next;n: Local Comms -> goto_command_demo_comms()
back;b: Interface Basics -> about_interface
>: goto_command_demo_comms()

# ------------------------------------------------------------------

## NODE comms_demo_start

|g** Local Comms **|n

|ysay|n transmits to everyone in your physical instance.
|wpose|n (or |wemote|n) expresses body language through text.

Examples:
  |ysay Connection stable.|n
  |ypose adjusts cybernetic visor.|n

All transmissions appear with timestamped neon overlay.
Try them before proceeding.

## OPTIONS
next;n: Paging Protocol -> paging_people
back;b: Help Matrix -> goto_command_demo_help()
>: paging_people

# ------------------------------------------------------------------

## NODE paging_people

|g** Private Messaging (Paging)**|n

You can send direct neural pings with |wpage|n:

  |ypage <name> Ping — you alive?|n

Pages work even across simulation sectors.
Try paging yourself to test the echo loop.

## OPTIONS
next;n: Color Feedback -> testing_colors
back;b: Local Comms -> comms_demo_start
>: testing_colors

# ------------------------------------------------------------------

## NODE testing_colors

|g** Visual Feedback & ANSI Spectrum **|n

You can colorize your text — helpful in the chaos of combat or chatter.

    |ysay ||rWarning||n — hostile signature detected!|n
    |ysay ||[005||520Bright green on orange!||n|n

Use |ycolor ansi|n or |ycolor xterm|n to preview all palettes.

Keep it subtle — flashing neon can burn corneas, even digital ones.

## OPTIONS
next;n: Movement Training -> goto_command_demo_room()
back;b: Paging Protocol -> goto_command_demo_comms(gotonode='paging_people')
>: goto_command_demo_room()

# ------------------------------------------------------------------

## NODE command_demo_room

|g** Movement Training **|n

You are being relocated to a holo-simulation. Use |wlook|n to orient yourself.
Explore, examine items, and move between doors. Use |wnext|n when you’re done.

## OPTIONS
next;n: Final Sync -> conclusions
back;b: Color Feedback -> goto_command_demo_comms(gotonode='testing_colors')
>: conclusions

# ------------------------------------------------------------------

## NODE conclusions

|g** Final Sync **|n

You’ve completed the Neo Eden onboarding simulation.

You now understand:
- Command parsing via language input.
- Communication protocols (say/page/pose).
- Object interaction.
- Basic navigation.

Disconnect at any time with |wretreat|n.

Welcome to the Grid.

## OPTIONS
next;n: End -> end
back;b: Movement Training -> goto_command_demo_room()
>: end

# ------------------------------------------------------------------

## NODE end

|g** Connection Stable. Welcome to Neo Eden. **|n

"""


# ============================================================
# Custom Menu subclass
# ============================================================

class NeoEdenIntroMenu(EvMenu):
    """Customized menu class."""

    def close_menu(self):
        self.caller.cmdset.remove(DemoCommandSetHelp)
        self.caller.cmdset.remove(DemoCommandSetRoom)
        self.caller.cmdset.remove(DemoCommandSetComms)
        _maintain_demo_room(self.caller, delete=True)
        super().close_menu()
        if self.caller.account:
            self.caller.msg("|cRestoring clearance protocols...|n")
            self.caller.account.execute_cmd("unquell")

    def options_formatter(self, optionslist):
        navigation_keys = ("next", "back", "back to start")
        other, navigation = [], []
        for key, desc in optionslist:
            if key in navigation_keys:
                desc = f" ({desc})" if desc else ""
                navigation.append(f"|lc{key}|lt|w{key}|n|le{desc}")
            else:
                other.append((key, desc))
        navigation = (
            (" " + " |W|||n ".join(navigation) + " |W|||n " + "|wQ|Wuit|n")
            if navigation
            else ""
        )
        other = super().options_formatter(other)
        sep = "\n\n" if navigation and other else ""
        return f"{navigation}{sep}{other}"


def init_menu(caller):
    """Entry point for Neo Eden tutorial menu."""
    menutree = parse_menu_template(caller, MENU_TEMPLATE, GOTO_CALLABLES)
    NeoEdenIntroMenu(caller, menutree)
