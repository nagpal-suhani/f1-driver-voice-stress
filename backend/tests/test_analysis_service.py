from app.services import analysis_service, demo_data


def test_build_lap_entries_computes_deltas():
    raw = demo_data.demo_laps(total=5)
    laps = analysis_service.build_lap_entries(raw)
    assert len(laps) == 5
    assert laps[0].delta_to_previous is None  # first lap has no previous
    assert laps[1].delta_to_previous is not None
    assert all(l.delta_to_best is not None for l in laps)


def test_build_race_snapshot_uses_last_lap():
    raw = demo_data.demo_laps(total=10)
    laps = analysis_service.build_lap_entries(raw)
    snap = analysis_service.build_race_snapshot(laps, [{"position": 4}], starting_position=6)
    assert snap.current_lap == 10
    assert snap.position == 4
    assert snap.starting_position == 6
    assert snap.best_lap is not None


def test_compute_association_insufficient_data():
    result = analysis_service.compute_association("STRESSED", [], [])
    assert result.sample_count == 0
    assert result.association is None


def test_compute_association_reports_temporal_language_not_causal():
    raw = demo_data.demo_laps(total=25)
    laps = analysis_service.build_lap_entries(raw)
    result = analysis_service.compute_association("STRESSED", laps, [17, 18, 19, 20, 21])
    assert result.sample_count >= 2
    assert "temporal association" in (result.association or "").lower()
    assert "caused" not in (result.association or "").lower()


def test_driver_summary_falls_back_gracefully():
    summary = analysis_service.build_driver_summary(None, fallback_number=44)
    assert summary.driver_number == 44
    assert summary.full_name is None
