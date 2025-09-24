""" """

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

name = "ES OPEN"
cabrillo_name = "ES-OPEN"
mode = "BOTH"  # CW SSB BOTH RTTY

# 5 Contest specific dupe check.
dupe_type = 5


def specific_contest_check_dupe(self, call):
    """Dupe checking specific to just this contest."""

    # constant to split the contest
    contest_length_in_minutes = 60
    split_contest_by_minutes = 20

    period_count = int(contest_length_in_minutes / split_contest_by_minutes)

    # think about generic solution by splitting the contest to n different periods
    start_date_init = self.contest_settings.get("StartDate", "")
    self.contest_start_date = start_date_init.split(" ")[0]
    self.contest_start_time = start_date_init.split(" ")[1]

    start_date_init_date = datetime.datetime.strptime(
        start_date_init, "%Y-%m-%d %H:%M:%S"
    )

    # Create time periods dynamically based on period count
    time_periods = []
    for i in range(period_count):
        minutes_to_add = split_contest_by_minutes * (i + 1)
        time_period = start_date_init_date + datetime.timedelta(minutes=minutes_to_add)
        time_periods.append(time_period)

    # Assign to variables for backwards compatibility
    time_period_1 = time_periods[0] if len(time_periods) > 0 else None
    time_period_2 = time_periods[1] if len(time_periods) > 1 else None
    time_period_3 = time_periods[2] if len(time_periods) > 2 else None

    # get current time in UTC
    iso_current_time = datetime.datetime.now(datetime.timezone.utc)
    current_time = iso_current_time.replace(tzinfo=None)

    result = {}
    result["isdupe"] = False

    if current_time < time_period_1:
        start_date_init = self.contest_start_date + " " + self.contest_start_time

        result = self.database.check_dupe_on_period_1_mode(
            call,
            self.contact.get("Band", ""),
            mode,
            start_date_init,
            time_period_1.strftime("%Y-%m-%d %H:%M:%S"),
        )

    elif current_time < time_period_2 and current_time >= time_period_1:
        start_date_init = self.contest_start_date + " " + self.contest_start_time

        result = self.database.check_dupe_on_period_2_mode(
            call,
            self.contact.get("Band", ""),
            mode,
            start_date_init,
            time_period_1.strftime("%Y-%m-%d %H:%M:%S"),
            time_period_2.strftime("%Y-%m-%d %H:%M:%S"),
        )

    elif current_time < time_period_3 and current_time >= time_period_2:
        start_date_init = self.contest_start_date + " " + self.contest_start_time

        result = self.database.check_dupe_on_period_3_mode(
            call,
            self.contact.get("Band", ""),
            mode,
            start_date_init,
            time_period_2.strftime("%Y-%m-%d %H:%M:%S"),
            time_period_3.strftime("%Y-%m-%d %H:%M:%S"),
        )

    return result


def points(self):
    """ """
    if self.contact_is_dupe > 0:
        return 0

    _mode = self.contact.get("Mode", "")
    if _mode in "SSB, USB, LSB, FM, AM":
        return 1
    if _mode in "CW":
        return 2

    return 0


def show_mults(self, rtc=None):
    """Return display string for mults"""
    our_prefix = calculate_wpx_prefix(self.station.get("Call", ""))
    query = f"SELECT count(DISTINCT(substr(WPXPrefix,3,1) || ':' || Band || ':' || Mode)) as mults from DXLOG where ContestNR = {self.pref.get('contest', '1')} AND CountryPrefix = 'ES' AND WPXPrefix != '{our_prefix}';"
    result = self.database.exec_sql(query)
    if result:
        mult_count = result.get("mults", 0)
        return mult_count
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
        mults = show_mults(self)
        return contest_points * (mults + 1)
    return 0


def recalculate_mults(self):
    """Recalculates multipliers after change in logged qso."""


def adif(self):
    """Call the generate ADIF function"""
    gen_adif(self, cabrillo_name, "ES OPEN")


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
                if themode == "LSB" or themode == "USB":
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
    except IOError:
        return


def get_mults(self):
    """Get mults for RTC XML"""
    mults = {}
    mults["country"], mults["state"] = show_mults(self, rtc=True)
    return mults


def just_points(self):
    """Get points for RTC XML"""
    return get_points(self)
