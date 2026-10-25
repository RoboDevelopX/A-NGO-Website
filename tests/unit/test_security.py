from starlette.datastructures import FormData

from app.security import RateLimiter, hash_ip, honeypot_triggered, new_form_nonce, read_form_nonce


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_rate_limiter_blocks_after_max_hits_and_recovers_after_window():
    clock = FakeClock()
    limiter = RateLimiter(max_hits=3, window_seconds=60, clock=clock)
    assert [limiter.hit("ip") for _ in range(4)] == [True, True, True, False]
    assert 1 <= limiter.retry_after("ip") <= 61
    clock.now += 61
    assert limiter.hit("ip") is True


def test_rate_limiter_is_per_key_and_sliding():
    clock = FakeClock()
    limiter = RateLimiter(max_hits=2, window_seconds=60, clock=clock)
    assert limiter.hit("a") and limiter.hit("b")
    limiter.hit("a")
    clock.now += 30
    assert limiter.hit("a") is False  # both earlier hits still inside the window
    clock.now += 31
    assert limiter.hit("a") is True  # the first hit slid out


def test_blocked_attempts_do_not_extend_the_ban():
    clock = FakeClock()
    limiter = RateLimiter(max_hits=1, window_seconds=10, clock=clock)
    limiter.hit("ip")
    for _ in range(5):
        clock.now += 1
        limiter.hit("ip")
    clock.now = 1011
    assert limiter.hit("ip") is True


def test_hash_ip_is_stable_keyed_and_not_reversible_by_eye():
    assert hash_ip("203.0.113.9", "k1") == hash_ip("203.0.113.9", "k1")
    assert hash_ip("203.0.113.9", "k1") != hash_ip("203.0.113.9", "k2")
    assert "203" not in hash_ip("203.0.113.9", "k1")


def test_honeypot():
    assert honeypot_triggered(FormData({"website": "http://spam.example"}))
    assert not honeypot_triggered(FormData({"website": "  "}))
    assert not honeypot_triggered(FormData({}))


def test_form_nonce_format():
    nonce = new_form_nonce()
    assert read_form_nonce(FormData({"form_nonce": nonce})) == nonce
    assert read_form_nonce(FormData({"form_nonce": "../../etc/passwd"})) is None
    assert read_form_nonce(FormData({})) is None
