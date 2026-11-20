from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
import random
from typing import Any

MAX_HEALTH = 20

PROGRAM_NAMES = (
    "Attack", "Area Attack", "Piercing Attack", "Slow", "Virus", "Silence",
    "Confuse", "Weaken", "Shield", "Smoke", "Decoy", "Medic", "Armor",
    "Hide", "Deceive", "Relocate", "Analyze", "Scan", "Evaluate", "Decrypt",
    "Reflect", "Attack Boost", "Defense Boost", "Stealth Boost",
    "Analysis Boost", "Client Program",
)
INITIAL_PROGRAMS = {0, 5, 9, 11, 12, 13, 14, 16, 17, 18, 19}
DEFAULT_PROGRAMS = set(INITIAL_PROGRAMS)
PROGRAM_COMPLEXITY = (2, 3, 3, 2, 3, 3, 4, 2, 3, 1, 4, 4, 3, 3, 2, 2, 1, 1, 1, 2, 4, 3, 3, 3, 3, 4)
PROGRAM_BRANDS = (
    ("Zap", "Magnum", "IceBreaker", "CyberSword"),
    ("Grenade", "Logic Bomb", "BugSwarm", "EMP"),
    ("Spear", "Laser", "IcePick", "Shredder"),
    ("Slow", "Bind", "Goo", "Freeze"),
    ("Flu", "Pneumonia", "RotWorms", "Ebola"),
    ("Silence", "Muffler", "QuietYou", "MegaMute"),
    ("Confusion", "Gremlins", "Lobotomy", "BrainFry"),
    ("Weaken", "Shrink", "Decrepify", "Impotence"),
    ("Shield", "Buckler", "Blocker", "Aegis"),
    ("Smoke", "Haze", "FogBank", "Whiteout"),
    ("Decoy", "Doppelganger", "Ghost", "Mimic"),
    ("Medic", "Repair", "PatchKit", "Phoenix"),
    ("Armor", "Plate", "Bastion", "Citadel"),
    ("Hide", "Cloak", "Stealth", "Vanish"),
    ("Deceive", "Disguise", "Spoof", "Chameleon"),
    ("Relocate", "Shift", "Warp", "Escape"),
    ("Analyze", "Probe", "Examiner", "Omniscient"),
    ("Scan", "Mapper", "Surveyor", "Cartographer"),
    ("Evaluate", "Appraiser", "Auditor", "Assessor"),
    ("Decrypt", "Key", "CipherBreaker", "Crack"),
    ("Reflect", "Mirror", "ReturnFire", "Rebound"),
    ("Attack Boost", "Overclock", "Amplifier", "Overdrive"),
    ("Defense Boost", "Fortify", "Harden", "Bulwark"),
    ("Stealth Boost", "Mask", "Shade", "Phantom"),
    ("Analysis Boost", "Focus", "Insight", "Clarity"),
    ("Client", "Client", "Client", "Client"),
)

HARDWARE_NAMES = (
    "Chip Burner", "Surge Suppressor", "Neural Damper", "Trace Monitor",
    "Bio Monitor", "High Bandwidth Bus", "Proximity Mapper", "Design Assistant",
    "AntiTrace Proxy",
)
CHIP_NAMES = ("CPU", "Attack", "Defense", "Stealth", "Analysis", "Coprocessor")
LIFESTYLES = ("Poverty", "Lower Class", "Middle Class", "Upper Class", "Elite")
LIFESTYLE_COST = (500, 1000, 2000, 4000, 10000)
MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December",
)
CORPORATIONS = (
    "Ares Macrotechnology", "Aztechnology", "Cross Applied Technologies", "Fuchi Industrial Electronics",
    "Mitsuhama Computer Technologies", "Renraku Computer Systems", "Saeder-Krupp", "Shiawase Corporation",
    "Yamatetsu", "Universal Omnitech", "Wuxing Incorporated", "Novatech",
)

CONTRACT_TYPES = (
    "Steal", "Steal and Erase", "Erase", "Edit", "Deactivate I/O", "Activate I/O",
    "Sabotage I/O", "Crash System", "Install Backdoor", "Run Client Program",
)
TARGETS = (
    "Research Data", "Chemical Formula", "Personnel Files", "Financial Data", "Grade Reports",
    "Security Files", "Security Camera Recordings", "Blueprints", "Employee Evaluations",
    "Product Information", "Medical Records", "Illegal Activity Records", "Test Results",
    "Inventory Data", "Door Locks", "Security Cameras", "Alarm Systems", "Fire Alarms",
    "Security Alarms", "Radiation Alarms", "Biohazard Alarms", "Chemical Alarms",
    "Manufacturing Controls", "Chemical Production", "Vault Controls", "Central Processor",
    "I/O Node", "Datastore Node", "CPU Node",
)
FILE_TARGET_TYPES = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)
NODE_TYPE_NAMES = ("CPU", "SPU", "Coprocessor", "Datastore", "I/O", "Junction", "Portal In", "Portal Out")
ICE_TYPE_NAMES = ("Gateway", "Probe", "Guardian", "Tapeworm", "Attack IC", "Trace IC")


