"""RSGB-IOTA"""

# Status:               Active
# Geographic Focus:     Worldwide
# Participation:        Worldwide
# Mode:                 CW, SSB
# Bands:                80, 40, 20, 15, 10m
# Classes:              Single Op (12/24 hrs | Island-Fixed/Island-DXped/World | CW/SSB/Mixed | QRP/Low/High)
#                       Single Op Assisted (12/24 hrs | Island/World | CW/SSB/Mixed | QRP/Low/High)
#                       Single Op Overlay:  Newcomer
#                       Multi-Single (Island-Fixed/Island-DXped | Low/High)
#                       Multi-Two (Island-Fixed/Island-DXped | Low/High)
# Max power:	        HP: 1500 watts
#                       LP: 100 watts
#                       QRP: 5 watts
# Exchange:             RS(T) + Serial No. + IOTA No.(if applicable)
# Work stations:        Once per band per mode
# QSO Points:           (see rules)
# Multipliers:          Each IOTA reference once per band per mode
# Score Calculation:	Total score = total QSO points x total mults
# E-mail logs to:       (none)
# Upload log at:        http://www.rsgbcc.org/cgi-bin/hfenter.pl
# Mail logs to:         (none)
# Find rules at:        https://www.rsgbcc.org/hf/rules/2025/riota.shtml
# Cabrillo name:        RSGB-IOTA


# (a) Island Stations contacting:
#         World Stations: 5 points
#         Island Stations having the same IOTA reference: 5 points
#         Other Island Stations: 15 points
# (b) World Stations contacting:
#         World Stations: 2 points
#         Island Stations: 15 points

# (c) Multiplier. The multiplier is the total of different IOTA references contacted on each band on CW,
#         plus the total of different IOTA references contacted on each band on SSB

# (d) The Total Score is the total of QSO points on all bands added together,
#         multiplied by the total of multipliers on all bands added together


# pylint: disable=invalid-name, unused-argument, unused-variable, c-extension-no-member, unused-import

import datetime
from pathlib import Path

try:
    from lib.ham_utility import get_logged_band
    from lib.plugin_common import gen_adif, get_points, online_score_xml
    from lib.version import __version__
except (ImportError, ModuleNotFoundError):
    from renfield.lib.ham_utility import get_logged_band
    from renfield.lib.plugin_common import gen_adif, get_points, online_score_xml
    from renfield.lib.version import __version__

name = "RSGB-IOTA"
cabrillo_name = "RSGB-IOTA"
mode = "BOTH"  # CW SSB BOTH RTTY

# 1 once per contest, 2 work each band, 3 each band/mode, 4 no dupe checking
dupe_type = 3


def show_mults(self):
    """Return display string for mults"""
    # Multiplier. The multiplier is the total of different IOTA references contacted on each band on CW,
    # plus the total of different IOTA references contacted on each band on SSB.
    # Island Multi-Op stations may not contact members of their own group for multiplier credit.

    query = query = (
        f"select count(DISTINCT(SUBSTR(Nr, INSTR(Nr, ' ') + 1) || ':' || Mode || ':' || Band)) as mults from DXLOG where ContestNR = {self.pref.get('contest', '1')} and INSTR(NR, ' ');"
    )
    result = self.database.exec_sql(query)
    mult_count = result.get("mults", 0)

    return mult_count


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
        return contest_points * (mults + 1)
    return 0


def adif(self):
    """Call the generate ADIF function"""
    gen_adif(self, cabrillo_name)


def output_cabrillo_line(line_to_output, ending, file_descriptor, file_encoding):
    """"""
    print(
        line_to_output.encode(file_encoding, errors="ignore").decode(),
        end=ending,
        file=file_descriptor,
    )


def convert_iota_number(iota: str) -> str:
    """
    converts an IOTA reference string to the correct format for cabrillo log.
    """
    if len(iota) >= 3 and iota[:2].isalpha and iota[2:].isdigit():
        return f"{iota[:2].upper()}-{iota[2:].zfill(3)}"

    return iota


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
            ops = ""
            list_of_ops = self.database.get_ops()
            for op in list_of_ops:
                ops += f"{op.get('Operator', '')}, "
            if self.station.get("Call", "") not in ops:
                ops += f"@{self.station.get('Call','')}"
            else:
                ops = ops.rstrip(", ")
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
                if themode == "LSB" or themode == "USB":
                    themode = "PH"
                frequency = str(round(contact.get("Freq", "0"))).rjust(5)

                loggeddate = the_date_and_time[:10]
                loggedtime = the_date_and_time[11:13] + the_date_and_time[14:16]
                sentnr = str(contact.get("SentNr", "")).upper().split()
                if len(sentnr) == 2:
                    sentnr = sentnr[0].zfill(4) + " " + convert_iota_number(sentnr[1])
                else:
                    sentnr = sentnr[0].zfill(4) + " ------"

                nr = str(contact.get("NR", "")).upper().split()
                if len(nr) == 2:
                    nr = nr[0].zfill(4) + " " + convert_iota_number(nr[1])
                else:
                    if nr[0][-2:].isalpha():
                        nr = nr[0][:-2].zfill(4) + " " + nr[0][-2:]
                    else:
                        nr = nr[0].zfill(4) + " ------"

                output_cabrillo_line(
                    f"QSO: {frequency} {themode} {loggeddate} {loggedtime} "
                    f"{contact.get('StationPrefix', '').ljust(13)} "
                    f"{str(contact.get('SNT', '')).ljust(3)} "
                    f"{sentnr} "
                    f"{contact.get('Call', '').ljust(13)} "
                    f"{str(contact.get('RCV', '')).ljust(3)} "
                    f"{nr}",
                    "\r\n",
                    file_descriptor,
                    file_encoding,
                )
            output_cabrillo_line("END-OF-LOG:", "\r\n", file_descriptor, file_encoding)
        self.show_message_box(f"Cabrillo saved to: {filename}")
    except IOError as ioerror:
        self.log_info(f"Error saving log: {ioerror}")
        return


def recalculate_mults(self):
    """Recalculates multipliers after change in logged qso."""


def get_mults(self):
    """"""

    mults = {}
    return mults


def just_points(self):
    """"""
    return get_points(self)
