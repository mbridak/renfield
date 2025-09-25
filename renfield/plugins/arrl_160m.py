"""ARRL 160 CW plugin"""

# pylint: disable=invalid-name, c-extension-no-member, unused-import, line-too-long

import datetime
from pathlib import Path

# Import path may change depending on if it's dev or production.
try:
    from lib.ham_utility import get_logged_band
    from lib.plugin_common import gen_adif, get_points, online_score_xml
    from lib.version import __version__
except (ImportError, ModuleNotFoundError):
    from renfield.lib.ham_utility import get_logged_band
    from renfield.lib.plugin_common import gen_adif, get_points, online_score_xml
    from renfield.lib.version import __version__

name = "ARRL 160-Meter"
cabrillo_name = "ARRL-160"
mode = "CW"  # CW SSB BOTH RTTY

# 1 once per contest, 2 work each band, 3 each band/mode, 4 no dupe checking
dupe_type = 1


def show_mults(self):
    """Return display string for mults"""
    mults = 0
    if can_claim_dxcc(self):
        result = self.database.fetch_country_count()
        mults = int(result.get("dxcc_count", 0))

    result = self.database.fetch_exchange1_unique_count()
    mults2 = int(result.get("exch1_count", 0))

    return mults + mults2


def show_qso(self):
    """Return qso count"""
    result = self.database.fetch_qso_count()
    if result:
        return int(result.get("qsos", 0))
    return 0


def calc_score(self):
    """Return calculated score"""
    mults = 0
    result = self.database.fetch_points()
    if result is not None:
        score = result.get("Points", "0")
        if score is None:
            score = "0"
        contest_points = int(score)

        if can_claim_dxcc(self):
            result = self.database.fetch_country_count()
            mults = int(result.get("dxcc_count", 0))

        result = self.database.fetch_exchange1_unique_count()
        mults2 = int(result.get("exch1_count", 0))
        return contest_points * (mults + mults2)
    return 0


def can_claim_dxcc(self):
    """"""
    result = self.cty_lookup(self.station.get("Call", ""))
    if result:
        mypfx = ""
        for item in result.items():
            mypfx = item[1].get("primary_pfx", "")
        if mypfx in [
            "K",
            "KL",
            "KH0",
            "KH1",
            "KH2",
            "KH3",
            "KH4",
            "KH5",
            "KH6",
            "KH7",
            "KH8",
            "KH9",
            "KP1",
            "KP2",
            "KP3",
            "KP4",
            "KP5",
            "VE",
        ]:
            return True
        return False


def adif(self):
    """Call the generate ADIF function"""
    gen_adif(self, cabrillo_name, "ARRL 160-Meter")


def output_cabrillo_line(line_to_output, ending, file_descriptor, file_encoding):
    """"""
    print(
        line_to_output.encode(file_encoding, errors="ignore").decode(),
        end=ending,
        file=file_descriptor,
    )


