"""10 10 fall cw plugin"""

# pylint: disable=invalid-name, unused-argument, unused-variable, c-extension-no-member, unused-import

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

ukei_pfx = [
    "G",
    "GD",
    "GJ",
    "GM",
    "GI",
    "GW",
    "GU",
    "EI",
]

name = "UKEI-DX"
cabrillo_name = "UKEI-DX"
mode = "BOTH"  # CW SSB BOTH RTTY

# 1 once per contest, 2 work each band, 3 each band/mode, 4 no dupe checking
dupe_type = 2


def points(self):
    """Calc point"""

    # UK/EI stations contacting :
    # UK/EI/Europe 80m, 40m - 4 points 20m, 15m, 10m - 2 points
    # DX (Outside Europe) 80m, 40m - 8 points 20m, 15m, 10m - 4 points

    # Note : For UK/EI stations only, all QSOs will score double points between the hours of 0100z and 0459z.

    # European stations contacting :
    # UK/EI 80m, 40m - 4 points 20m, 15m, 10m - 2 points
    # Europe 80m, 40m - 2 points 20m, 15m, 10m - 1 points
    # DX (Outside Europe) 80m, 40m - 4 points 20m, 15m, 10m - 2 points

    # DX (Outside Europe) contacting :
    # UK/EI 80m, 40m - 8 points 20m, 15m, 10m - 4 points
    # Europe 80m, 40m - 4 points 20m, 15m, 10m - 2 points
    # DX (Outside Europe) 80m, 40m - 2 points 20m, 15m, 10m - 1 points

    # f"{primary_pfx}: {continent}/{entity} cq:{cq} itu:{itu}"

    if self.contact_is_dupe > 0:
        return 0

    myprimary_pfx = ""
    mycontinent = ""
    hisprimary_pfx = ""
    hiscontinent = ""

    result = self.cty_lookup(self.station.get("Call", ""))
    if result:
        for item in result.items():
            myprimary_pfx = item[1].get("primary_pfx", "")
            mycontinent = item[1].get("continent", "")

    result = self.cty_lookup(self.contact.get("Call", ""))
    if result:
        for item in result.items():
            hisprimary_pfx = item[1].get("primary_pfx", "")
            hiscontinent = item[1].get("continent", "")

    st = 100
    et = 459
    zt = datetime.datetime.now(datetime.timezone.utc).isoformat(" ")[11:16]
    ct = int(zt[0:2]) * 100 + int(zt[3:5])
    double_window = st <= ct <= et

    # UK/EI stations:
    if myprimary_pfx in ukei_pfx:
        if hiscontinent == "EU":
            if self.contact.get("Band", 0) in ["3.5", "7"]:
                return 4 + (4 * double_window)
            return 2 + (2 * double_window)
        if self.contact.get("Band", 0) in ["3.5", "7"]:
            return 8 + (8 * double_window)
        return 4 + (4 * double_window)

    # European stations:
    if mycontinent == "EU":
        if hisprimary_pfx in ukei_pfx:
            if self.contact.get("Band", 0) in ["3.5", "7"]:
                return 4
            return 2
        elif hiscontinent == "EU":
            if self.contact.get("Band", 0) in ["3.5", "7"]:
                return 2
            return 1
        if self.contact.get("Band", 0) in ["3.5", "7"]:
            return 4
        return 2

    # DX (Outside Europe)
    if mycontinent != "EU":
        if hisprimary_pfx in ukei_pfx:
            if self.contact.get("Band", "") in ["3.5", "7"]:
                return 8
            return 4
        elif hiscontinent == "EU":
            if self.contact.get("Band", "") in ["3.5", "7"]:
                return 4
            return 2
        if self.contact.get("Band", "") in ["3.5", "7"]:
            return 2
        return 1

    return 0


def show_mults(self):
    """Return display string for mults"""

    query = f"SELECT COUNT(DISTINCT CountryPrefix) as dxcc_count FROM DXLOG WHERE CountryPrefix NOT IN ('EI', 'G', 'GD', 'GI', 'GJ', 'GM', 'GU', 'GW') and ContestNR = {self.pref.get('contest', '1')};"
    result = self.database.exec_sql(query)
    dxcc_count = result.get("dxcc_count", 0)

    query = f"SELECT COUNT(DISTINCT SUBSTR(NR, LENGTH(NR) - 1)) as code_count FROM DXLOG WHERE ContestNR = {self.pref.get('contest', '1')}  and typeof(NR) = 'text';"
    result = self.database.exec_sql(query)
    code_count = result.get("code_count", 0)

    return dxcc_count + code_count


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
                sentnr = str(contact.get("SentNr", "")).upper().split()
                if len(sentnr) == 2:
                    sentnr = sentnr[0].zfill(3) + " " + sentnr[1]
                else:
                    sentnr = sentnr[0].zfill(3) + " --"

                nr = str(contact.get("NR", "")).upper().split()
                if len(nr) == 2:
                    nr = nr[0].zfill(3) + " " + nr[1]
                else:
                    if nr[0][-2:].isalpha():
                        nr = nr[0][:-2].zfill(3) + " " + nr[0][-2:]
                    else:
                        nr = nr[0].zfill(3) + " --"

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
    except IOError as ioerror:
        self.log_info(f"Error saving the log: {ioerror}")
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
