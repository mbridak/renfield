import datetime
from pathlib import Path

try:
    from lib.plugin_common import gen_adif, get_points
    from lib.version import __version__
except (ImportError, ModuleNotFoundError):
    from renfield.lib.plugin_common import gen_adif, get_points
    from renfield.lib.version import __version__

name = "California QSO Party"
mode = "BOTH"  # CW SSB BOTH RTTY
cabrillo_name = "CQP"

# California 4-letter county abbreviations (58 total)
# Used to validate CA station exchanges and for mult checking
CA_COUNTIES = {
    "ALAM",
    "ALPI",
    "AMAD",
    "BUTT",
    "CALA",
    "CCOS",
    "COLU",
    "DELN",
    "ELDO",
    "FRES",
    "GLEN",
    "HUMB",
    "IMPE",
    "INYO",
    "KERN",
    "KING",
    "LAKE",
    "LASS",
    "LANG",
    "MADE",
    "MARN",
    "MARP",
    "MEND",
    "MERC",
    "MODO",
    "MONO",
    "MONT",
    "NAPA",
    "NEVA",
    "ORAN",
    "PLAC",
    "PLUM",
    "RIVE",
    "SACR",
    "SBAR",
    "SBEN",
    "SBER",
    "SCLA",
    "SCRU",
    "SDIE",
    "SFRA",
    "SHAS",
    "SJOA",
    "SIER",
    "SISK",
    "SLUI",
    "SOLA",
    "SONO",
    "STAN",
    "SUTT",
    "SMAT",
    "TEHA",
    "TRIN",
    "TULA",
    "TUOL",
    "VENT",
    "YOLO",
    "YUBA",
}

# US state/province 2-letter abbreviations (63 total: 50 states + 13 Canadian)
# Used for CA station multipliers. DX does not count as a mult for CA stations.
CA_MULTS = {
    # US states
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    # Canadian provinces/territories
    "AB",
    "BC",
    "MB",
    "NB",
    "NL",
    "NT",
    "NS",
    "NU",
    "ON",
    "PE",
    "QC",
    "SK",
    "YT",
}


# 1 once per contest, 2 work each band, 3 each band/mode, 4 no dupe checking
dupe_type = 3


def show_mults(self):
    """Return display string for mults"""
    # CA stations: states/provinces (capped at 58)
    # Non-CA stations: CA counties (capped at 58)
    # The 58 cap is natural since those are the max possible distinct values

    dx = 0
    sql = (
        "select count(DISTINCT Exchange1) as mult_count "
        "from dxlog where "
        f"ContestName = '{self.database.current_contest}' "
        "and typeof(Exchange1) = 'text' "
        "and Exchange1 != 'DX';"
    )
    result = self.database.exec_sql(sql)
    if result:
        dx = result.get("mult_count", 0)

    return min(dx, 58)


def show_qso(self):
    """Return qso count"""
    result = self.database.fetch_qso_count()
    if result:
        return int(result.get("qsos", 0))
    return 0


def calc_score(self):
    """Return calculated score"""
    # Total score = total QSO points x total multipliers (max 58)
    _points = get_points(self)
    _mults = show_mults(self)
    return _points * _mults


def recalculate_mults(self):
    """Recalculates multipliers after change in logged qso."""

    all_contacts = self.database.fetch_all_contacts_asc()
    for contact in all_contacts:
        contact["IsMultiplier1"] = 0

        time_stamp = contact.get("TS", "")
        exch = contact.get("Exchange1", "")
        query = (
            f"select count(*) as exch_count from dxlog where TS < '{time_stamp}' "
            f"and Exchange1 = '{exch.upper()}' "
            f"and ContestName = '{self.database.current_contest}';"
        )
        result = self.database.exec_sql(query)
        count = int(result.get("exch_count", 0))
        if count == 0:
            contact["IsMultiplier1"] = 1

        self.database.change_contact(contact)

    cmd = {}
    cmd["cmd"] = "UPDATELOG"
    if self.log_window:
        self.log_window.msg_from_main(cmd)


