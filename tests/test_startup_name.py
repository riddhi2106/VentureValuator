from tools.startup_name import (
    infer_name_from_text,
    is_placeholder_startup_name,
    name_from_pdf_path,
    resolve_startup_name,
)


def test_placeholder_detection():
    assert is_placeholder_startup_name("Unknown Startup")
    assert is_placeholder_startup_name(None)
    assert not is_placeholder_startup_name("Acme Robotics")


def test_name_resolution_prefers_extracted_then_text_then_filename():
    assert resolve_startup_name({"name": "Acme Robotics"}) == "Acme Robotics"
    assert (
        resolve_startup_name(
            {"name": "Unknown Startup"},
            raw_text="Nova Health\nInvestor presentation",
            pdf_path="/tmp/fallback.pdf",
        )
        == "Nova Health"
    )
    assert resolve_startup_name({}, pdf_path="/tmp/solar_grid.pdf") == "solar grid"
    assert resolve_startup_name({}) == "Startup Analysis"


def test_text_and_file_helpers_reject_generic_cover_lines():
    assert infer_name_from_text("Pitch Deck\nConfidential\nOrbit AI") == "Orbit AI"
    assert name_from_pdf_path("/tmp/Nova-Fintech.pdf") == "Nova Fintech"

