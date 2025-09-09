#!/usr/bin/env python3
"""Not1MM Contest Contact Aggregation Server"""

import logging
import importlib
import socket
import time

from time import gmtime, strftime

import datetime

# import os
import sys

# import threading
# import argparse
import queue

# import pkgutil
# from itertools import chain
from json import JSONDecodeError, loads, dumps

# from pathlib import Path
# from shutil import copyfile
# Import path may change depending on if it's dev or production.
try:
    import renfield.lib.fsutils as fsutils
    from renfield.lib.version import __version__
    from renfield.lib.database import DataBase
except (ImportError, ModuleNotFoundError):
    import lib.fsutils as fsutils
    from lib.version import __version__
    from lib.database import DataBase

from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import Static, Header, Footer, Placeholder, DataTable
from textual.containers import VerticalScroll, Horizontal, Vertical, Grid, Container

# from textual import log


# pylint: disable=no-name-in-module, invalid-name, c-extension-no-member, global-statement


class Trafficlog:
    """holds recent udp log traffic"""

    def __init__(self):
        self.items = []

    def add_item(self, item):
        """adds an item to the log and trims the log"""
        self.items.append(item)
        if len(self.items) > 16:
            self.items = self.items[1 : len(self.items)]

    def get_log(self):
        """returns a list of log items"""
        return self.items


def doimp(modname) -> object:
    """
    Imports a module.

    Parameters
    ----------
    modname : str
    The name of the module to import.

    Returns
    -------
    object
    The module object.
    """

    # logger.debug("doimp: %s", modname)
    try:
        return importlib.import_module(f"plugins.{modname}")
    except (ImportError, ModuleNotFoundError):
        return importlib.import_module(f"renfield.plugins.{modname}")


class Msg(Static):
    """A widget to display messages."""

    def __init__(self) -> None:
        super().__init__()
        self.contents = [""]

    def on_mount(self) -> None: ...

    def on_update(self, message: str) -> None:
        """Update the message."""
        self.contents.insert(0, message)
        message = "\n".join(self.contents)
        self.update(message)


class NetworkInfo(DataTable):
    """A widget to display UPD network information."""

    def __init__(self) -> None:
        super().__init__()

    def on_mount(self) -> None: ...

    def on_update(self, group: str, port: int, interface: str) -> None:
        """Update the message."""
        ROWS = [
            ("", ""),
            (Text("Group:", justify="right"), f"{group}"),
            (Text("Port:", justify="right"), f"{port}"),
            (Text("Interface:", justify="right"), f"{interface}"),
        ]
        self.show_header = False
        self.show_cursor = False
        self.add_columns(*ROWS[0])
        self.add_rows(ROWS[1:])


class ContestInfo(DataTable):
    """A widget to display the current contest information."""

    def __init__(self) -> None:
        super().__init__()

    def on_mount(self) -> None: ...

    def on_update(self, station: str, contest: str, interface: str) -> None:
        """Update the message."""
        ROWS = [
            ("", ""),
            (Text("Station:", justify="right"), f"{station}"),
            (Text("Contest:", justify="right"), f"{contest}"),
            # (Text("Interface:", justify="right"), f"{interface}"),
        ]
        self.show_header = False
        self.show_cursor = False
        self.clear()
        self.add_columns(*ROWS[0])
        self.add_rows(ROWS[1:])


class ContactsInfo(DataTable):
    """A widget to display a table of contact counts by band and mode."""

    def __init__(self) -> None:
        super().__init__()

    def on_mount(self) -> None:
        self.zebra_style = True
        self.show_header = True
        self.show_cursor = False
        ROWS = [("Band", "QSO", "CW", "PH", "DI", "Pts")]
        self.add_columns(*ROWS[0])

    def on_update(self, stats: list[tuple[str, str, str, str, str, str]]) -> None:
        """Update the message."""
        self.clear()
        self.add_rows(stats)


