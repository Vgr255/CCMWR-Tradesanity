"""Convert CrossCode Traders (from database.json) into a human-readable format."""

from __future__ import annotations

import json

BANNED = [ # all of these are listed in the order they appear in the database.json file
    "vermillionWeapon1_old",
    "testing",
    "defaultHeal",
    "defaultRegen",
    "defaultBuffsSingle",
    "defaultBuffsDouble",
    "defaultBuffsAllround",
    "defaultBuffsWrapRolls",
    "defaultMetal",
    "defaultDefault",
    "bergenLoot2",
    "bergenMetal", # this one is the pre-New Metals quest
    "sapphireBuffs3", # some additional ridge traders planned but never used?
    "sapphireBuffs4", # they all have different consumables to sell, too
    "sapphireBuffs5", # shame, really.
    "glitchTrader", # lunatic paws uwu (is quest + behind arena)
    "bakiMetal",
    "bakiBrewing_1",
    "bakiBrewingAuto",
    "basinBuffs3",
    "papagangQuestTrade",
    "villageFood",
    "villageEquip1",
    "turretDefTrader",
    "rhombusEquipAntique2",
    "rhombusBuffsSpecial",
    "rhombusPostEquipArena1", # arena DLC traders
    "rhombusPostEquipArena2", # 1 is weapons, 2 is other gear
    "tremorTrader1", # this is technically a dupe, but is quest-related
    "tremorTrader2", # DLC quest etc.
    "rhombusDlcLoot1", # DLC trader for Azure before Ku'lero
    "rookieHeal",
    "rookieHeal2",
    "rookieBuffs1", # all of these are the early versions of other traders
    "rookieBuffs2",
    "rookieBuffs3",
    "rookieBuffs4",
    "rookieSteaks1", # ms.teak quest
    "rookieSteaks2",
    "rookieNorthBuffs2", # more early versions
    "rookieNorthBuffs3",
    "rookieNorthBuffs4",
    "rookieRiseMetal1", # this upgrade chain might be quest-gated, unsure
    "rookieRiseMetal2",
    "rookieFallMetal1",
    "rookieFallMetal2",
    "rookieKontorMeat1",
    "rookieKontorFruitA1",
    "rookieKontorFruitB1",
    "rookieKontorBracer1",
    "rookieKontorBracer2",
    "rookieKontorBags1",
    "rookieReset",
]

ONLY_DLC_OFF = [
    "bakiBrewing_2",
]

AREA_OVERRIDE = {
    # pond slum pass
    "basinEastShadyBuffs": "open11",
    "basinEastExcalibro": "open11",
    "basinEastDrill": "open11",
    "basinEastRevolver": "open11",
    "basinEastBanditScarf": "open11",
    "basinEastStick": "open11",
    # v'rda vil 
    "villageMaterials": "open10.Right",
    "villageSets": "open10.Right",
    "villageMetals": "open10.Right",
    # turret defense (in grove, apparently)
    "turretDefTraderUpg": "open10.Grove",
    "turretDefTrader2": "open10.Grove",
    # north rookie traders
    "rookieSetsFall": "open8",
    "rookieNorthHeals": "open8",
    "rookieNorthBuffs": "open8",
    "rookieNorthBuffs2Ext": "open8",
    "rookieNorthBuffs3Ext": "open8",
    "rookieNorthBuffs4Ext": "open8",
    "rookieRiseMetal3": "open8",
    "rookieNorthWeaponTorso": "open8",
    "rookieFallMetal3": "open8",
    "rookieNorthHeadLegs": "open8",
    "rookieLootFall1": "open8",
    "rookieKontorMeat2": "open8",
    "rookieKontorFruitA2": "open8",
    "rookieKontorFruitB2": "open8",
    "rookieKontorBracer3": "open8",
    "rookieKontorBags2": "open8",
}

AREAS: dict[str, str] = {}
ENEMIES: dict[str, str] = {}
ENEMY_LOCS: dict[str, str] = {}
TRADERS: dict[str, Trader] = {}

ITEMS: list[Item] = []

# A lot of the regions in the game's JSON are "proper" regions
# Need to make sure we have proper granulation of every region
# Especially with the temples and Closed Gaia
# Also needs split areas (e.g. Basin Keep+Pond Slums, North Rookie Harbor)
# Every area where a plant or enemy can be found (i.e. drops) needs to be in there

# These regions will be used for logic of what is locked where
# For tradesanity, we want to add all trade outcomes as location checks
# but we also need to make sure we CAN do these trades, for spheres
# so each item needs to check its location and keep track of it in logic
# this could also be used for if we want the items we trade away to be in logic

REGIONS = {
    "open2": ["Rookie Harbor"],
    "open3": ["Autumn's Rise", "Bergen Trail", "Bergen Village"],
    "open3.1": "guild pass cutscene",
    "open4.x": ["Temple Mine"],
    "open5": ["Maroon Valley", "Ba'kii Kum"],
    "open6": "maroon cave",
    "open7.x": ["Faj'ro Temple"],
    "open8": "north rookie harbor",
    "open9": ["Autumn's Fall"],
    "open10": ["Gaia's Garden", "Basin Keep"],
    "open10.Left": ["So'najiz Temple", "lower left gaia's garden"],
    "open10.Right": ["Zir'vitar Temple", "lower right gaia's garden"],
    "open10.Mid": "upper middle gaia's garden (path to the temples)",
    "open10.Grove": "upper left gaia's garden",
    "open10.Infested": ["Infested Marshes"],
    "open11": "basin keep pond slums",
    "open13.x": "later zir'vitar",
    "open14.x": "later so'najiz",
    "open15.x": ["Grand Krys'kajo"],
    "open16": ["Sapphire Ridge"],
    "open16.1": ["Ascension Temple"],
    "open17": "old dojo interior",
    "open18": ["Vermillion Wasteland"],
    "open19": ["Vermillion Tower"], # dungeon too? unsure
    "open20": ["Rhombus Square"],
    "openDLC1": ["Homestedt"],
    "openDLC_Beach": ["Azure Archipelago"],
    "openDLC_Dungeon*": ["Ku'lero Temple"],
}