def cabrillo(self, file_encoding):
    """Generates Cabrillo file. Maybe."""
    # https://www.cw160.com/cabrillo.htm

    now = datetime.datetime.now()
    date_time = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = (
        str(Path.home())
        + "/"
        + f"{self.station.get('Call', '').upper()}_{cabrillo_name}_{date_time}.log"
    )
    self.log_info(f"Saving log to:{filename}")
    log = self.database.fetch_all_contacts_asc()
    try:
        with open(filename, "w", encoding=file_encoding, newline="") as file_descriptor:
            output_cabrillo_line(
                "START-OF-LOG: 3.0",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"CREATED-BY: Not1MM v{__version__}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"CONTEST: {cabrillo_name}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            if self.station.get("Club", ""):
                output_cabrillo_line(
                    f"CLUB: {self.station.get('Club', '').upper()}",
                    "\r\n",
                    file_descriptor,
                    file_encoding,
                )
            output_cabrillo_line(
                f"CALLSIGN: {self.station.get('Call','')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"LOCATION: {self.station.get('ARRLSection', '')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"CATEGORY-OPERATOR: {self.contest_settings.get('OperatorCategory','')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"CATEGORY-ASSISTED: {self.contest_settings.get('AssistedCategory','')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"CATEGORY-BAND: {self.contest_settings.get('BandCategory','')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            mode = self.contest_settings.get("ModeCategory", "")
            if mode in ["SSB+CW", "SSB+CW+DIGITAL"]:
                mode = "MIXED"
            output_cabrillo_line(
                f"CATEGORY-MODE: {mode}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"CATEGORY-TRANSMITTER: {self.contest_settings.get('TransmitterCategory','')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            if self.contest_settings.get("OverlayCategory", "") != "N/A":
                output_cabrillo_line(
                    f"CATEGORY-OVERLAY: {self.contest_settings.get('OverlayCategory','')}",
                    "\r\n",
                    file_descriptor,
                    file_encoding,
                )
            output_cabrillo_line(
                f"GRID-LOCATOR: {self.station.get('GridSquare','')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"CATEGORY-POWER: {self.contest_settings.get('PowerCategory','')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )

            output_cabrillo_line(
                f"CLAIMED-SCORE: {calc_score(self)}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            ops = f"@{self.station.get('Call','')}"
            list_of_ops = self.database.get_ops()
            for op in list_of_ops:
                ops += f", {op.get('Operator', '')}"
            output_cabrillo_line(
                f"OPERATORS: {ops}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"NAME: {self.station.get('Name', '')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"ADDRESS: {self.station.get('Street1', '')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"ADDRESS-CITY: {self.station.get('City', '')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"ADDRESS-STATE-PROVINCE: {self.station.get('State', '')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"ADDRESS-POSTALCODE: {self.station.get('Zip', '')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"ADDRESS-COUNTRY: {self.station.get('Country', '')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"EMAIL: {self.station.get('Email', '')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            for contact in log:
                the_date_and_time = contact.get("TS", "")
                themode = contact.get("Mode", "")
                if themode in ("LSB", "USB", "FM"):
                    themode = "PH"
                frequency = str(int(contact.get("Freq", "0"))).rjust(5)

                loggeddate = the_date_and_time[:10]
                loggedtime = the_date_and_time[11:13] + the_date_and_time[14:16]
                thesentnr = contact.get("SentNr", "---")
                if thesentnr == "":
                    thesentnr = "---"
                theexch = contact.get("Exchange1", "---")
                if theexch == "":
                    theexch = "---"

                output_cabrillo_line(
                    f"QSO: {frequency} {themode} {loggeddate} {loggedtime} "
                    f"{contact.get('StationPrefix', '').ljust(13)} "
                    f"{str(contact.get('SNT', '')).ljust(3)} "
                    f"{str(thesentnr).ljust(6)} "
                    f"{contact.get('Call', '').ljust(13)} "
                    f"{str(contact.get('RCV', '')).ljust(3)} "
                    f"{str(theexch).ljust(6)}",
                    "\r\n",
                    file_descriptor,
                    file_encoding,
                )
            output_cabrillo_line("END-OF-LOG:", "\r\n", file_descriptor, file_encoding)
    except IOError as ioerror:
        self.log_info(f"Error saving log: {ioerror}")
        return


def recalculate_mults(self):
    """Recalculates multipliers after change in logged qso."""
    # all_contacts = self.database.fetch_all_contacts_asc()
    # for contact in all_contacts:
    #     time_stamp = contact.get("TS", "")
    #     if contact.get("CountryPrefix", "") == "K":
    #         query = f"select count(*) as count from dxlog where TS < '{time_stamp}' and CountryPrefix = 'K' and Exchange1 = '{contact.get('Exchange1', '')}' and ContestNR = '{self.pref.get('contest', '0')}'"
    #         result = self.database.exec_sql(query)
    #         if result.get("count", 0) == 0:
    #             contact["IsMultiplier1"] = 1
    #         else:
    #             contact["IsMultiplier1"] = 0
    #         self.database.change_contact(contact)
    #         continue
    #     if contact.get("CountryPrefix", "") == "VE":
    #         query = f"select count(*) as count from dxlog where TS < '{time_stamp}' and CountryPrefix = 'VE' and Exchange1 = '{contact.get('Exchange1', '')}' and ContestNR = '{self.pref.get('contest', '0')}'"
    #         result = self.database.exec_sql(query)
    #         if result.get("count", 0) == 0:
    #             contact["IsMultiplier1"] = 1
    #         else:
    #             contact["IsMultiplier1"] = 0
    #         self.database.change_contact(contact)
    #         continue
    #     query = f"select count(*) as count from dxlog where TS < '{time_stamp}' and CountryPrefix = '{contact.get('CountryPrefix', '')}' and ContestNR = '{self.pref.get('contest', '0')}'"
    #     result = self.database.exec_sql(query)
    #     if result.get("count", 0) == 0:
    #         contact["IsMultiplier1"] = 1
    #     else:
    #         contact["IsMultiplier1"] = 0
    #     self.database.change_contact(contact)
    # trigger_update(self)


def get_mults(self):
    """"""
    mults = {}
    if can_claim_dxcc(self):
        mults["country"] = self.database.fetch_country_count().get("dxcc_count", 0)

    mults["state"] = self.database.fetch_exchange1_unique_count().get("exch1_count", 0)

    return mults


def just_points(self):
    """"""
    return self.database.fetch_points().get("Points", "0")
