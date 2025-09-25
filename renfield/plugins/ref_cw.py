"""
REF Contest, CW
Status:	Active
Geographic Focus:	France + overseas territories
Participation:	Worldwide
Awards:	Worldwide
Mode:	CW
Bands:	80, 40, 20, 15, 10m
Classes:	Single Op All Band
            Single Op Single Band
            Multi-Single
            Club
            SWL
Max power:	HP: >100 Watts
            LP: 100 Watts
            QRP: 5 Watts

Exchange:	French: RST + Department/Prefix
            non-French: RST + Serial No.

Work stations:	Once per band

QSO Points:	French: 6 points per QSO with French station same continent
            French: 15 points per QSO with French station on different continent
            French: 1 point per QSO with non-French station same continent
            French: 2 points per QSO with non-French station on different continent
            non-French: 1 point per QSO with French station same continent
            non-French: 3 points per QSO with French station on different continent

Multipliers:	French/Corsica departments once per band
                French overseas prefixes once per band
                non-French DXCC countries once per band (available only to French stations)

Score Calculation:	Total score = total QSO points x total mults

Upload log at:	https://concours.r-e-f.org/contest/logs/upload-form/
Find rules at:	https://concours.r-e-f.org/reglements/actuels/reg_cdfhfdx.pdf
Cabrillo name:	REF-CW
Cabrillo name aliases:	REF
"""

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

name = "French REF DX contest - CW"
cabrillo_name = "REF-CW"
mode = "CW"  # CW SSB BOTH RTTY

# 1 once per contest, 2 work each band, 3 each band/mode, 4 no dupe checking
dupe_type = 2


def points(self):
    """
    Scoring:
    French: 6 points per QSO with French station same continent
    French: 15 points per QSO with French station on different continent
    French: 1 point per QSO with non-French station same continent
    French: 2 points per QSO with non-French station on different continent
    non-French: 1 point per QSO with French station same continent
    non-French: 3 points per QSO with French station on different continent

    self.contact["CountryPrefix"]
    self.contact["Continent"]
    """

    if self.contact_is_dupe > 0:
        return 0

    # Just incase the cty lookup fails
    my_country = None
    my_continent = None
    their_continent = None
    their_country = None

    result = self.cty_lookup(self.station.get("Call", ""))
    if result:
        for item in result.items():
            my_country = item[1].get("entity", "")
            my_continent = item[1].get("continent", "")
    result = self.cty_lookup(self.contact.get("Call", ""))
    if result:
        for item in result.items():
            their_country = item[1].get("entity", "")
            their_continent = item[1].get("continent", "")

    if my_country == "France":
        if their_country == "France":
            if my_continent == their_continent:
                return 6
            else:
                return 15
        else:
            if my_continent == their_continent:
                return 1
            else:
                return 2
    else:
        if their_country == "France":
            if their_continent == my_continent:
                return 1
            else:
                return 3

    return 0


def show_mults(self, rtc=None):
    """Return display string for mults"""
    one = int(self.database.fetch_mult_count(1).get("count", 0))
    two = int(self.database.fetch_mult_count(2).get("count", 0))
    if rtc is not None:
        return (two, one)

    return one + two


def show_qso(self):
    """Return qso count"""
    result = self.database.fetch_qso_count()
    if result:
        return int(result.get("qsos", 0))
    return 0


def calc_score(self):
    """Return calculated score"""
    result = self.database.fetch_points()
    if result is not None:
        score = result.get("Points", "0")
        if score is None:
            score = "0"
        contest_points = int(score)
        mults = show_mults(self)
        return contest_points * mults
    return 0


def recalculate_mults(self):
    """Recalculates multipliers after change in logged qso."""

    all_contacts = self.database.fetch_all_contacts_asc()
    for contact in all_contacts:

        contact["IsMultiplier1"] = 0
        contact["IsMultiplier2"] = 0

        time_stamp = contact.get("TS", "")
        canton = contact.get("NR", "")
        dxcc = contact.get("CountryPrefix", "")
        band = contact.get("Band", "")
        if dxcc == "HB" and canton.isalpha():
            query = (
                f"select count(*) as canton_count from dxlog where  TS < '{time_stamp}' "
                f"and NR = '{canton.upper()}' "
                f"and Band = '{band}' "
                f"and ContestNR = {self.pref.get('contest', '1')};"
            )
            result = self.database.exec_sql(query)
            count = int(result.get("canton_count", 0))
            if count == 0:
                contact["IsMultiplier1"] = 1

        if dxcc:
            query = (
                f"select count(*) as dxcc_count from dxlog where TS < '{time_stamp}' "
                f"and CountryPrefix = '{dxcc}' "
                f"and Band = '{band}' "
                f"and ContestNR = {self.pref.get('contest', '1')};"
            )
            result = self.database.exec_sql(query)
            if not result.get("dxcc_count", ""):
                contact["IsMultiplier2"] = 1

        self.database.change_contact(contact)
    cmd = {}
    cmd["cmd"] = "UPDATELOG"
    if self.log_window:
        self.log_window.msg_from_main(cmd)


def adif(self):
    """Call the generate ADIF function"""
    gen_adif(self, cabrillo_name, "REF-CW")


def output_cabrillo_line(line_to_output, ending, file_descriptor, file_encoding):
    """"""
    print(
        line_to_output.encode(file_encoding, errors="ignore").decode(),
        end=ending,
        file=file_descriptor,
    )


def cabrillo(self, file_encoding):
    """Generates Cabrillo file. Maybe."""
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
                output_cabrillo_line(
                    f"QSO: {frequency} {themode} {loggeddate} {loggedtime} "
                    f"{contact.get('StationPrefix', '').ljust(13)} "
                    f"{str(contact.get('SNT', '')).ljust(3)} "
                    f"{str(contact.get('SentNr', '')).ljust(6)} "
                    f"{contact.get('Call', '').ljust(13)} "
                    f"{str(contact.get('RCV', '')).ljust(3)} "
                    f"{str(contact.get('NR', '')).ljust(6)}",
                    "\r\n",
                    file_descriptor,
                    file_encoding,
                )
            output_cabrillo_line("END-OF-LOG:", "\r\n", file_descriptor, file_encoding)
    except IOError as ioerror:
        self.log_info(f"Error saving the log: {ioerror}")
        return


def get_mults(self):
    """Get mults for RTC XML"""
    mults = {}
    mults["country"], mults["state"] = show_mults(self, rtc=True)
    return mults


def just_points(self):
    """Get points for RTC XML"""
    return get_points(self)