REGIONS_MAP = {x:k for k,v in REGIONS.items() for x in v}

_n = lambda x: x["name"]["en_US"]

class Item:
    def __init__(self, d: dict):
        self.name = _n(d)
        self.areas: list[str] = []
        self.enemies: list[str] = []
        self._traders: list[str] = []
        self.plants: list[str] = []
        self.trader_types: list[str] = []

        for x in d.get("sources", ()):
            match x["type"]:
                case "CHEST":
                    self.areas.append(AREAS[x["value"]])
                case "ENEMY":
                    self.enemies.append(ENEMIES[x["value"]])
                case "TRADER":
                    self._traders.append(x["value"])
                case "PLANT":
                    self.plants.append(x["value"])
                case "OTHER": # mostly traders
                    v = x["value"]
                    match v["type"]: # sometimes a certain "baggy-kun-test" can drop it
                        # but that's like beta stuff, ignore
                        # we only care about truck-kun in here
                        case "TRADER":
                            self.trader_types.append(v["value"])

    @property
    def traders(self) -> list[Trader]:
        return [TRADERS[x] for x in self._traders]

class Trade:
    def __init__(self, d: dict, i: int):
        if len(d["get"]) != 1:
            raise AttributeError
        self.result = ITEMS[int(d["get"][0]["id"])]
        self.amount = d["get"][0]["amount"]
        self.index = i
        self.cost = []
        for s in d["require"]:
            self.cost.append( ( ITEMS[int(s["id"])].name, s["amount"] ) )

    def to_json(self):
        res = self.result.name
        if self.amount > 1:
            res = f"{res} x{self.amount}"
        return {
            res:
            {
                "reward": ["item", self.result.name, self.amount],
                "condition": self.cost,
                "location": {"index": self.index}
            }
        }

class Trader2: # unused atm
    def __init__(self, name: str):
        self.name = name
        self.internal_names: list[str] = []
        self.trades: list[list[Trade]] = []
        self.upgrade_chain: list[str] = []
        self.tracking: list[bool] = []
        self.conditions: list[None | tuple[str, str]] = []

    def add_trader(self, d: dict, internal: str):
        self.internal_names.append(internal)
        self.upgrade_chain.append(d.get("upgradeTo"))
        self.tracking.append(d.get("noTrack", False))
        index = len(self.internal_names) - 1
        trades = []
        for i, t in enumerate(d["options"]):
            try:
                trades.append(Trade(t, i, index))
            except AttributeError:
                pass

        self.trades.append(trades)

    def to_json(self):
        """Validate the data and export to JSON."""

class Trader:
    def __init__(self, d: dict, internal: str):
        self.name = _n(d)
        self.internal = internal
        self.area = AREAS[d["area"]]
        self.trades: list[Trade] = []
        self.is_dlc = d.get("noTrack", False) # not entirely true, but close enough?
        self.upgrade_to = d.get("upgradeTo")
        for i, t in enumerate(d["options"]):
            try:
                self.trades.append(Trade(t, i))
            except AttributeError:
                pass

    def to_json(self):
        """Return a two-tuple to fit into a bigger dict."""
        trades = {}
        for trade in self.trades:
            key, values = trade.to_json().popitem()
            while key in trades:
                key += "_"
            trades[key] = values
        meta = {}
        if self.is_dlc:
            meta["dlc"] = True
        if self.internal in ONLY_DLC_OFF:
            meta["dlc"] = False
        region = REGIONS_MAP.get(self.area, self.area)
        region = AREA_OVERRIDE.get(self.internal, region)
        return {
            self.internal:
            {
                "location": {
                    "trader": self.name,
                    "area": self.area,
                },
                "region": {
                    "open": region,
                },
                "condition": [], # this will likely need manual intervention
                "metadata": meta,
                "trades": trades,
            }
        }

def extract():
    """Extract the JSONs into meaningful variables."""
    with open("database.json") as f:
        data = json.load(f)

    # Store a mapping of {internal: readable} names
    # where the internal one is what the game uses
    # and readable is what we see in-game
    for k,v in data["areas"].items():
        AREAS[k] = _n(v)

    # Store a mapping of {internal: readable} enemy names
    # Also store the area that each enemy appears in
    for k,v in data["enemies"].items():
        if v["area"]: # one enemy does not
            ENEMIES[k] = n = _n(v)
            ENEMY_LOCS[n] = AREAS[v["area"]]

    with open("item-database.json") as f:
        j = json.load(f)

    for i in j["items"]:
        ITEMS.append(Item(i))

    for k,v in data["traders"].items():
        tr = Trader(v, k)
        if tr.trades and tr.internal not in BANNED:
            TRADERS[k] = tr

    final = {}

    for trader in TRADERS.values():
        final.update(trader.to_json())

    with open("trades-converted.json", "w") as fw:
        json.dump(final, fw, indent=4)