class OperatorInfo(DataTable):
    """A widget to display contest operators."""

    def __init__(self) -> None:
        super().__init__()

    def on_mount(self) -> None:
        self.zebra_style = True
        self.show_header = True
        self.show_cursor = False
        ROWS = [("Operator", "Log Pos", "Band", "Mode")]
        self.add_columns(*ROWS[0])

    def on_update(self, op_list) -> None:
        """Update the widget."""
        ops = []
        for opname in op_list.keys():
            items = op_list.get(opname, ["", "", ""])
            ops.append([opname, items[0], items[1], items[2]])
        self.clear()
        self.add_rows(ops)


class Application(App):

    BINDINGS = [
        ("q", "quit_app", "Exit the application"),
        ("R", "reset_db", "Reset the database"),
        ("c", "save_cabrillo", "Save Cabrillo"),
    ]
    contest = None

    def __init__(self):
        super().__init__()
        self.database: DataBase = DataBase("server_database.db", fsutils.HOME_PATH)
        self.active_contest: str | None = None
        self.station: dict = {}
        self.contest_settings: dict = {}
        self.contest: object | None = None
        self.operators_seen = {}
        self.udp_fifo: queue.Queue = queue.Queue()
        self.MULTICAST_PORT: int = 2239
        self.MULTICAST_GROUP: str = "224.1.1.1"
        self.INTERFACE_IP: str = "0.0.0.0"
        self.network_socket: socket.socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM
        )
        if sys.platform.startswith("darwin"):
            self.network_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        else:
            self.network_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.network_socket.bind(("", self.MULTICAST_PORT))
        mreq = socket.inet_aton(self.MULTICAST_GROUP) + socket.inet_aton(
            self.INTERFACE_IP
        )
        self.network_socket.setsockopt(
            socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, bytes(mreq)
        )
        self.network_socket.settimeout(0.1)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        self.server_msg = Msg()
        self.networkinfo = NetworkInfo()
        self.contestinfo = ContestInfo()
        self.contactsinfo = ContactsInfo()
        self.operatorinfo = OperatorInfo()

        yield Header()
        with Vertical():
            with Horizontal(id="h1"):
                yield Container(self.contestinfo, id="contestinfo")
                yield Container(self.networkinfo, id="networkinfo")
                yield Placeholder(id="ph5")
            with Horizontal(id="h2"):
                yield Vertical(VerticalScroll(self.server_msg, id="scroll"), id="v1")
                yield Vertical(
                    Container(self.contactsinfo, id="contactsinfo"),
                    Container(self.operatorinfo, id="operatorinfo"),
                    id="v2",
                )
        yield Footer()

    def on_mount(self) -> None:
        """Called when widget is first added."""

        self.title = "renfield"
        self.sub_title = f"v{__version__}"

        self.server_msg.styles.text_overflow = "ellipsis"
        self.networkinfo.styles.text_overflow = "ellipsis"
        self.networkinfo.styles.align = ("center", "middle")
        # self.server_msg.styles.width = "2fr"

        widget = self.query_one("#scroll")
        widget.styles.overflow_y = "scroll"
        widget.styles.border = ("solid", "green")
        widget.styles.width = "100%"
        widget.border_title = "[blue]UDP Traffic[/]"

        h1 = self.query_one("#h1")
        h2 = self.query_one("#h2")
        h1.styles.height = "1fr"
        h2.styles.height = "2fr"
        contestinfo = self.query_one("#contestinfo")
        networkinfo = self.query_one("#networkinfo")
        ph5 = self.query_one("#ph5")
        contestinfo.styles.width = "1fr"
        networkinfo.styles.width = "1fr"
        ph5.styles.width = "1fr"
        contestinfo.styles.border = ("solid", "green")
        networkinfo.styles.border = ("solid", "green")
        ph5.styles.border = ("solid", "green")
        contestinfo.border_title = "[blue]Group[/]"
        networkinfo.border_title = "[blue]Network[/]"
        ph5.border_title = "[blue]Scoring[/]"

        v1 = self.query_one("#v1")
        v2 = self.query_one("#v2")
        v1.styles.width = "2fr"
        v2.styles.width = "1fr"

        contactsinfo = self.query_one("#contactsinfo")
        contactsinfo.styles.height = "1fr"
        contactsinfo.styles.border = ("solid", "green")
        contactsinfo.border_title = "[blue]Contacts[/]"

        operatorinfo = self.query_one("#operatorinfo")
        operatorinfo.styles.height = "1fr"
        operatorinfo.styles.border = ("solid", "green")
        operatorinfo.border_title = "[blue]Operators[/]"

        self.set_interval(0.2, self.server_message)
        self.set_interval(10.0, self.send_pulse)
        self.update_network_window()
        self.update_contest_window()
        self.update_contacts_window()

    def log_info(self, msg: str = "") -> None:
        """send timestamped message to onscreen log"""
        timestamp = strftime("%H:%M:%S", gmtime())
        self.server_msg.on_update(f"\\[{timestamp}] {msg}")

    def action_quit_app(self) -> None:
        """Exit the application."""
        self.exit()

    def action_reset_db(self) -> None:
        """Reset the contest database."""
        self.log_info("Resetting DB")
        self.database.reset_database()
        self.update_contacts_window()

    def action_save_cabrillo(self) -> None:
        """Save Cabrillo."""
        self.contest.cabrillo(self, "utf-8")

    def send_pulse(self) -> None:
        """send heartbeat"""
        try:
            pulse = b'{"cmd": "PING", "host": "server"}'
            self.network_socket.sendto(
                pulse, (self.MULTICAST_GROUP, self.MULTICAST_PORT)
            )
        except OSError as error:
            self.log_info(f"OSError: {error}")

        if self.active_contest is None:
            self.send_contest_request()

    def send_contest_request(self) -> None:
        """send heartbeat"""
        try:
            pulse = b'{"cmd": "CONTEST_REQUEST", "host": "server"}'
            self.network_socket.sendto(
                pulse, (self.MULTICAST_GROUP, self.MULTICAST_PORT)
            )
        except OSError as error:
            self.log_info(f"OSError: {error}")

    def server_message(self) -> None:
        """Respond to network messages"""

        try:
            payload = self.network_socket.recv(2048)
        except socket.timeout:
            return
        if not payload:
            return
        try:
            json_data = loads(payload.decode())
        except UnicodeDecodeError as err:
            the_error = f"Not Unicode: {err}\n{payload}\n"
            print(the_error)
            return
        except JSONDecodeError as err:
            the_error = f"Not JSON: {err}\n{payload}\n"
            print(the_error)
            return
        print(json_data)

        if json_data.get("cmd") == "POST":

            # {
            #     'TS': '2025-05-05 20:44:46',
            #     'Call': 'K5TUX',
            #     'Freq': 14030.0,
            #     'QSXFreq': 14030.0,
            #     'Mode': 'CW',
            #     'ContestName': 'ARRL-FIELD-DAY',
            #     'SNT': '599',
            #     'RCV': '599',
            #     'CountryPrefix': 'K',
            #     'StationPrefix': 'K6GTE',
            #     'QTH': '',
            #     'Name': '',
            #     'Comment': '',
            #     'NR': 0,
            #     'Sect': 'MO',
            #     'Prec': '',
            #     'CK': 0,
            #     'ZN': 4,
            #     'SentNr': 0,
            #     'Points': 2,
            #     'IsMultiplier1': 0,
            #     'IsMultiplier2': 0,
            #     'Power': 0,
            #     'Band': '14',
            #     'WPXPrefix': 'K5',
            #     'Exchange1': '1B',
            #     'RadioNR': '',
            #     'ContestNR': '4',
            #     'isMultiplier3': 0,
            #     'MiscText': '',
            #     'IsRunQSO': False,
            #     'ContactType': '',
            #     'Run1Run2': '',
            #     'GridSquare': '',
            #     'Operator': 'K6GTE',
            #     'Continent': 'NA',
            #     'RoverLocation': '',
            #     'RadioInterfaced': '',
            #     'NetworkedCompNr': 1,
            #     'NetBiosName': 'fredo',
            #     'IsOriginal': 1,
            #     'ID': '42a30a19379b4171a810bb6b8ac4d9ce',
            #     'CLAIMEDQSO': 1,
            #     'cmd': 'POST',
            #     'expire': '2025-05-05T13:45:16.061513'
            # }

            self.log_info(
                f"CMD:{json_data.get('cmd', '')}:{json_data.get('Call', '')} From:{json_data.get('NetBiosName', '')}:{json_data.get('Operator', '')} "
            )
            json_data.pop("cmd", None)
            json_data.pop("expire", None)

            self.database.log_contact(json_data)

            packet = {"cmd": "RESPONSE"}
            packet["recipient"] = json_data.get("NetBiosName")
            packet["subject"] = "POST"
            packet["unique_id"] = json_data.get("ID")
            sendme = bytes(dumps(packet), encoding="ascii")
            self.network_socket.sendto(
                sendme, (self.MULTICAST_GROUP, self.MULTICAST_PORT)
            )
            self.update_contacts_window()
            self.operators_seen[json_data.get("Operator", "Unknown")] = [
                json_data.get("NetBiosName", "Unknown"),
                json_data.get("Band", "Unknown"),
                json_data.get("Mode", "Unknown"),
            ]
            self.update_operators_window()
            return

        if json_data.get("cmd") == "STATION_STATE":
            self.operators_seen[json_data.get("Operator", "Unknown")] = [
                json_data.get("NetBiosName", "Unknown"),
                json_data.get("Band", "Unknown"),
                json_data.get("Mode", "Unknown"),
            ]
            self.update_operators_window()
            return

        if json_data.get("cmd") == "LOG":
            self.log_info(f"Got {json_data.get("cmd")}: {json_data=} ")
            # LOG.add_item(f"[{timestamp}] GENERATE LOG: {json_data.get('station')}")
            # cabrillo()
            # packet = {"cmd": "RESPONSE"}
            # packet["recipient"] = json_data.get("station")
            # packet["subject"] = "LOG"
            # bytes_to_send = bytes(dumps(packet), encoding="ascii")
            # s.sendto(bytes_to_send, (MULTICAST_GROUP, MULTICAST_PORT))
            # LOG.add_item(
            #     f"[{timestamp}] GENERATE LOG CONF: {json_data.get('station')}"
            # )
            return

        if json_data.get("cmd") == "DUPE":
            self.log_info(f"Got {json_data.get("cmd")}: {json_data=} ")
            # LOG.add_item(f"[{timestamp}] Checking Dupe: {json_data.get('contact')}")
            # packet = {"cmd": "RESPONSE"}
            # packet["recipient"] = json_data.get("station")
            # packet["subject"] = "DUPE"
            # packet["contact"] = json_data.get("contact")
            # _call = json_data.get("contact")
            # _mode = json_data.get("mode")
            # _band = json_data.get("band")
            # the_count = DB.get_dupe_status(_call, _band, _mode)
            # packet["isdupe"] = the_count
            # bytes_to_send = bytes(dumps(packet), encoding="ascii")
            # s.sendto(bytes_to_send, (MULTICAST_GROUP, MULTICAST_PORT))
            # # comm_log()
            return

        if json_data.get("cmd") == "DELETE":
            self.log_info(
                f"CMD:{json_data.get('cmd', '')} From:{json_data.get('station', '')} ID:{json_data.get('ID', '')}"
            )

            self.database.delete_contact(json_data.get("unique_id", ""))

            packet = {"cmd": "RESPONSE"}
            packet["recipient"] = json_data.get("station")
            packet["subject"] = "DELETE"
            packet["unique_id"] = json_data.get("unique_id")
            sendme = bytes(dumps(packet), encoding="ascii")
            self.network_socket.sendto(
                sendme, (self.MULTICAST_GROUP, self.MULTICAST_PORT)
            )
            self.update_contacts_window()
            return

        if json_data.get("cmd") == "CONTACTCHANGED":
            self.log_info(
                f"CMD:{json_data.get('cmd', '')} From:{json_data.get('NetBiosName', '')} OP:{json_data.get('Operator', '')} ID:{json_data.get('ID', '')}"
            )
            print(json_data)
            # Construct a response.
            packet = {"cmd": "RESPONSE"}
            packet["recipient"] = json_data.get("NetBiosName")
            packet["subject"] = "CONTACTCHANGED"
            packet["unique_id"] = json_data.get("ID")

            # Strip out unneeded keys value pairs.
            json_data.pop("cmd", None)
            json_data.pop("station", None)
            json_data.pop("expire", None)
            json_data.pop("unique_id", None)

            self.database.change_contact(json_data)
            sendme = bytes(dumps(packet), encoding="ascii")
            self.network_socket.sendto(
                sendme, (self.MULTICAST_GROUP, self.MULTICAST_PORT)
            )
            self.update_contacts_window()
            return

        if json_data.get("cmd") == "NEWDB":
            # {"ContestID": 1, "ContestName": "general_logging", "StartDate": "2025-08-13 00:00:00",
            # "OperatorCategory": "SINGLE-OP", "BandCategory": "ALL", "PowerCategory": "LOW",
            # "ModeCategory": "CW", "OverlayCategory": "N/A", "ClaimedScore": "'''''''0'''''''",
            # "Operators": "k6gte", "Soapbox": "", "SentExchange": "", "ContestNR": 1, "SubType": null,
            # "StationCategory": "FIXED", "AssistedCategory": "ASSISTED", "TransmitterCategory": "ONE",
            # "TimeCategory": null, "cmd": "NEWDB", "expire": "2025-08-24T09:36:36.212594",
            # "NetBiosName": "fredo", "Operator": "K6GTE", "ID": "713af39d088d467ab7dfc431debc59e9",
            # "Station": {"Call": "K6GTE", "Name": "Michael Bridak", "Email": "michael.bridak@gmail.com",
            # "Street1": "2854 W Bridgeport Ave", "Street2": "", "City": "Anaheim", "State": "CA",
            # "Zip": "92804", "Country": "United States", "GridSquare": "dm13at", "LicenseClass": "General",
            # "Latitude": 33.8125, "Longitude": -117.9583, "PacketNode": "N/A", "ARRLSection": "ORG",
            # "Club": "", "IARUZone": 6, "CQZone": 3, "STXeq": "", "SPowe": "", "SAnte": "", "SAntH1": "",
            # "SAntH2": "", "RoverQTH": ""}}

            self.log_info(
                f"CMD:{json_data.get('cmd', '')} From:{json_data.get('NetBiosName', '')} OP:{json_data.get('Operator', '')}"
            )
            globals()["station"] = json_data.get("Station")

            self.active_contest = json_data.get("ContestName", "")
            self.database.current_contest = self.active_contest.upper().replace(
                "_", "-"
            )
            self.contest = doimp(json_data.get("ContestName"))
            self.station = json_data.get("Station", {})
            self.contest_settings = json_data
            self.update_contest_window()
            self.update_contacts_window()
            print(f"Active contest set to {self.active_contest}")
            packet = {"cmd": "RESPONSE"}
            packet["recipient"] = json_data.get("NetBiosName")
            packet["subject"] = "NEWDB"
            packet["unique_id"] = json_data.get("ID")
            sendme = bytes(dumps(packet), encoding="ascii")
            self.network_socket.sendto(
                sendme, (self.MULTICAST_GROUP, self.MULTICAST_PORT)
            )
            return

        if json_data.get("cmd") == "CURRENT_CONTEST":
            self.active_contest = json_data.get("ContestName", "")
            self.database.current_contest = self.active_contest.upper().replace(
                "_", "-"
            )
            self.server_msg.on_update("")
            self.contest = doimp(self.active_contest)
            self.update_contest_window()
            self.update_contacts_window()
            print(f"Active contest set to {self.active_contest}")

    def update_network_window(self) -> None:
        """Shows the network information."""
        self.networkinfo.on_update(
            self.MULTICAST_GROUP, self.MULTICAST_PORT, self.INTERFACE_IP
        )

    def update_contest_window(self) -> None:
        """Shows the contest information."""
        self.contestinfo.on_update(
            self.station.get("Call", ""), self.active_contest, ""
        )

    def update_contacts_window(self) -> None:
        """Shows the contacts information."""
        self.contactsinfo.on_update(self.database.get_statistics())

    def update_operators_window(self) -> None:
        """
        Shows the operators information.
        operator_list = list[tuple[str, str, str]]
        """
        self.operatorinfo.on_update(self.operators_seen)


def run():
    app = Application()
    app.run()


if __name__ == "__main__":
    run()