def die_roll(target: int) -> int:
    target = min(target, 20)
    roll = random.randint(1, 20)
    if roll == 1:
        return -1
    if roll < target:
        return 0
    return min(5, max(1, (roll - target + 4) // 4))


def compute_damage(success: int) -> int:
    return max(0, success) ** 2


def program_size(class_id: int, rating: int) -> int:
    return max(1, PROGRAM_COMPLEXITY[class_id] * rating)


def software_price(class_id: int, rating: int) -> int:
    return 100 * PROGRAM_COMPLEXITY[class_id] * rating * rating


def chip_price(chip_type: int, rating: int) -> int:
    return CHIP_BASE_PRICE[chip_type] * rating * rating


HARDWARE_BASE_PRICE = (1000, 500, 1000, 250, 500, 500, 2000, 2000, 1500)
HARDWARE_MAX_LEVEL = (4, 5, 5, 3, 2, 5, 1, 3, 1)
CHIP_BASE_PRICE = (150, 100, 100, 100, 100, 125)


def hardware_price(hardware_type: int, rating: int) -> int:
    return HARDWARE_BASE_PRICE[hardware_type] * (1 << (max(1, rating) - 1))


@dataclass
class Program:
    class_id: int
    rating: int = 1
    name: str = ""
    load_default: bool = False
    loaded: bool = False
    sound: int = 0

    def __post_init__(self) -> None:
        if not self.name:
            brand_index = min(3, max(0, (self.rating - 1) // 5))
            self.name = f"{PROGRAM_BRANDS[self.class_id][brand_index]} {self.rating}.0"

    @property
    def size(self) -> int:
        return program_size(self.class_id, self.rating)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Program:
        return cls(**value)


@dataclass
class Contract:
    corporation: int
    system_name: str
    size: int
    contract_type: int
    target: int
    difficulty: int
    pay: int
    days_left: int
    target_count: int = 1
    no_alarms: bool = False
    timed: bool = False
    time_limit: int = 0

    @classmethod
    def generate(cls, reputation: int) -> Contract:
        corporation = random.randrange(len(CORPORATIONS))
        difficulty = min(20, max(1, 2 + reputation // 4 + random.randrange(5)))
        size = 2 + difficulty // 4
        contract_type = random.randrange(len(CONTRACT_TYPES))
        if contract_type in (0, 1, 2, 3):
            target = random.choice(FILE_TARGET_TYPES)
        elif contract_type == 4:
            target = random.choice(range(14, 17))
        elif contract_type == 5:
            target = random.choice(range(17, 22))
        elif contract_type == 6:
            target = random.choice(range(22, 25))
        elif contract_type == 9:
            target = random.choice((26, 27, 28))
        else:
            target = 25
        target_count = 1 + (1 if contract_type in (0, 1, 2) and random.random() < 0.25 else 0)
        pay = 250 * difficulty * target_count + random.randint(0, 150)
        timed = random.random() < 0.15
        time_limit = random.choice((15, 20, 30)) if timed else 0
        return cls(
            corporation, CORPORATIONS[corporation], size, contract_type, target,
            difficulty, pay, random.randint(3, 10), target_count,
            random.random() < 0.2, timed, time_limit,
        )

    @property
    def description(self) -> str:
        noun = TARGETS[min(self.target, len(TARGETS) - 1)].lower()
        descriptions = (
            f"A client needs access to {noun} from the {self.system_name} system. You must recover a copy of this data.",
            f"A client desires sole access to {noun} from the {self.system_name} system. Recover a copy and erase it from the system.",
            f"A client wishes to destroy {noun} on the {self.system_name} system. Locate and erase the data.",
            f"A client wishes to alter {noun} on the {self.system_name} system. Locate and edit the data.",
            f"A client wishes to deactivate {noun} from the {self.system_name} system. Locate its I/O node and deactivate it.",
            f"A client wishes to activate {noun} from the {self.system_name} system. Locate its I/O node and activate it.",
            f"A client wishes to sabotage {noun} at the {self.system_name} system.",
            f"A client wishes to crash the {self.system_name} system. Locate the CPU and initiate a system failure.",
            f"A client wants a backdoor into the {self.system_name} system. Locate the CPU and create it.",
            f"A client needs a special program activated on the {self.system_name} system. Locate the target node and remain there while it runs.",
        )
        text = descriptions[self.contract_type]
        if self.target_count > 1:
            text += f" ({self.target_count} targets)"
        if self.no_alarms:
            text += " The target system must not become aware of any tampering."
        if self.timed:
            text += f" Complete the mission within {self.time_limit} minutes of system entry."
        return text

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Contract:
        return cls(**value)


@dataclass
class SourceCode:
    source_type: str
    class_id: int = 0
    rating: int = 1


@dataclass
class ShopItem:
    item_type: str
    subtype: int
    rating: int
    price: int

    @property
    def description(self) -> str:
        if self.item_type == "software":
            return f"{PROGRAM_NAMES[self.subtype]} {self.rating}"
        if self.item_type == "chip":
            return f"{CHIP_NAMES[self.subtype]} Chip {self.rating}"
        return f"{HARDWARE_NAMES[self.subtype]} {self.rating}"


@dataclass
class DSFile:
    name: str
    file_type: int
    value: int
    size: int
    target: bool = False
    state: str = "node"
    scanned: bool = False
    evaluated: bool = False
    downloaded: bool = False
    edited: bool = False
    erased: bool = False

    @property
    def description(self) -> str:
        labels = ("Junk Data", "Valuable File", "Passcode", "Clue", "Quest File", "Program", "Program Source", "Chip Source")
        return labels[self.file_type] if self.file_type < len(labels) else "Data File"


@dataclass
class Ice:
    name: str
    ice_type: int
    rating: int
    health: int
    node: int
    grid_x: int = 0
    grid_y: int = 0
    direction: int = -1
    bypassed: bool = False
    hostile: bool = False
    noticed: bool = False
    query_turns: int = 0
    following: bool = False
    analyzed: bool = False
    slow_turns: int = 0
    confuse_turns: int = 0
    weaken_turns: int = 0

    @classmethod
    def generate(cls, difficulty: int, node: int, sequence: int) -> Ice:
        ice_type = random.choices(range(6), weights=(1, 2, 3, 1, 4, 1))[0]
        rating = max(1, difficulty - 2 + random.randint(0, 5))
        direction = random.randrange(4) if ice_type == 0 else -1
        x, y = random.randrange(1, 9), random.randrange(1, 9)
        if ice_type == 0:
            x, y = ((4, 0), (8, 4), (4, 8), (0, 4))[direction]
        return cls(
            f"{ICE_TYPE_NAMES[ice_type]}-{sequence:02d}", ice_type, rating,
            4 + rating * 3, node, x, y, direction,
        )

    @property
    def combat_rating(self) -> int:
        return max(1, self.rating - self.weaken_turns)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MatrixNode:
    name: str
    node_type: int
    x: int
    y: int
    neighbors: dict[str, int] = field(default_factory=dict)
    files: list[DSFile] = field(default_factory=list)
    mapped: bool = False
    activated: bool = False
    smoke: int = 0
    silence: int = 0
    objective: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "node_type": self.node_type, "x": self.x, "y": self.y,
                "neighbors": {k: int(v) for k, v in self.neighbors.items()},
                "files": [asdict(item) for item in self.files], "mapped": self.mapped,
                "activated": self.activated, "smoke": self.smoke, "silence": self.silence,
                "objective": self.objective}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> MatrixNode:
        return cls(files=[DSFile(**item) for item in value.pop("files", [])], **value)


@dataclass
class MatrixRun:
    nodes: list[MatrixNode]
    ice: list[Ice]
    current_node: int
    difficulty: int
    contract_type: int
    corporation: str
    target_count: int
    target: int = 25
    completed: int = 0
    turns: int = 0
    trace_turns: int = 0
    alert: int = 0
    mental_health: int = MAX_HEALTH
    deck_health: int = MAX_HEALTH
    disconnected: bool = False
    crashed: bool = False
    backdoor: bool = False
    no_alarms: bool = False
    time_limit: int = 0
    messages: list[str] = field(default_factory=lambda: ["Jack in complete. Locate the contract objective."])
    loaded_programs: list[Program] = field(default_factory=list, repr=False)

    @classmethod
    def generate(cls, contract: Contract, backdoor: bool = False) -> MatrixRun:
        node_count = 8 + contract.size * 3
        nodes: list[MatrixNode] = []
        for index in range(node_count):
            if index == 0:
                node_type = 7
            elif index == node_count - 1:
                node_type = 0
            else:
                node_type = random.choices((1, 2, 3, 4, 5, 6), weights=(1, 2, 4, 3, 5, 1))[0]
            if index == 1 and contract.contract_type in (0, 1, 2, 3):
                node_type = 3
            elif index == 1 and contract.contract_type in (4, 5, 6):
                node_type = 4
            x = 1 + index % 6
            y = 1 + index // 6
            nodes.append(MatrixNode(f"{NODE_TYPE_NAMES[node_type]}-{index:02d}", node_type, x, y))
        for index in range(node_count):
            if (index % 6 != 5) and index + 1 < node_count:
                nodes[index].neighbors["E"] = index + 1
                nodes[index + 1].neighbors["W"] = index
            if index + 6 < node_count and (index % 6 == 0 or random.random() < 0.52):
                nodes[index].neighbors["S"] = index + 6
                nodes[index + 6].neighbors["N"] = index
        targets_left = contract.target_count if contract.contract_type in (0, 1, 2, 3) else 0
        for index, node in enumerate(nodes):
            if node.node_type == 3:
                file_count = random.randint(1, 4)
                for file_index in range(file_count):
                    is_target = targets_left > 0 and (file_index == file_count - 1 or random.random() < 0.45)
                    if is_target:
                        targets_left -= 1
                    file_type = random.choice((0, 1, 2, 3, 4))
                    if is_target and contract.contract_type in (0, 1, 2, 3):
                        file_type = 4
                    node.files.append(DSFile(
                        f"{TARGETS[contract.target]}-{index}-{file_index}.dat" if is_target else f"data-{index}-{file_index}.dat",
                        file_type, random.randint(50, 1000), random.randint(2, 12), is_target,
                    ))
        while targets_left > 0:
            datastores = [node for node in nodes if node.node_type == 3]
            node = random.choice(datastores)
            node.files.append(DSFile(f"{TARGETS[contract.target]}-objective.dat", 4, 500, 6, True))
            targets_left -= 1
        ice = [Ice.generate(contract.difficulty, i, i + 1) for i in range(1, node_count) if random.random() < 0.52]
        start = node_count - 1 if backdoor else 0
        nodes[start].mapped = True
        for _ in range(contract.target_count if contract.contract_type in (4, 5, 6, 9) else 0):
            expected_type = 0 if contract.target == 28 else (3 if contract.target == 27 else 4)
            candidates = [node for node in nodes if node.node_type == expected_type and node.objective is None]
            if candidates:
                random.choice(candidates).objective = contract.target
        return cls(nodes, ice, start, contract.difficulty, contract.contract_type, contract.system_name,
                   contract.target_count, target=contract.target, backdoor=backdoor,
                   no_alarms=contract.no_alarms, time_limit=contract.time_limit)

    @property
    def node(self) -> MatrixNode:
        return self.nodes[self.current_node]

    @property
    def local_ice(self) -> list[Ice]:
        return [item for item in self.ice if item.node == self.current_node and item.health > 0]

    def post(self, message: str) -> None:
        self.messages.append(message)
        del self.messages[:-80]

    def move(self, direction: str) -> bool:
        destination = self.node.neighbors.get(direction)
        if destination is None:
            self.post(f"No connection to the {direction}.")
            return False
        source = self.current_node
        direction_index = "NESW".index(direction)
        gateway = next((ice for ice in self.local_ice
                        if ice.ice_type == 0 and ice.direction == direction_index and ice.health > 0 and not ice.bypassed), None)
        if gateway is not None:
            self.post(f"{gateway.name} blocks this passage.")
            return False
        followers = [ice for ice in self.local_ice if ice.ice_type in (1, 4, 5) and
                     (ice.following or ice.query_turns > 0) and not ice.bypassed and
                     self.nodes[source].smoke == 0]
        self.current_node = destination
        self.node.mapped = True
        for follower in followers:
            follower.node = destination
            follower.following = True
            follower.noticed = True
            follower.grid_x, follower.grid_y = ((4, 8), (0, 4), (4, 0), (8, 4))[direction_index]
            self.post(f"{follower.name} follows you into {self.node.name}.")
        self.post(f"Moved to {self.node.name}.")
        self.tick()
        return True

    def tick(self) -> None:
        self.turns += 1
        if self.time_limit and self.turns >= self.time_limit:
            self.crashed = True
            self.post("The mission time limit expired.")
        if self.trace_turns:
            self.trace_turns -= 1
            if not self.trace_turns:
                self.crashed = True
                self.post("Trace completed. The run has crashed.")
        for item in self.local_ice:
            if item.hostile:
                damage = max(1, item.combat_rating // 3 + random.randint(0, 2))
                self.deck_health = max(0, self.deck_health - damage)
                self.post(f"{item.name} attacks the deck for {damage}.")
                if self.deck_health <= 0:
                    self.crashed = True
                    self.post("Deck integrity lost.")
                continue
            if item.bypassed:
                continue
            if item.query_turns:
                item.query_turns += 1
                if item.query_turns >= 4:
                    self.raise_alert(item)
                    item.query_turns = 1
                    self.post(f"{item.name} queries you again.")
                continue
            if item.ice_type in (1, 2, 3, 4, 5) and self.notice_ice(item):
                item.noticed = True
                item.query_turns = 1
                if item.ice_type in (1, 4, 5):
                    item.following = True
                self.post(f"{item.name} has queried you.")
        if self.no_alarms and self.alert:
            self.crashed = True
            self.post("The no-alarms contract condition was violated.")
        if self.local_ice and not self.trace_turns and self.alert > 0 and random.random() < 0.08 * self.alert:
            self.trace_turns = max(3, 12 - self.alert)
            self.post("Trace IC has started tracking you.")
        for item in self.ice:
            if item.slow_turns:
                item.slow_turns -= 1
            if item.confuse_turns:
                item.confuse_turns -= 1
            if item.weaken_turns:
                item.weaken_turns -= 1

    def notice_ice(self, ice: Ice) -> bool:
        hide = next((program for program in self.loaded_programs if program.loaded and program.class_id == 13), None)
        if hide is not None and die_roll(10 + ice.rating * 2 - hide.rating) > 0:
            self.post(f"{ice.name} fails to notice you.")
            return False
        return True

    def raise_alert(self, source: Ice | None = None) -> None:
        if self.node.silence:
            for ice in self.local_ice:
                ice.hostile = True
            self.post("The silenced node prevents an alarm; local ICE goes hostile.")
            return
        self.alert = min(2, self.alert + 1)
        self.post(f"{source.name if source else 'An ICE'} signals a {'red' if self.alert == 2 else 'yellow'} alert.")
        if self.alert == 2:
            for ice in self.local_ice:
                ice.hostile = True
                ice.query_turns = 0

    def attack(self, program: Program | None, target: Ice | None = None) -> None:
        targets = self.local_ice
        if not targets:
            self.post("No target in this node.")
            return
        if program is None or program.class_id not in (0, 1, 2):
            self.post("Load and select an attack program.")
            return
        if not program.loaded:
            self.post("The default attack program is not loaded.")
            return
        target = target if target in targets else targets[0]
        success = die_roll(target.combat_rating + 4 - program.rating * 2)
        damage = compute_damage(success)
        if damage:
            target.health -= damage
            self.post(f"{program.name} hits {target.name} for {damage}.")
            if target.health <= 0:
                self.post(f"{target.name} crashed.")
        elif success == -1:
            self.deck_health = max(0, self.deck_health - 3)
            self.post("Catastrophic program failure. Deck feedback causes 3 damage.")
        else:
            self.post(f"{program.name} missed {target.name}.")
        for ice in self.local_ice:
            ice.hostile = True
            ice.query_turns = 0
        self.post("Your attack exposes you. Local ICE is now hostile.")
        self.tick()

    def run_program(self, program: Program, target: Ice | None = None) -> None:
        if program.class_id == 25:
            if self.contract_type == 9 and self.node.objective == self.target:
                self.completed += 1
                self.node.objective = None
                self.post(f"{program.name} completed the client task.")
            else:
                self.post("This node is not a valid client-program target.")
            self.tick()
            return
        if program.class_id == 5:  # Silence
            self.node.silence = program.rating * 2
            self.post(f"{program.name} silences the current node.")
        elif program.class_id == 9:  # Smoke
            self.node.smoke = program.rating * 2
            self.post(f"{program.name} deploys a smoke screen.")
        elif program.class_id == 14:  # Deceive
            if target is None:
                self.post(f"{program.name} needs a targeted ICE.")
                return
            if target.hostile:
                self.post(f"{target.name} already knows you are hostile. {program.name} has no effect.")
                self.tick()
                return
            success = die_roll(10 + (2 * self.difficulty) + target.rating - (program.rating + 1))
            if success > 0:
                for item in self.local_ice:
                    if item.rating <= target.rating:
                        item.bypassed = True
                        item.query_turns = 0
                        item.following = False
                self.post(f"{program.name} succeeds. {target.name} is deceived.")
            else:
                self.post(f"{program.name} failed. {target.name} was not deceived.")
                if target.query_turns:
                    target.query_turns = 3
                else:
                    self.raise_alert(target)
        elif program.class_id == 16:  # Analyze
            if target:
                target.analyzed = True
                self.post(f"Analyzed {target.name}: rating {target.rating}, health {target.health}.")
            else:
                self.post("No ICE selected for analysis.")
        elif program.class_id == 17:  # Scan
            for node in self.nodes:
                if abs(node.x - self.node.x) + abs(node.y - self.node.y) <= program.rating + 1:
                    node.mapped = True
            self.post("Nearby topology mapped.")
        elif program.class_id == 19:  # Decrypt
            for file in self.node.files:
                if file.target:
                    file.scanned = True
            self.post("Encrypted target data decrypted.")
        elif target and program.class_id in (3, 6, 7):
            setattr(target, {3: "slow_turns", 6: "confuse_turns", 7: "weaken_turns"}[program.class_id], program.rating + 1)
            self.post(f"{program.name} affects {target.name}.")
        elif program.class_id == 11:  # Medic
            self.deck_health = min(MAX_HEALTH, self.deck_health + program.rating * 2)
            self.post(f"{program.name} repairs the deck.")
        elif program.class_id == 15:  # Relocate
            safe = [i for i, node in enumerate(self.nodes) if node.mapped and not any(ice.node == i for ice in self.ice)]
            if safe:
                self.current_node = random.choice(safe)
                self.post("Relocated to a mapped, clear node.")
        elif program.class_id in (0, 1, 2):
            self.attack(program)
            return
        else:
            self.post(f"{program.name} is active for this action.")
        self.tick()

    def file_target_complete(self, file: DSFile) -> bool:
        if not file.target:
            return False
        if self.contract_type == 0:
            return file.downloaded
        if self.contract_type == 1:
            return file.downloaded and file.erased
        if self.contract_type == 2:
            return file.erased
        if self.contract_type == 3:
            return file.edited
        return False

    def use_node(self, action: str, file_index: int | None = None) -> bool:
        if any(item.hostile and item.health > 0 for item in self.local_ice):
            self.post("Hostile ICE prevents node access.")
            return False
        node_type = self.node.node_type
        if action in ("download", "edit", "erase") and self.node.files and self.node.node_type == 3:
            if file_index is not None and 0 <= file_index < len(self.node.files):
                target = self.node.files[file_index]
            else:
                target = next((item for item in self.node.files if item.target and item.state == "node"), None)
            if target is None:
                target = next((item for item in self.node.files if item.state == "node"), None)
            if target is None:
                self.post("No files remain to access in this datastore.")
                return False
            previously_complete = self.file_target_complete(target)
            if action == "download":
                target.state = "deck"
                target.downloaded = True
            elif action == "edit":
                target.state = "edited"
                target.edited = True
            else:
                target.state = "erased"
                target.erased = True
            if target.target and not previously_complete and self.file_target_complete(target):
                self.completed += 1
            self.post(f"{action.title()} complete: {target.name}.")
            self.tick()
            return True
        if action == "map" and node_type in (0, 1):
            for node in self.nodes:
                node.mapped = True
            self.post("System map acquired.")
            self.tick()
            return True
        if action == "backdoor" and node_type == 0:
            self.backdoor = True
            self.post("Persistent backdoor installed.")
            if self.contract_type == 8:
                self.completed = self.target_count
            self.tick()
            return True
        if action == "crash" and node_type == 0:
            self.post("Core processor crashed.")
            self.completed = self.target_count
            if self.contract_type != 7:
                self.crashed = True
            else:
                self.tick()
            return True
        if action == "io" and node_type == 4:
            self.node.activated = not self.node.activated
            self.post("I/O controller state changed.")
            if self.contract_type in (4, 5, 6) and self.node.objective == self.target:
                self.completed += 1
                self.node.objective = None
            elif self.contract_type in (4, 5, 6):
                self.alert = max(self.alert, 1)
                self.post("That controller did not match the contract target.")
            self.tick()
            return True
        if action == "portal" and node_type in (6, 7):
            self.current_node = 0 if node_type == 6 else len(self.nodes) - 1
            self.post("Portal traversed.")
            self.tick()
            return True
        self.post("That action is not available at this node.")
        return False

    def complete(self) -> bool:
        return self.completed >= self.target_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self.nodes], "ice": [item.to_dict() for item in self.ice],
            "current_node": self.current_node, "difficulty": self.difficulty, "contract_type": self.contract_type,
            "corporation": self.corporation, "target_count": self.target_count, "target": self.target, "completed": self.completed,
            "turns": self.turns, "trace_turns": self.trace_turns, "alert": self.alert,
            "mental_health": self.mental_health, "deck_health": self.deck_health, "disconnected": self.disconnected,
            "crashed": self.crashed, "backdoor": self.backdoor, "messages": self.messages,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> MatrixRun:
        value = dict(value)
        value["nodes"] = [MatrixNode.from_dict(dict(node)) for node in value["nodes"]]
        value["ice"] = [Ice(**item) for item in value["ice"]]
        return cls(**value)


@dataclass
class Character:
    name: str = "Decker"
    credits: int = 100
    lifestyle: int = 0
    reputation: int = 0
    reputation_points: int = 0
    skills: dict[str, int] = field(default_factory=lambda: {
        "Attack": 1, "Defense": 1, "Stealth": 1, "Analysis": 1, "Programming": 1, "Chip Design": 1,
    })
    skill_points: int = 0
    image: int = 0
    tooltips: bool = True
    ironman: bool = False
    chips: list[int] = field(default_factory=lambda: [1] * 6)
    hardware: list[int] = field(default_factory=lambda: [0] * len(HARDWARE_NAMES))
    programs: list[Program] = field(default_factory=list)
    contracts: list[Contract] = field(default_factory=list)
    current_contract: Contract | None = None
    source_code: list[SourceCode] = field(default_factory=list)
    project: SourceCode | None = None
    project_time: int = 0
    shop: list[ShopItem] = field(default_factory=list)
    ordered_item: ShopItem | None = None
    order_time: int = 0
    calendar: date = field(default_factory=lambda: date(2132, 1, 1))
    physical_health: int = MAX_HEALTH
    matrix: MatrixRun | None = None
    backdoors: list[int] = field(default_factory=list)
    filename: str = ""

    @classmethod
    def new(cls, name: str, bonus: str = "none") -> Character:
        character = cls(name=name)
        if bonus == "skills":
            character.skills = {key: 2 for key in character.skills}
        elif bonus == "hardware":
            character.chips = [2] * 6
        elif bonus == "money":
            character.credits = 2000
        for class_id in sorted(INITIAL_PROGRAMS):
            rating = 2 if bonus == "software" else 1
            program = Program(class_id, rating, load_default=class_id in DEFAULT_PROGRAMS, loaded=class_id in DEFAULT_PROGRAMS)
            character.programs.append(program)
        character.generate_contracts()
        character.generate_shop()
        return character

    @property
    def current_load(self) -> int:
        return sum(program.size for program in self.programs if program.loaded)

    @property
    def load_capacity(self) -> int:
        return 30 * (self.chips[0] + min(self.chips[5], self.chips[0]))

    def generate_contracts(self) -> None:
        wanted = max(1, 3 + self.reputation // 5 - len(self.contracts))
        for _ in range(wanted):
            self.contracts.append(Contract.generate(self.reputation))

    def generate_shop(self) -> None:
        self.shop.clear()
        seen: set[tuple[str, int, int]] = set()
        for item_type, count in (
            ("software", 3 + random.randrange(4) + random.randrange(4) + random.randrange(4)),
            ("hardware", 1 + random.randrange(4)),
            ("chip", 2 + random.randrange(4) + random.randrange(4)),
        ):
            while len([item for item in self.shop if item.item_type == item_type]) < count:
                if item_type == "software":
                    subtype = random.randrange(len(PROGRAM_NAMES) - 1)
                    rating = random.randrange(1, 7) + self.lifestyle * 2
                    price = software_price(subtype, rating)
                elif item_type == "chip":
                    subtype = random.randrange(len(CHIP_NAMES))
                    rating = random.randrange(2, 8) + self.lifestyle * 2
                    price = chip_price(subtype, rating)
                else:
                    subtype = random.randrange(len(HARDWARE_NAMES))
                    rating = min(1 + random.randrange(self.lifestyle + 1), HARDWARE_MAX_LEVEL[subtype])
                    price = hardware_price(subtype, rating)
                identity = (item_type, subtype, rating)
                if identity in seen:
                    continue
                seen.add(identity)
                price += price * random.randint(-15, 15) // 100
                self.shop.append(ShopItem(item_type, subtype, rating, price))

    def current_item_level(self, item_type: str, subtype: int) -> int:
        if item_type == "software":
            return max((program.rating for program in self.programs if program.class_id == subtype), default=0)
        if item_type == "chip":
            return self.chips[subtype]
        return self.hardware[subtype]

    def buy(self, index: int) -> str:
        item = self.shop[index]
        if self.credits < item.price:
            return "You cannot afford that item."
        self.credits -= item.price
        if item.item_type == "software":
            if any(p.class_id == item.subtype and p.rating == item.rating for p in self.programs):
                self.credits += item.price
                return "You already own this type of program."
            if any(p.class_id == item.subtype and p.rating > item.rating for p in self.programs):
                # The original prompts before buying; confirmation is handled by the UI.
                pass
            self.programs.append(Program(item.subtype, item.rating))
            self.programs.sort(key=lambda program: (program.class_id, -program.rating))
        elif item.item_type == "chip":
            self.chips[item.subtype] = max(self.chips[item.subtype], item.rating)
        else:
            self.hardware[item.subtype] = max(self.hardware[item.subtype], item.rating)
        if item.item_type != "software":
            self.shop.pop(index)
        return f"Purchased {item.description}."

    def accept_contract(self, index: int) -> None:
        self.current_contract = self.contracts.pop(index)
        if self.current_contract.contract_type == 9:
            self.programs.append(Program(25, max(1, (self.current_contract.corporation + 4) // 5), "Mission Client"))
            self.programs.sort(key=lambda program: (program.class_id, -program.rating))

    def abandon_contract(self) -> str:
        if self.current_contract is None:
            return "No contract is active."
        self.current_contract = None
        self.reputation_points = max(0, self.reputation_points - 2)
        return "Contract abandoned. Reputation decreased."

    def start_matrix(self) -> str:
        if self.current_contract is None:
            return "No contract has been accepted."
        backdoor = self.current_contract.corporation in self.backdoors
        self.matrix = MatrixRun.generate(self.current_contract, backdoor)
        if self.current_contract.contract_type == 9 and not any(program.class_id == 25 for program in self.programs):
            self.programs.append(Program(25, max(1, (self.current_contract.corporation + 4) // 5), "Mission Client"))
        for program in self.programs:
            program.loaded = program.load_default or (program.class_id == 25 and self.current_contract.contract_type == 9)
        self.matrix.loaded_programs = self.programs
        return f"Connected to {self.current_contract.system_name}."

    def finish_matrix(self) -> str:
        if self.matrix is None or self.current_contract is None:
            return "No active matrix run."
        run = self.matrix
        if run.complete() and run.crashed is False:
            reward = self.current_contract.pay
            self.credits += reward
            self.reputation_points += self.current_contract.difficulty
            while self.reputation_points >= (self.reputation + 1) * 5:
                self.reputation_points -= (self.reputation + 1) * 5
                self.reputation += 1
                self.skill_points += 1
            if run.backdoor:
                self.backdoors.append(self.current_contract.corporation)
                self.backdoors = list(set(self.backdoors))
            result = f"Contract complete. Payment: {reward} credits."
            self.current_contract = None
        else:
            self.credits = max(0, self.credits - 250)
            result = "Run failed. Recovery and medical costs: 250 credits."
        self.matrix = None
        self.generate_contracts()
        return result

    def rest(self, days: int) -> str:
        self.calendar = date.fromordinal(self.calendar.toordinal() + max(1, days))
        self.physical_health = MAX_HEALTH
        if self.ordered_item is not None:
            self.order_time = max(0, self.order_time - max(1, days))
            if self.order_time == 0:
                item = self.ordered_item
                if item.item_type == "software":
                    self.programs.append(Program(item.subtype, item.rating))
                elif item.item_type == "chip":
                    self.chips[item.subtype] = max(item.rating, self.chips[item.subtype])
                else:
                    self.hardware[item.subtype] = max(item.rating, self.hardware[item.subtype])
                self.ordered_item = None
        for index, contract in enumerate(list(self.contracts)):
            contract.days_left -= max(1, days)
            if contract.days_left <= 0:
                self.contracts.remove(contract)
        if self.current_contract:
            self.current_contract.days_left -= max(1, days)
            if self.current_contract.days_left <= 0:
                self.current_contract = None
                return "Rest complete, but the active contract expired."
        self.credits -= LIFESTYLE_COST[self.lifestyle]
        if self.credits < 0:
            self.lifestyle = max(0, self.lifestyle - 1)
            self.credits = 0
        self.generate_contracts()
        self.generate_shop()
        return f"Rested until {self.calendar.isoformat()}."

    def advance_project(self, days: int) -> str:
        if self.project is None:
            return "There is no active project."
        skill_name = "Programming" if self.project.source_type == "software" else "Chip Design"
        skill = self.skills[skill_name] * (1 + self.hardware[7])
        used_days = max(1, days)
        self.project_time = max(0, self.project_time - used_days * skill)
        if self.project_time:
            return f"{self.project_time} work unit(s) remain."
        target = 10 + self.project.rating - (skill + self.hardware[7])
        if die_roll(target) > 0:
            self.source_code.append(self.project)
            result = "Your project is now complete."
            self.project = None
        else:
            self.project_time = max(1, (self.project_time + 3) // 4)
            result = "A flaw was discovered. Additional time is required."
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 2, "name": self.name, "credits": self.credits, "lifestyle": self.lifestyle,
            "reputation": self.reputation, "reputation_points": self.reputation_points, "skills": self.skills,
            "skill_points": self.skill_points, "image": self.image, "tooltips": self.tooltips, "ironman": self.ironman,
            "chips": self.chips, "hardware": self.hardware, "programs": [asdict(item) for item in self.programs],
            "contracts": [asdict(item) for item in self.contracts],
            "current_contract": asdict(self.current_contract) if self.current_contract else None,
            "source_code": [asdict(item) for item in self.source_code], "project": asdict(self.project) if self.project else None,
            "project_time": self.project_time, "shop": [asdict(item) for item in self.shop],
            "ordered_item": asdict(self.ordered_item) if self.ordered_item else None, "order_time": self.order_time,
            "calendar": self.calendar.isoformat(), "physical_health": self.physical_health,
            "matrix": self.matrix.to_dict() if self.matrix else None, "backdoors": self.backdoors, "filename": self.filename,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Character:
        if value.get("version") != 2:
            raise ValueError("Unsupported Decker save version")
        character = cls(
            name=value["name"], credits=value["credits"], lifestyle=value["lifestyle"], reputation=value["reputation"],
            reputation_points=value["reputation_points"], skills=value["skills"], skill_points=value["skill_points"],
            image=value["image"], tooltips=value.get("tooltips", True), ironman=value.get("ironman", False),
            chips=value["chips"], hardware=value["hardware"], programs=[Program.from_dict(item) for item in value["programs"]],
            contracts=[Contract.from_dict(item) for item in value["contracts"]],
            current_contract=Contract.from_dict(value["current_contract"]) if value.get("current_contract") else None,
            source_code=[SourceCode(**item) for item in value["source_code"]],
            project=SourceCode(**value["project"]) if value.get("project") else None, project_time=value["project_time"],
            shop=[ShopItem(**item) for item in value["shop"]],
            ordered_item=ShopItem(**value["ordered_item"]) if value.get("ordered_item") else None,
            order_time=value["order_time"], calendar=date.fromisoformat(value["calendar"]),
            physical_health=value["physical_health"], matrix=MatrixRun.from_dict(value["matrix"]) if value.get("matrix") else None,
            backdoors=value.get("backdoors", []), filename=value.get("filename", ""),
        )
        if character.matrix is not None:
            character.matrix.loaded_programs = character.programs
        return character
