from datetime import datetime
from transaction_simulator.transaction_models import SimulationConfig, Event
from transaction_simulator.life_simulator import LifeTransactionSimulator
from models import Person


def test_event_description_in_context():
    person = Person(name="Test", id="p1", gender="male", region="RU")
    config = SimulationConfig(
        target_person_id="p1",
        start_date=datetime.now(),
        days=1,
        events=[Event(day=0, type="personal", description="Important event")]
    )
    sim = LifeTransactionSimulator(config, [person])

    event = sim._check_for_event(0)
    assert event is not None
    assert event.description == "Important event"

    ctx = sim.daily_simulator._build_day_context(datetime.now(), event)
    assert any("Important event" in e for e in ctx.events)
