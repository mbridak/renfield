"""
His Maj. King of Spain Contest, CW
Status:	            Active
Geographic Focus:	Worldwide
Participation:	    Worldwide
Awards:	            Worldwide
Mode:	            CW
Bands:	            160, 80, 40, 20, 15, 10m
Classes:	        Single Op All Band (QRP/Low/High)
                    Single Op All Band Youth
                    Single Op Single Band
                    Multi-Op (Low/High)
Max power:	        HP: >100 watts
                    LP: 100 watts
                    QRP: 5 watts
Exchange:	        EA: RST + province
                    non-EA: RST + Serial No.
Work stations:	    Once per band
QSO Points:	        (see rules)
Multipliers:	    Each EA province once per band
                    Each EADX100 entity once per band
                    Each special (EA0) station once per band
Score Calculation:	Total score = total QSO points x total mults
E-mail logs to:	    (none)
Upload log at:	    https://concursos.ure.es/en/logs/
Mail logs to:	    (none)
Find rules at:	    https://concursos.ure.es/en/s-m-el-rey-de-espana-cw/bases/
Cabrillo name:	    EA-MAJESTAD-CW
"""

# pylint: disable=invalid-name, unused-argument, unused-variable, c-extension-no-member

# EA1: AV, BU, C, LE, LO, LU, O, OU, P, PO, S, SA, SG, SO, VA, ZA
# EA2: BI, HU, NA, SS, TE, VI, Z
# EA3: B, GI, L, T
# EA4: BA, CC, CR, CU, GU, M, TO
# EA5: A, AB, CS, MU, V
# EA6: IB
# EA7: AL, CA, CO, GR, H, J, MA, SE
# EA8: GC, TF
# EA9: CE, ML


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

name = "His Maj. King of Spain Contest, CW"
mode = "CW"  # CW SSB BOTH RTTY
cabrillo_name = "EA-MAJESTAD-CW"

# 1 once per contest, 2 work each band, 3 each band/mode, 4 no dupe checking
dupe_type = 2


def points(self) -> int:
    """
    Calculate the points for this contact.
    """
    # EA: 2 points per QSO with EA
    # EA: 1 point per QSO with non-EA
    # non-EA: 3 points per QSO with EA
    # non-EA: 1 point per QSO with non-EA

    if self.contact_is_dupe > 0:
        return 0

    ea_prefixes = ["EA", "EA1", "EA2", "EA3", "EA4", "EA5", "EA6", "EA7", "EA8", "EA9"]

    me = None
    him = None

    result = self.cty_lookup(self.station.get("Call", ""))
    if result:
        for item in result.items():
            me = item[1].get("primary_pfx", "")

    result = self.cty_lookup(self.contact.get("Call", ""))
    if result:
        for item in result.items():
            him = item[1].get("primary_pfx", "")

    if me is not None and him is not None:
        if me in ea_prefixes and him in ea_prefixes:
            return 2
        elif me in ea_prefixes and him not in ea_prefixes:
            return 1
        elif me not in ea_prefixes and him in ea_prefixes:
            return 3
        else:
            return 1

    return 1


def show_mults(self, rtc=None) -> int:
    """Return display string for mults"""

    ea_provinces = 0
    # dx = 0
    ef0f = 0
    eadx100 = 0

    # Each EADX100 entity once per band
    sql = (
        "select count(DISTINCT(CountryPrefix || ':' || Band)) as mult_count "
        f"from dxlog where ContestNR = {self.database.current_contest};"
    )
    result = self.database.exec_sql(sql)
    if result:
        eadx100 = result.get("mult_count", 0)

    # Each EA province once per band
    sql = (
        "select count(DISTINCT(NR || ':' || Band)) as mult_count "
        f"from dxlog where ContestNR = {self.database.current_contest} and typeof(NR) = 'text';"
    )
    result = self.database.exec_sql(sql)
    if result:
        ea_provinces = result.get("mult_count", 0)

    # # Each USA, VE, JA or VK call area once per band
    # sql = (
    #     "select count(DISTINCT(CountryPrefix || ':' || substr(WPXPrefix, -1) || ':' || Band)) as mult_count "
    #     f"from dxlog where CountryPrefix in ('K', 'VE', 'VK', 'JA') and ContestNR = {self.database.current_contest};"
    # )
    # result = self.database.exec_sql(sql)
    # if result:
    #     dx = result.get("mult_count", 0)

    # Each QSO with EF0F/8 once per band
    sql = (
        "select count(DISTINCT(Band)) as mult_count "
        f"from dxlog where Call = 'EF0F/8' and ContestNR = {self.database.current_contest};"
    )
    result = self.database.exec_sql(sql)
    if result:
        ef0f = result.get("mult_count", 0)

    if rtc is not None:
        return 0, 0

    return ea_provinces + ef0f + eadx100


def show_qso(self) -> int:
    """Return qso count"""
    result = self.database.fetch_qso_count()
    if result:
        return int(result.get("qsos", 0))
    return 0


def calc_score(self) -> int:
    """Return calculated score"""
    _points = get_points(self)
    _mults = show_mults(self)

    return _points * _mults


def adif(self) -> None:
    """Call the generate ADIF function"""
    gen_adif(self, cabrillo_name, contest_id=cabrillo_name)


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
                if themode == "RTTY":
                    themode = "RY"
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


def recalculate_mults(self) -> None:
    """Recalculates multipliers after change in logged qso."""


def get_mults(self):
    """"""
    mults = {}
    mults["country"], mults["state"] = show_mults(self, rtc=True)
    return mults


def just_points(self):
    """"""
    return get_points(self)