def adif(self):
    """Call the generate ADIF function"""
    gen_adif(self, cabrillo_name, "QSO_PARTY")


def output_cabrillo_line(line_to_output, ending, file_descriptor, file_encoding):
    print(
        line_to_output.encode(file_encoding, errors="ignore").decode(),
        end=ending,
        file=file_descriptor,
    )


def cabrillo(self, file_encoding):
    """Generates Cabrillo file."""
    now = datetime.datetime.now().astimezone()
    date_time = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = (
        str(Path.home())
        + "/"
        + f"{self.station.get('Call', '').upper().replace('/', '-')}_{cabrillo_name}_{date_time}.log"
    )
    self.log_info(f"{filename}")
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
                f"CALLSIGN: {self.station.get('Call', '')}",
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
                f"CATEGORY-OPERATOR: {self.contest_settings.get('OperatorCategory', '')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"CATEGORY-ASSISTED: {self.contest_settings.get('AssistedCategory', '')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            output_cabrillo_line(
                f"CATEGORY-BAND: {self.contest_settings.get('BandCategory', '')}",
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
                f"CATEGORY-TRANSMITTER: {self.contest_settings.get('TransmitterCategory', '')}",
                "\r\n",
                file_descriptor,
                file_encoding,
            )
            if self.contest_settings.get("OverlayCategory", "") != "N/A":
                output_cabrillo_line(
                    f"CATEGORY-OVERLAY: {self.contest_settings.get('OverlayCategory', '')}",
                    "\r\n",
                    file_descriptor,
                    file_encoding,
                )
            output_cabrillo_line(
                f"CATEGORY-POWER: {self.contest_settings.get('PowerCategory', '')}",
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
                ops += f"@{self.station.get('Call', '')}"
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

                match themode:
                    case "LSB" | "USB" | "SSB" | "FM" | "AM":
                        themode = "PH"
                    case "CW" | "CW-U" | "CW-L" | "CWR" | "CW-R":
                        themode = "CW"

                freq = contact.get("Freq", "0") / 1000

                frequency = str(round(freq)).rjust(5)

                loggeddate = the_date_and_time[:10]
                loggedtime = the_date_and_time[11:13] + the_date_and_time[14:16]

                sent_nr = str(contact.get("SentNr", "")).strip()
                sent_qth = str(contact.get("Exchange1", "")).upper().strip()

                recv_nr = str(contact.get("NR", "")).strip()

                # In Cabrillo: our sent QTH goes in sent position,
                # their received QTH goes in received position.
                # The Cabrillo format is:
                # QSO: freq mo date time my_call sent_nr sent_qth their_call recv_nr recv_qth
                my_qth = self.contest_settings.get("SentExchange", "").upper()

                output_cabrillo_line(
                    f"QSO: {frequency} {themode} {loggeddate} {loggedtime} "
                    f"{contact.get('StationPrefix', '').ljust(13)} "
                    f"{sent_nr.ljust(6)} "
                    f"{my_qth.ljust(5)} "
                    f"{contact.get('Call', '').ljust(13)} "
                    f"{recv_nr.ljust(6)} "
                    f"{sent_qth.ljust(5)}",
                    "\r\n",
                    file_descriptor,
                    file_encoding,
                )
            output_cabrillo_line("END-OF-LOG:", "\r\n", file_descriptor, file_encoding)
        self.log_info(f"Cabrillo saved to: {filename}")
    except OSError as exception:
        self.log_info("cabrillo: IO error: %s, writing to %s", exception, filename)
        return


def get_mults(self):
    """Get mults for RTC XML"""
    mults = {}
    mults["state"] = show_mults(self)
    return mults


def just_points(self):
    """Get points for RTC XML"""
    return get_points(self)
