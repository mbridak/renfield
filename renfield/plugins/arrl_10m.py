"""
ARRL 10-Meter Contest
Status: Active
Geographic Focus: Worldwide
Participation: Worldwide
Mode: CW, Phone
Bands: 10m Only
Classes: Single Op (QRP/Low/High)(CW/Phone/Mixed)
Single Op Unlimited (QRP/Low/High)(CW/Phone/Mixed)
Single Op Overlay: (Limited Antennas)
Multi-Single (Low/High)
Max operating hours: 36 hours
Max power: HP: 1500 watts
LP: 100 watts
QRP: 5 watts
Exchange: W/VE: RST + State/Province
XE: RST + State
DX: RST + Serial No.
MM: RST + ITU Region
QSO Points: 2 points per Phone QSO
4 points per CW QSO
Multipliers: Each US State + DC once per mode
Each VE Province/Territory once per mode
Each XE State once per mode
Each DXCC Country once per mode
Each ITU Region (MM only) once per mode
Score Calculation: Total score = total QSO points x total mults
Find rules at: <http://www.arrl.org/10-meter>
Cabrillo name: ARRL-10


Scoring: Each phone contact counts for two (2) QSO points. Each CW contact counts for four (4) QSO
points. To calculate your final score, multiply the total QSO points by the number of US states (plus the
District of Columbia), Canadian Provinces and Territories, Mexican states, DXCC entities, and ITU
regions you contacted. Each multiplier counts once on phone and once on CW

Scoring Example: KA1RWY makes 2235 contacts including 1305 phone QSOs, and 930 CW QSOs, for
a total of 6330 QSO points. On phone, she works 49 states, 10 Canadian provinces, 3 Mexican states, 20
DXCC entities and a maritime mobile station in Region 2 for a total of 49+10+3+20+1 = 83 phone
multipliers. On CW she works 30 states, 8 Canadian provinces, 1 Mexican state, and 18 DXCC entities
for a total of 30+8+1+18 = 57 CW multipliers. Her final score = 6330 QSO points x (83+57) multipliers =
6330 x 140 = 886,200 points.


"""

# pylint: disable=invalid-name, unused-argument, unused-variable, c-extension-no-member

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

name = "ARRL 10M"
mode = "BOTH"  # CW SSB BOTH RTTY
cabrillo_name = "ARRL-10"

# 1 once per contest, 2 work each band, 3 each band/mode, 4 no dupe checking
dupe_type = 3


def show_mults(self, rtc=None):
    """Return display string for mults"""
    # CountryPrefix, integer

    us_ve_mx = 0
    mm = 0
    dx = 0

    sql = (
        "select count(DISTINCT(NR || ':' || Mode)) as mult_count "
        f"from dxlog where ContestNR = {self.database.current_contest} and typeof(NR) = 'text';"
    )
    result = self.database.exec_sql(sql)
    if result:
        us_ve_mx = result.get("mult_count", 0)

    # MM
    sql = (
        "select count(DISTINCT(NR || ':' || Mode)) as mult_count "
        f"from dxlog where ContestNR = {self.database.current_contest} "
        "and typeof(NR) = 'integer' "
        "and call like '%/MM';"
    )
    result = self.database.exec_sql(sql)
    if result:
        mm = result.get("mult_count", 0)

    # DX
    sql = (
        "select count(DISTINCT(CountryPrefix || ':' || Mode)) as mult_count "
        f"from dxlog where ContestNR = {self.database.current_contest} "
        "and typeof(NR) = 'integer' "
        "and call not like '%/MM';"
    )
    result = self.database.exec_sql(sql)
    if result:
        dx = result.get("mult_count", 0)

    if rtc is not None:
        return dx, us_ve_mx + mm

    return us_ve_mx + mm + dx


def show_qso(self):
    """Return qso count"""
    result = self.database.fetch_qso_count()
    if result:
        return int(result.get("qsos", 0))
    return 0


def calc_score(self):
    """Return calculated score"""
    # Multipliers: Each US State + DC once per mode
    _points = get_points(self)
    _mults = show_mults(self)
    _power_mult = 1
    # if self.contest_settings.get("PowerCategory", "") == "QRP":
    #     _power_mult = 2
    return _points * _power_mult * _mults


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
                    f"CLUB: {self.station.get('Club', '')}",
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
        self.log_info(f"Error saving log: {ioerror}")
        return


def recalculate_mults(self):
    """Recalculates multipliers after change in logged qso."""


def get_mults(self):
    """"""
    mults = {}
    mults["country"], mults["state"] = show_mults(self, rtc=True)
    return mults


def just_points(self):
    """"""
    return get_points(self)
