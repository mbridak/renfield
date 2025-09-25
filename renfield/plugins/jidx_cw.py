"""CQ WPX CW plugin"""

# pylint: disable=invalid-name, unused-variable, c-extension-no-member

# JIDX CW Contest
#  	Status:	Active
#  	Geographic Focus:	Japan
#  	Participation:	Worldwide
#  	Mode:	CW
#  	Bands:	160, 80, 40, 20, 15, 10m
#  	Classes:	Single Op All Band (Low/High)
# Single Op Single Band (Low/High)
# Multi-Single
# Multi-Two
# Maritime Mobile
#  	Max power:	HP: >100W
# LP: 100W
#  	Exchange:	JA: RST + Prefecture No.
# non-JA: RST + CQ Zone No.
#  	Work stations:	Once per band
#  	QSO Points:	4 points per JA-DX QSO on 160m
# 2 points per JA-DX QSO on 80m
# 1 points per JA-DX QSO on 40, 20, 15m
# 2 points per JA-DX QSO on 10m
#  	Multipliers:	JA Stations: DXCC countries and CQ zones once per band
# non-JA Stations: JA prefectures plus JD1/O, JD1/MT, JD1/OT once per band
#  	Score Calculation:	Total score = total QSO points x total mults
#  	E-mail logs to:	cw[at]jidx[dot]org
#  	Upload log at:	http://www.jidx.org/upload/uplog.html
#  	Mail logs to:	(none)
#  	Find rules at:	http://www.jidx.org/jidxrule-e.html
#  	Cabrillo name:	JIDX-CW

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

name = "JIDX CW"
cabrillo_name = "JIDX-CW"
mode = "CW"  # CW SSB BOTH RTTY

# 1 once per contest, 2 work each band, 3 each band/mode, 4 no dupe checking
dupe_type = 2


def points(self):
    """Calc point"""

    if self.contact_is_dupe > 0:
        return 0

    pts = {
        1: 4,
        3: 2,
        7: 1,
        14: 1,
        21: 1,
        28: 2,
    }
    mhz = int(int(float(self.contact.get("Freq", 0))) / 1000)
    return pts.get(mhz, 0)


def show_mults(self):
    """Return display string for mults"""
    result = self.database.fetch_nr_count()
    if result:
        return int(result.get("nr_count", 0))
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
        result = self.database.fetch_nr_count()
        mults = int(result.get("nr_count", 0))
        return contest_points * mults
    return 0


def adif(self):
    """Call the generate ADIF function"""
    gen_adif(self, cabrillo_name, "JIDX-CW")


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
    result = self.cty_lookup(self.station.get("Call", ""))
    if result:
        for item in result.items():
            mycountry = item[1].get("entity", "")
            mycontinent = item[1].get("continent", "")
    category = ""
    band = self.contest_settings.get("BandCategory", "")
    if self.contest_settings.get("OperatorCategory", "") == "SINGLE-OP":
        if band == "ALL":
            category = "AB"
        if band == "10M":
            category = "28"
        if band == "15M":
            category = "21"
        if band == "20M":
            category = "14"
        if band == "40m":
            category = "7"
        if band == "80M":
            category = "3.5"
        if band == "160M":
            category = "1.8"
        if self.contest_settings.get("PowerCategory", "") in "LOW QRP":
            category += "L"
    else:
        if self.contest_settings.get("TransmitterCategory", "") == "ONE":
            category = "MOP1"
        else:
            category = "MOP2"

    result = self.database.fetch_qso_count()
    qsos = result.get("qsos", 0)
    result = self.database.fetch_points()
    raw_points = get_points(self)
    result = self.database.fetch_nr_count()
    mults = show_mults(self)
    log = self.database.fetch_all_contacts_asc()
    try:
        with open(filename, "w", encoding=file_encoding, newline="") as file_descriptor:
            output_cabrillo_line(
                "START-OF-LOG: 2.0", "\r\n", file_descriptor, file_encoding
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
                f"CATEGORY: {category}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"CLAIMED-SCORE: {calc_score(self)} ({qsos}-{raw_points}-{mults})",
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
                f"CREATED-BY: Not1MM v{__version__}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"ENTITY: {mycountry}",
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
            output_cabrillo_line(
                f'SENTNR: {self.contest_settings.get("SentExchange", "")}',
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


def recalculate_mults(self):
    """Recalculates multipliers after change in logged qso."""
    all_contacts = self.database.fetch_all_contacts_asc()
    for contact in all_contacts:
        time_stamp = contact.get("TS", "")
        nr = contact.get("NR", "")
        result = self.database.fetch_nr_exists_before_me(nr, time_stamp)
        nr_count = result.get("nr_count", 1)
        if nr_count == 0:
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
