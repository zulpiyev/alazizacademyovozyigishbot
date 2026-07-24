from app.utils.percent_card import percent_card_row


def test_percent_card_row_shows_branch_before_student_and_only_percent():
    text = percent_card_row(
        "Normuxamedova Madina",
        "Chinoz",
        100.0,
        selected=True,
    )

    assert "Chinoz" in text
    assert text.index("Chinoz") < text.index("Normuxamedova Madina")
    assert "100.0%" in text
    assert "\n" not in text
    assert "Normuxamedova Madina — 📈 <b>100.0%</b>" in text
    assert "✅" in text
    assert "ovoz" not in text.lower()
    assert "jami" not in text.lower()
