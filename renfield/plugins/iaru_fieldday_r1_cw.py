"""IARU Region 1 Field Day"""

# pylint: disable=invalid-name, c-extension-no-member, unused-import

# Status:	Active
# Geographic Focus:	Europe
# Participation:	Worldwide
# Mode:	CW
# Bands:	160, 80, 40, 20, 15, 10m
# Classes:	(see your national society rules)
# Exchange:	RST + Serial No.
# E-mail logs to:	(none)
# Upload log at:	https://dxhf2.darc.de/~fdcwlog/upload.cgi?form=referat&lang=en
# Mail logs to:	(none)
# Find rules at:	https://www.darc.de/der-club/referate/conteste/iaru-region-1-fieldday/en/

# Scoring
# Fixed station to fixed station: 0 points

# For contacts with:

# fixed stations in Europe: 2 points
# fixed stations outside Europe: 3 points
# portable stations in Europe: 4 points
# portable stations outside Europe: 6 points

# Each station may be contacted only once per band.

# Portable stations only count as portable if they sign "/p", "/m", "/mm", or "/am",

# 10. Multipliers
# ONE for each WAE country / DXCC entity worked on each band


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

name = "IARU FIELDDAY R1 DARC CW"
cabrillo_name = "FIELDDAY-REGION-1"
mode = "CW"  # CW SSB BOTH RTTY

# 1 once per contest, 2 work each band, 3 each band/mode, 4 no dupe checking
dupe_type = 2


def points(self):
    """
    Calc point

    # fixed stations in Europe: 2 points
    # fixed stations outside Europe: 3 points
    # portable stations in Europe: 4 points
    # portable stations outside Europe: 6 points
    """

    if self.contact_is_dupe > 0:
        return 0

    their_portable = False
    im_portable = False
    their_continent = self.contact.get("Continent", "")
    the_call = self.contact.get("Call", "").upper()

    if the_call.endswith(("/P", "/M", "/MM", "/AM")):
        their_portable = True
    if self.station.get("Call", "").endswith(("/P", "/M", "/MM", "/AM")):
        im_portable = True

    if not im_portable and not their_portable:
        return 0

    if their_continent:
        if their_portable:
            if their_continent == "EU":
                return 4
            else:
                return 6
        else:
            if their_continent == "EU":
                return 2
            else:
                return 3

    # Something wrong
    return 0


def show_mults(self):
    """Return display string for mults"""
    result = self.database.fetch_mult_count(1)
    if result:
        return int(result.get("count", 0))
    return 0


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
        result = self.database.fetch_mult_count(1)
        mults = int(result.get("count", 0))
        return contest_points * mults
    return 0


def adif(self):
    """Call the generate ADIF function"""
    gen_adif(self, cabrillo_name, "IARU FIELDDAY R1 DARC CW")


def output_cabrillo_line(line_to_output, ending, file_descriptor, file_encoding):
    """"""
    print(
        line_to_output.encode(file_encoding, errors="ignore").decode(),
        end=ending,
        file=file_descriptor,
    )


def cabrillo(self, file_encoding):
    """Generates Cabrillo file. Maybe."""
    # https://www.cqwpx.com/cabrillo.htm
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
        self.log_info(f"Error saving the log:  {ioerror}")
        return


def recalculate_mults(self):
    """Recalculates multipliers after change in logged qso."""
    all_contacts = self.database.fetch_all_contacts_asc()
    for contact in all_contacts:
        self.contact = contact
        contact["Points"] = points(self)
        time_stamp = contact.get("TS", "")
        dxcc = contact.get("CountryPrefix", "")
        result = self.database.fetch_dxcc_exists_before_me(dxcc, time_stamp)
        dxcc_count = result.get("dxcc_count", 1)
        if dxcc_count == 0:
            contact["IsMultiplier1"] = 1
        else:
            contact["IsMultiplier1"] = 0
        self.database.change_contact(contact)


def get_mults(self):
    """Get mults for RTC XML"""
    mults = {}
    mults["country"] = show_mults(self)
    return mults


def just_points(self):
    """Get points for RTC XML"""
    return get_points(self)
