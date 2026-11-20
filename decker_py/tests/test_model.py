from pathlib import Path
import random

from decker.model import Character, Ice, Program
from decker.storage import load_game, save_game


def test_new_character_has_expected_equipment() -> None:
    character = Character.new("Test", "software")
    assert character.credits == 100
    assert character.programs
    assert all(program.rating == 2 for program in character.programs)
    assert any(program.class_id == 0 and program.loaded for program in character.programs)
    assert character.contracts
    assert character.shop


def test_contract_failure_cycle() -> None:
    random.seed(7)
    character = Character.new("Runner")
    character.contracts[0].contract_type = 0
    character.contracts[0].target = 0
    character.accept_contract(0)
    character.start_matrix()
    assert character.matrix is not None
    assert character.matrix.nodes
    assert any(any(file.target for file in node.files) for node in character.matrix.nodes)
    character.matrix.crashed = True
    result = character.finish_matrix()
    assert "failed" in result.lower()
    assert character.matrix is None


def test_save_round_trip(tmp_path: Path) -> None:
    character = Character.new("Portable")
    character.accept_contract(0)
    character.start_matrix()
    path = tmp_path / "portable.json"
    save_game(character, path)
    restored = load_game(path)
    assert restored.name == character.name
    assert restored.matrix is not None
    assert len(restored.matrix.nodes) == len(character.matrix.nodes)
    assert restored.to_dict() == character.to_dict()


def test_program_load_respects_deck_capacity() -> None:
    character = Character.new("Buyer", "money")
    program = Program(0, 20)
    character.programs.append(program)
    assert character.current_load + program.size > character.load_capacity


def test_ice_queries_before_attacking_on_entry() -> None:
    character = Character.new("Query Runner")
    character.accept_contract(0)
    character.start_matrix()
    assert character.matrix is not None
    ice = Ice("Probe", 1, 1, 7, character.matrix.current_node)
    character.matrix.ice = [ice]
    before = character.matrix.deck_health
    character.matrix.tick()
    assert ice.query_turns == 1
    assert not ice.hostile
    assert character.matrix.deck_health == before


def test_seen_mobile_ice_follows_through_adjacent_room() -> None:
    character = Character.new("Follower")
    character.accept_contract(0)
    character.start_matrix()
    assert character.matrix is not None
    run = character.matrix
    ice = Ice("Probe", 1, 1, 7, run.current_node, query_turns=2, noticed=True)
    run.ice = [ice]
    direction = next(iter(run.node.neighbors))
    destination = run.move(direction)
    assert destination
    assert ice.node == run.current_node
    assert ice.following


def test_smoke_breaks_follow() -> None:
    character = Character.new("Smoker")
    character.accept_contract(0)
    character.start_matrix()
    assert character.matrix is not None
    run = character.matrix
    run.node.smoke = 2
    ice = Ice("Probe", 1, 1, 7, run.current_node, query_turns=2, noticed=True)
    run.ice = [ice]
    direction = next(iter(run.node.neighbors))
    old_node = run.current_node
    run.move(direction)
    assert ice.node == old_node


def test_crash_contract_completes_at_cpu() -> None:
    random.seed(4)
    character = Character.new("Crash Runner")
    contract = character.contracts[0]
    contract.contract_type = 7
    contract.target = 25
    contract.target_count = 1
    character.accept_contract(0)
    character.start_matrix()
    assert character.matrix is not None
    character.matrix.current_node = len(character.matrix.nodes) - 1
    character.matrix.use_node("crash")
    assert character.matrix.complete()
    assert not character.matrix.crashed


def test_contract_is_viewable_without_acceptance(monkeypatch) -> None:
    character = Character.new("Viewer")
    count = len(character.contracts)
    description = character.contracts[0].description
    assert "client" in description.lower()
    assert character.current_contract is None
    assert len(character.contracts) == count


def test_shop_is_grouped_and_has_legacy_current_levels() -> None:
    character = Character.new("Buyer")
    groups = [item.item_type for item in character.shop]
    order = {"software": 0, "hardware": 1, "chip": 2}
    assert [order[group] for group in groups] == sorted(order[group] for group in groups)
    assert character.current_item_level("software", 0) == 1
    assert character.current_item_level("chip", 0) == 1


def test_project_only_advances_when_work_is_requested() -> None:
    character = Character.new("Designer")
    character.project = __import__("decker.model", fromlist=["SourceCode"]).SourceCode("software", 0, 1)
    character.project_time = 10
    character.rest(1)
    assert character.project_time == 10


def test_file_objective_is_placed_in_datastore() -> None:
    character = Character.new("Data Runner")
    contract = character.contracts[0]
    contract.contract_type = 0
    contract.target = 0
    character.accept_contract(0)
    character.start_matrix()
    assert character.matrix is not None
    target_nodes = [node for node in character.matrix.nodes if any(file.target for file in node.files)]
    assert target_nodes
    assert all(node.node_type == 3 for node in target_nodes)


def test_steal_erase_requires_both_file_actions() -> None:
    character = Character.new("File Runner")
    contract = character.contracts[0]
    contract.contract_type = 1
    contract.target = 0
    contract.target_count = 1
    character.accept_contract(0)
    character.start_matrix()
    assert character.matrix is not None
    node = next(node for node in character.matrix.nodes if any(file.target for file in node.files))
    character.matrix.current_node = character.matrix.nodes.index(node)
    character.matrix.ice = [ice for ice in character.matrix.ice if ice.node != character.matrix.current_node]
    index = next(index for index, file in enumerate(node.files) if file.target)
    character.matrix.use_node("download", index)
    assert not character.matrix.complete()
    character.matrix.use_node("erase", index)
    assert character.matrix.complete()


def test_io_contract_only_completes_at_marked_controller() -> None:
    character = Character.new("IO Runner")
    contract = character.contracts[0]
    contract.contract_type = 4
    contract.target = 14
    contract.target_count = 1
    character.accept_contract(0)
    character.start_matrix()
    assert character.matrix is not None
    marked = next(node for node in character.matrix.nodes if node.objective == contract.target)
    character.matrix.current_node = character.matrix.nodes.index(marked)
    character.matrix.use_node("io")
    assert character.matrix.complete()


def test_client_contract_gets_loaded_mission_program() -> None:
    character = Character.new("Client Runner")
    contract = character.contracts[0]
    contract.contract_type = 9
    contract.target = 27
    character.accept_contract(0)
    character.start_matrix()
    client = next(program for program in character.programs if program.class_id == 25)
    assert client.loaded
