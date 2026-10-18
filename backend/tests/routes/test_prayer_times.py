from mosques import MOSQUES


def test_prayer_times_merges_mosque_metadata(client, app, prayer_times_factory):
    mosque = MOSQUES[0]
    prayer_times_factory(mosque_name=mosque["name"])

    resp = client.get("/prayer-times")
    assert resp.status_code == 200
    data = resp.get_json()

    match = next((m for m in data if m["name"] == mosque["name"]), None)
    assert match is not None
    assert match["address"] == mosque["address"]
    assert match["latitude"] == mosque["latitude"]
    assert "prayer_times" in match


def test_prayer_times_omits_unknown_mosque(client, app, prayer_times_factory):
    prayer_times_factory(mosque_name="Unknown Mosque XYZ")

    resp = client.get("/prayer-times")
    data = resp.get_json()

    names = [m["name"] for m in data]
    assert "Unknown Mosque XYZ" not in names
