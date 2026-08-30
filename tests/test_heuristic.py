from pcos_litwatch.heuristic import is_priority_title, skip_reason_for


def test_skips_nomenclature_and_reviews():
    assert skip_reason_for("From PCOS to PMOS: why terminology change matters") == "heuristic:title-skip"
    assert skip_reason_for("Harnessing herbs against ferroptosis: a review") == "heuristic:review"
    assert skip_reason_for("PCOS management", source_type="review") == "heuristic:review"


def test_lets_rct_through():
    assert skip_reason_for("Letrozole versus clomiphene in PCOS: a randomized trial") is None
    assert is_priority_title("Letrozole versus clomiphene in PCOS: a randomized trial")


def test_animal_only():
    assert skip_reason_for("Androgen excess in a rat model of PCOS") == "heuristic:animal-only"
    assert skip_reason_for("Androgen excess in women with PCOS: a trial") is None
