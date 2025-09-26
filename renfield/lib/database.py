"""
K6GTE, Database class to store contacts
Email: michael.bridak@gmail.com
GPL V3
"""

# pylint: disable=line-too-long

# get Saturday plus 48 hours: select datetime('now', 'WEEKDAY 6','48 HOURS');
# DROP TABLE IF EXISTS t1;

import os
import sqlite3

if __name__ == "__main__":
    print("I'm not the program you are looking for.")


class DataBase:
    """Database class for our database."""

    current_contest = ""

    def __init__(self, database: str, app_data_dir: str):
        """initializes DataBase instance"""
        print(f"Database: {database}")
        self.app_data_dir = app_data_dir

        self.database = app_data_dir + "/" + database
        self.create_dxlog_table()
        self.create_sn_table()

    def reset_database(self):
        """Reset DataBase instance"""
        print(f"Resetting database: {self.database}")
        try:
            os.remove(self.database)
        except OSError:
            ...
        self.create_dxlog_table()
        self.create_sn_table()

    @staticmethod
    def row_factory(cursor, row):
        """
        cursor.description:
        (name, type_code, display_size,
        internal_size, precision, scale, null_ok)
        row: (value, value, ...)
        """
        return {
            col[0]: row[idx]
            for idx, col in enumerate(
                cursor.description,
            )
        }

    def create_sn_table(self) -> None:
        """creates the sn table"""
        print("Creating SN Table")
        try:
            with sqlite3.connect(self.database) as conn:
                cursor = conn.cursor()
                sql_command = (
                    "CREATE TABLE IF NOT EXISTS SN ("
                    "SerialNumber INTEGER DEFAULT 0, "
                    "Call VARCHAR(15) NOT NULL, "
                    "PRIMARY KEY (SerialNumber) );"
                )
                cursor.execute(sql_command)
        except sqlite3.OperationalError as exception:
            print(f"{exception}")

    def create_dxlog_table(self) -> None:
        """creates the dxlog table"""
        print("Creating DXLOG Table")
        try:
            with sqlite3.connect(self.database) as conn:
                cursor = conn.cursor()
                sql_command = (
                    "CREATE TABLE IF NOT EXISTS DXLOG ("
                    "TS DATETIME NOT NULL, "
                    "Call VARCHAR(15) NOT NULL, "
                    "Freq DOUBLE NULL, "
                    "QSXFreq DOUBLE NULL DEFAULT 0, "
                    "Mode VARCHAR(6) DEFAULT '', "
                    "ContestName VARCHAR(10) DEFAULT 'NORMAL', "
                    "SNT VARCHAR(10) DEFAULT '', "
                    "RCV VARCHAR(15) DEFAULT '', "
                    "CountryPrefix VARCHAR(8) DEFAULT '', "
                    "StationPrefix VARCHAR(15) DEFAULT '', "
                    "QTH VARCHAR(25) DEFAULT '', "
                    "Name VARCHAR(20) DEFAULT '', "
                    "Comment VARCHAR(60) DEFAULT '', "
                    "NR INTEGER DEFAULT 0, "
                    "Sect VARCHAR(8) DEFAULT '', "
                    "Prec VARCHAR(1) DEFAULT '', "
                    "CK TINYINT DEFAULT 0, "
                    "ZN TINYINT DEFAULT 0, "
                    "SentNr INTEGER DEFAULT 0, "
                    "Points INTEGER DEFAULT 0, "
                    "IsMultiplier1 TINYINT DEFAULT 0, "
                    "IsMultiplier2 INTEGER DEFAULT 0, "
                    "Power VARCHAR(8) DEFAULT '', "
                    "Band FLOAT NULL DEFAULT 0, "
                    "WPXPrefix VARCHAR(8) DEFAULT '', "
                    "Exchange1 VARCHAR(20) DEFAULT '', "
                    "RadioNR TINYINT DEFAULT 1, "
                    "ContestNR INTEGER, "
                    "isMultiplier3 INTEGER DEFAULT 0, "
                    "MiscText VARCHAR(20) DEFAULT '', "
                    "IsRunQSO TINYINT(1) DEFAULT 0, "
                    "ContactType VARCHAR(1) DEFAULT '', "
                    "Run1Run2 TINYINT NOT NULL, "
                    "GridSquare VARCHAR(6) DEFAULT '', "
                    "Operator VARCHAR(20) DEFAULT '', "
                    "Continent VARCHAR(2) DEFAULT '', "
                    "RoverLocation VARCHAR(10) DEFAULT '', "
                    "RadioInterfaced INTEGER, "
                    "NetworkedCompNr INTEGER, NetBiosName varchar (255), "
                    "IsOriginal Boolean, "
                    "ID TEXT(32) NOT NULL DEFAULT '00000000000000000000000000000000', "
                    "CLAIMEDQSO INTEGER DEFAULT 1,"
                    "Dirty INTEGER DEFAULT 1,"
                    "PRIMARY KEY (`TS`, `Call`) );"
                )
                cursor.execute(sql_command)
                conn.commit()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")

    def get_next_sn(self, call: str) -> int | None:
        """
        Return next serial number.
        Do this by getting the highest SerialNumber from the SN table and adding 1.
        Then write this to the SN table with the call and return the serial number.
        If no call given or call is not a string return None.
        """
        if not isinstance(call, str) or len(call) == 0:
            return None
        call = call.upper()
        try:
            with sqlite3.connect(self.database) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT count(*) from SN where Call = '{call}';")
                call_exists = cursor.fetchone()[0]
                cursor.execute("select max(SerialNumber) as highest from SN;")
                highest = cursor.fetchone()[0]
                if highest is None:
                    highest = 0
                highest += 1
                if call_exists == 0:
                    cursor.execute(
                        f"insert into SN (SerialNumber, Call) values ({highest}, '{call}');"
                    )
                else:
                    cursor.execute(
                        f"update SN set SerialNumber = {highest} where Call = '{call}';"
                    )
                conn.commit()
                return highest
        except sqlite3.Error as exception:
            print(f"DataBase get_next_sn: {exception}")
            return None

    def log_contact(self, contact: dict) -> None:
        """
        Inserts a contact into the db.
        pass in a dict object, see get_empty() for keys
        """

        try:
            with sqlite3.connect(self.database) as conn:
                sql = f"SELECT count(*) from DXLOG where ID ='{contact.get('ID','')}';"
                cur = conn.cursor()
                cur.execute(sql)
                if cur.fetchone()[0] == 0:
                    pre = "INSERT INTO DXLOG("
                    values = []
                    columns = ""
                    placeholders = ""
                    for key in contact.keys():
                        columns += f"{key},"
                        values.append(contact[key])
                        placeholders += "?,"
                    post = f") VALUES({placeholders[:-1]});"
                    sql = f"{pre}{columns[:-1]}{post}"

                    cur.execute(sql, tuple(values))
                    conn.commit()
                else:
                    self.change_contact(contact)
        except sqlite3.Error as exception:
            print(f"DataBase log_contact: {exception}")

    def change_contact(self, qso: dict) -> None:
        """Update an existing contact."""

        pre = "UPDATE dxlog set "
        for key in qso.keys():
            pre += f"{key} = '{qso[key]}',"
        sql = f"{pre[:-1]} where ID='{qso['ID']}';"

        try:
            with sqlite3.connect(self.database) as conn:
                # logger.debug("%s\n%s", sql, qso)
                cur = conn.cursor()
                cur.execute(sql)
                conn.commit()
        except sqlite3.Error as exception:
            print(f"DataBase change_contact: {exception}")

    def delete_contact(self, unique_id: str) -> None:
        """Deletes a contact from the db."""
        if unique_id:
            try:
                with sqlite3.connect(self.database) as conn:
                    sql = f"delete from dxlog where ID='{unique_id}';"
                    cur = conn.cursor()
                    cur.execute(sql)
                    conn.commit()
            except sqlite3.Error as exception:
                print(f"DataBase delete_contact: {exception}")

    def fetch_all_contacts_asc(self) -> list:
        """returns a list of dicts with contacts in the database."""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select * from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE order by TS ASC;"
                )
                return cursor.fetchall()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return ()

    def fetch_all_contacts_desc(self) -> list:
        """returns a list of dicts with contacts in the database."""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select * from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE order by ts desc;"
                )
                return cursor.fetchall()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return ()

    def fetch_last_contact(self) -> dict:
        """returns a list of dicts with last contact in the database."""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute("select * from dxlog order by ts desc;")
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_contact_by_uuid(self, uuid: str) -> dict:
        """returns a list of dicts with last contact in the database."""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(f"select * from dxlog where ID='{uuid}';")
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_cqzn_exists(self, number) -> dict:
        """returns a dict key of nr_count"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as zn_count from dxlog where ZN = '{number}' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_zn_band_count(self) -> dict:
        """
        returns dict with count of unique ZN and Band.
        {nr_count: count}
        """
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(DISTINCT(ZN || ':' || Band)) as zb_count from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_zn_band_mode_count(self) -> dict:
        """
        returns dict with count of unique ZN, Band and Mode.
        {nr_count: count}
        """
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(DISTINCT(ZN || ':' || Band || ':' || Mode)) as zbm_count from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_country_band_count(self) -> dict:
        """
        returns dict with count of unique NR.
        {cb_count: count}
        """
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(DISTINCT(CountryPrefix || ':' || Band)) as cb_count from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_country_count(self) -> dict:
        """
        Fetch count of unique countries
        {dxcc_count: count}
        """
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(DISTINCT(CountryPrefix)) as dxcc_count from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_exchange1_unique_count(self) -> dict:
        """
        Fetch count of unique countries
        {exch1_count: count}
        """
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(DISTINCT(Exchange1)) as exch1_count from dxlog where Exchange1 != '' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_arrldx_country_band_count(self) -> dict:
        """
        returns dict with count of unique NR.
        {nr_count: count}
        """
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(DISTINCT(CountryPrefix || ':' || Band)) as cb_count from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE and points = 3;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_arrldx_state_prov_count(self) -> dict:
        """
        returns dict with count of unique NR.
        {nr_count: count}
        """
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(DISTINCT(NR || ':' || Band)) as cb_count from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE and points = 3;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_nr_count(self) -> dict:
        """
        returns dict with count of unique NR.
        {nr_count: count}
        """
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(DISTINCT NR) as nr_count from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_nr_exists(self, number) -> dict:
        """returns a dict key of nr_count"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as nr_count from dxlog where NR = '{number}' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_call_exists(self, call: str) -> dict:
        """returns a dict key of call_count"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as call_count from dxlog where Call = '{call}' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_nr_exists_before_me(self, number, time_stamp) -> dict:
        """returns a dict key of nr_count"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as nr_count from dxlog where  TS < '{time_stamp}' and NR = '{number}' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_call_count(self) -> dict:
        """
        returns dict with count of unique calls.
        {call_count: count}
        """
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(DISTINCT Call) as call_count from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_wpx_count(self) -> dict:
        """
        returns dict with count of unique WPXPrefix.
        {wpx_count: count}
        """
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(DISTINCT WPXPrefix) as wpx_count from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_dxcc_exists(self, dxcc) -> dict:
        """returns the dict dxcc_count of dxcc existing in current contest."""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as dxcc_count from dxlog where CountryPrefix = '{dxcc}' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_dxcc_exists_before_me(self, dxcc, time_stamp) -> dict:
        """returns the dict dxcc_count of dxcc existing in current contest."""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as dxcc_count from dxlog where TS < '{time_stamp}' and CountryPrefix = '{dxcc}' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_wpx_exists(self, wpx) -> dict:
        """returns a dict key of wpx_count"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as wpx_count from dxlog where WPXPrefix = '{wpx}' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_wpx_exists_before_me(self, wpx, time_stamp) -> dict:
        """returns a dict key of wpx_count"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as wpx_count from dxlog where  TS < '{time_stamp}' and WPXPrefix = '{wpx}' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_sect_band_exists(self, sect, band) -> dict:
        """returns a dict key of sect_count"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as sect_count from dxlog where Sect = '{sect}' and Band = '{band}' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_sect_exists(self, sect) -> dict:
        """returns a dict key of sect_count"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as sect_count from dxlog where Sect = '{sect}' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_sect_exists_before_me(self, sec, time_stamp) -> dict:
        """returns a dict key of sect_count"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as sect_count from dxlog where  TS < '{time_stamp}' and Sect = '{sec}' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_section_band_count(self) -> dict:
        """
        returns dict with count of unique Section/Band.
        {sb_count: count}
        """
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(DISTINCT(Sect || ':' || Band)) as sb_count from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_section_band_count_nodx(self) -> dict:
        """
        returns dict with count of unique Section/Band.
        {sb_count: count}
        """
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    "select count(DISTINCT(Sect || ':' || Band)) as sb_count from dxlog "
                    f"where ContestName = '{self.current_contest}' COLLATE NOCASE and Sect != 'DX';"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def check_dupe_on_band_mode(self, call, band, mode) -> dict:
        """Checks if a call is dupe on band/mode"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as isdupe from dxlog where Call = '{call}' and Mode = '{mode}' and Band = '{band}' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def check_dupe_on_band(self, call, band) -> dict:
        """Checks if a call is dupe on band/mode"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as isdupe from dxlog where Call = '{call}' and Band = '{band}' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def check_dupe(self, call) -> dict:
        """Checks if a call is dupe on band/mode"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as isdupe from dxlog where Call = '{call}' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_points(self) -> dict:
        """return points"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select sum(Points) as Points from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_mult_count(self, mult: int) -> dict:
        """return QSO count"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as count from dxlog where IsMultiplier{mult} = 1 and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_qso_count(self) -> dict:
        """return QSO count"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as qsos from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def fetch_like_calls(self, call: str) -> list:
        """returns a list of dicts with contacts in the database."""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select * from dxlog where call like '%{call}%' and ContestName = '{self.current_contest}' COLLATE NOCASE order by TS ASC;"
                )
                return cursor.fetchall()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return ()

    def get_serial(self) -> dict:
        """Return next serial number"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select max(SentNR) + 1 as serial_nr from DXLOG where ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def get_calls_and_bands(self) -> dict:
        """
        Returns a dict like:
        {'K5TUX': [14.0, 21.0], 'N2CQR': [14.0], 'NE4RD': [14.0]}
        """
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select call, band from DXLOG where ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                result = cursor.fetchall()
                worked_list = {}
                # This converts a list of dicts like:
                # [
                #     {"Call": "K5TUX", "Band": 14.0},
                #     {"Call": "K5TUX", "Band": 21.0},
                #     {"Call": "N2CQR", "Band": 14.0},
                #     {"Call": "NE4RD", "Band": 14.0},
                # ]
                #
                # To:
                # {'K5TUX': [14.0, 21.0], 'N2CQR': [14.0], 'NE4RD': [14.0]}
                for worked_dict in result:
                    call = worked_dict.get("Call")
                    if call in worked_list:
                        bandlist = worked_list[call]
                        bandlist.append(worked_dict["Band"])
                        worked_list[call] = bandlist
                        continue
                    worked_list[call] = [worked_dict["Band"]]
                return worked_list
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def get_like_calls_and_bands(self, call: str) -> dict:
        """
        Returns a dict like:
        {'K5TUX': [14.0, 21.0], 'N2CQR': [14.0], 'NE4RD': [14.0]}
        """
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select call, band from DXLOG where call like '%{call}%' and ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                result = cursor.fetchall()
                worked_list = {}
                # This converts a list of dicts like:
                # [
                #     {"Call": "K5TUX", "Band": 14.0},
                #     {"Call": "K5TUX", "Band": 21.0},
                #     {"Call": "N2CQR", "Band": 14.0},
                #     {"Call": "NE4RD", "Band": 14.0},
                # ]
                #
                # To:
                # {'K5TUX': [14.0, 21.0], 'N2CQR': [14.0], 'NE4RD': [14.0]}
                for worked_dict in result:
                    call = worked_dict.get("Call")
                    if call in worked_list:
                        bandlist = worked_list[call]
                        bandlist.append(worked_dict["Band"])
                        worked_list[call] = bandlist
                        continue
                    worked_list[call] = [worked_dict["Band"]]
                return worked_list
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def get_ops(self) -> list:
        """get dict of unique station operators for contest"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select DISTINCT(Operator) from DXLOG where ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchall()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def get_unique_band_and_mode(self) -> dict:
        """get count of unique band and mode as {mult: x}"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(DISTINCT(band || ':' || mode)) as mult from dxlog where ContestName = '{self.current_contest}' COLLATE NOCASE;"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def get_statistics(self) -> dict:
        """Get QSO count, sum of modes and sum of points in each band

        Band	QSO	CW	PH	DI	Pts
        1.8     9	9	0	0	18
        3.5     2	0	2	0	2
        7.0     33	30	3	0	60
        14.0	141	124	11	0	266
        21.0	128	84	32	0	255
        28.0	31	15	6	0	80
        144.0	4	4	0	0	2

        """

        query = f"""select 
                    Band,
                    count(*) as QSO,
                    sum(sortedmode.mode == 'CW') as CW, 
                    sum(sortedmode.mode == 'PH') as PH, 
                    sum(sortedmode.mode == 'DI') as DI,
                    sum(Points) as Points
                from (
                    select 
                        Band,
                        Points,
                        CASE 
                            WHEN Mode IN ('LSB','USB','SSB','FM','AM') THEN 'PH' 
                            WHEN Mode IN ('CW','CW-R') THEN 'CW' 
                            WHEN Mode In ('FT8','FT4','RTTY','PSK31','FSK441','MSK144','JT65','JT9','Q65', 'PKTUSB', 'PKTLSB') THEN 'DI' 
                            ELSE 'OTHER' 
                        END mode 
                    from DXLOG
                    where ContestName = '{self.current_contest}' COLLATE NOCASE
                    ) as sortedmode
                    
                GROUP by Band
                ORDER by Band;
                """
        try:
            with sqlite3.connect(self.database) as conn:
                # conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(query)
                return cursor.fetchall()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def exec_sql(self, query: str) -> dict:
        """Exec one off queries returning one dict"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(query)
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def exec_sql_mult(self, query: str) -> list:
        """Exec one off queries returning list of dicts"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(query)
                return cursor.fetchall()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return ()

    def check_dupe_on_period_1_mode(
        self, call, band, mode, contest_start_time, contest_time_period_1
    ) -> dict:
        """Checks if a call is dupe on band/mode"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as isdupe from dxlog where Call = '{call}' and Mode = '{mode}' and Band = '{band}' and ContestName = '{self.current_contest}' COLLATE NOCASE AND TS >= '{contest_start_time}' AND TS <= '{contest_time_period_1}';"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def check_dupe_on_period_2_mode(
        self,
        call,
        band,
        mode,
        contest_start_time,
        contest_time_period_1,
        contest_time_period_2,
    ) -> dict:
        """Checks if a call is dupe on band/mode"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as isdupe from dxlog where Call = '{call}' and Mode = '{mode}' and Band = '{band}' and ContestName = '{self.current_contest}' COLLATE NOCASE AND TS >= '{contest_time_period_1}' AND TS <= '{contest_time_period_2}';"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}

    def check_dupe_on_period_3_mode(
        self,
        call,
        band,
        mode,
        contest_start_time,
        contest_time_period_2,
        contest_time_period_3,
    ) -> dict:
        """Checks if a call is dupe on band/mode"""
        try:
            with sqlite3.connect(self.database) as conn:
                conn.row_factory = self.row_factory
                cursor = conn.cursor()
                cursor.execute(
                    f"select count(*) as isdupe from dxlog where Call = '{call}' and Mode = '{mode}' and Band = '{band}' and ContestName = '{self.current_contest}' COLLATE NOCASE AND TS >= '{contest_time_period_2}' AND TS <= '{contest_time_period_3}';"
                )
                return cursor.fetchone()
        except sqlite3.OperationalError as exception:
            print(f"{exception}")
            return {}
