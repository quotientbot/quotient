from enum import Enum, IntEnum


class DayType(IntEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class IdpShareType(IntEnum):
    LEADER_ONLY = 0
    ALL_TEAM_MEMBERS = 1


class RegOpenMsgVar(Enum):
    MENTIONS = "Required Mentions for successful registration."
    SLOTS = "Total no of slots in scrim."
    RESERVED = "No of reserved slots"
    MULTIREG = "Whether multiple registrations are allowed."
    START_TIME = "Actual game start time."
    MAP = "Game Map of the day."


class RegCloseMsgVar(Enum):
    SLOTS = "No of total slots in scrim."
    FILLED = "No of slots filled already."
    TIME_TAKEN = "Time taken to finish reg."
    OPEN_TIME = "Next time when the reg will start."
    MAP = "Game Map of the day."
    START_TIME = "Time when game will start."


class SlotlistMsgVar(Enum):
    NAME = "Registration Channel Name"
    TIME_TAKEN = "Time taken to finish reg."
    OPEN_TIME = "Next time when this reg will start."
    MAP = "Game Map of the day."
    SLOTS = "List of scrims slots."


class MapType(Enum):
    ERANGLE = "ERANGLE"
    MIRAMAR = "MIRAMAR"
    SANHOK = "SANHOK"
    VIKENDI = "VIKENDI"


class ErangleLocation(Enum):
    zharki = (276, 293)
    severny = (1028, 290)
    stalber = (1550, 306)
    kameshki = (1832, 234)
    shooting_range = (868, 437)
    georgopol = (512, 746)
    hospital = (426, 822)
    rozhok = (1084, 784)
    yasnaya = (1452, 644)
    ruins = (756, 888)
    school = (1126, 880)
    mansion = (1700, 815)
    lipovka = (1944, 860)
    prison = (1712, 1008)
    shelter = (1584, 1072)
    gatka = (550, 1078)
    pochinki = (970, 1098)
    farm = (1406, 1240)
    mylta = (1632, 1302)
    power = (2000, 1162)
    quarry = (392, 1434)
    ferry = (712, 1558)
    primorsk = (380, 1658)
    military_base = (1204, 1736)
    novo = (1664, 1666)


class SanhokLocation(Enum):
    khao = (1284, 372)
    ha_tinh = (654, 582)
    tat_mok = (1186, 496)
    mongnai = (1734, 398)
    camp_alpha = (408, 870)
    paradise_resort = (1362, 738)
    camp_bravo = (1880, 830)
    bootcamp = (1040, 1060)
    bhan = (1770, 994)
    ruins = (640, 1432)
    pai_nan = (1004, 1482)
    quarry = (1330, 1332)
    lakawi = (1920, 1206)
    tambang = (502, 1502)
    kampong = (1872, 1570)
    na_kham = (600, 1812)
    cave = (1440, 1642)
    sahmee = (780, 1968)
    camp_charlie = (1300, 1890)
    docks = (1800, 1904)
    ban_tai = (1312, 2050)


class VikendiLocation(Enum):
    port = (816, 382)
    zabava = (990, 396)
    cosmodrome = (1348, 460)
    trevno = (1740, 438)
    krichas = (570, 634)
    coal_mine = (1066, 668)
    peshkova = (1744, 748)
    dobro_mesto = (338, 878)
    goroka = (826, 802)
    mount_kreznic = (1174, 930)
    podvosto = (1396, 988)
    villa = (1000, 1106)
    cement_factory = (1562, 1194)
    castle = (1274, 1300)
    vihar = (432, 1360)
    movatra = (570, 1358)
    dino_park = (800, 1392)
    tovar = (1060, 1292)
    abbey = (1020, 1496)
    volnova = (1330, 1562)
    hot_springs = (1584, 1538)
    milnar = (726, 1784)
    winery = (1156, 1776)
    cantra = (1550, 1642)


class MiramarLocation(Enum):
    ruins = (146, 640)
    la_cobreria = (1200, 606)
    torre_ahumada = (2676, 270)
    campo_militar = (3500, 212)
    el_pozo = (760, 1340)
    los_leones = (2258, 2682)
    monte_nuevo = (900, 2030)
    valle_del_mar = (658, 3018)
    puerto_paraiso = (3136, 3180)
    san_martin = (1938, 1582)
    pecado = (1830, 2142)
    chumacera = (1238, 2722)
    tierra_bronca = (3270, 630)
    los_higos = (1200, 3726)
    power_grid = (1572, 1770)
    minas_generales = (2650, 1862)
    hacienda_del_patron = (1900, 1416)
    junkyard = (2950, 1612)
    crater_fields = (1016, 990)
    minas_del_sur = (558, 3586)
    la_bendita = (2494, 2164)
    impala = (3170, 2390)
    trailer_park = (480, 1020)
    water_treatment = (2152, 934)
    cruz_del_valle = (2750, 762)
    el_azahar = (3250, 1208)
    graveyard = (2384, 1788)
    minas_del_valle = (1090, 3002)
    ladrillera = (900, 2468)
