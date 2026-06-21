import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rocket_library import (  # noqa: E402
    build_comparison_rows,
    get_rocket_by_name,
    get_rocket_names,
    load_rocket_library,
    map_vehicle_to_simulator_parameters,
    return_vehicle_summary,
)


def test_library_loads_known_vehicles() -> None:
    library = load_rocket_library()
    assert "PSLV" in library
    assert "Falcon 9" in library
    assert "Ariane 5" in library


def test_lookup_and_mapping_for_simulator() -> None:
    pslv = get_rocket_by_name("PSLV")
    assert pslv is not None

    mapped = map_vehicle_to_simulator_parameters(pslv)
    assert mapped["thrust"] == pslv["thrust_kn"] * 1000.0
    assert mapped["burn_time"] == pslv["burn_time_s"]
    assert mapped["dry_mass"] > 0.0
    assert mapped["fuel_mass"] > 0.0


def test_summary_and_comparison_rows() -> None:
    names = get_rocket_names()
    assert names

    summary = return_vehicle_summary("Falcon 9")
    assert "Falcon 9" in summary

    rows = build_comparison_rows()
    assert rows
    assert {"Rocket", "Country", "Height", "Stages", "Mass", "Payload", "Thrust"}.issubset(
        rows[0].keys()
    )
