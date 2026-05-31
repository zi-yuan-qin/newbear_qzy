"""BE-006: seed_loader + world_factory 重写 测试"""
import sys; sys.path.insert(0, "backend")

# Test 1: No seed = old behavior
print("=== Test 1: seed=None (old behavior) ===")
from src.core.world.world_factory import create_initial_world_state
w = create_initial_world_state()
assert w.company.cash == 5000.0, "FAIL cash"
actor = list(w.actors.values())[0]
assert actor.stress == 30, "FAIL stress"
assert actor.energy == 70, "FAIL energy"
print("PASS: cash=5000, stress=30, energy=70")

# Test 2: SessionSeed provided
print()
print("=== Test 2: SessionSeed with modifiers ===")
from src.core.world.seed_loader import SessionSeed
seed = SessionSeed(
    seed_id="test-be006-001",
    company_params={"cash": 7500, "runway_days": 14, "strategy_consensus": 75, "team_morale": 80, "resource_scarcity": 35},
    character_modifiers={
        "xionglaoban": {"stress_base_offset": -5, "energy_base_offset": 8},
        "xiongjishu": {"stress_base_offset": 7, "energy_base_offset": -3},
        "xiongshichang": {"stress_base_offset": 0, "energy_base_offset": 0},
        "xiongxingzheng": {"stress_base_offset": -10, "energy_base_offset": 10},
    }
)
w2 = create_initial_world_state(seed=seed)
assert w2.company.cash == 7500.0, "FAIL cash"
assert w2.actors["xionglaoban"].stress == 25, f"FAIL laoban stress={w2.actors['xionglaoban'].stress}"
assert w2.actors["xionglaoban"].energy == 78, f"FAIL energy"
assert w2.actors["xiongjishu"].stress == 37, f"FAIL jishu stress"
assert w2.actors["xiongxingzheng"].energy == 80, "FAIL energy"
print(f"PASS: cash={w2.company.cash}")

# Test 3: load_world_seed(user_id)
print()
print("=== Test 3: load_world_seed with user_id ===")
from src.core.world.seed_loader import load_world_seed
s = load_world_seed(user_id=1)
assert len(s["characters"]) == 4
print(f"PASS: {len(s['characters'])} chars, runway={s['company'].get('runway_days')}")

# Test 4: Randomness
print()
print("=== Test 4: Randomness ===")
cash_set = set()
for i in range(5):
    si = load_world_seed(user_id=i)
    cash_set.add(si["company"].get("runway_days"))
assert len(cash_set) >= 2, f"FAIL: only {len(cash_set)} different values"
print(f"PASS: 5 calls produced {len(cash_set)} different runway values")

# Test 5: No user_id = old behavior
print()
print("=== Test 5: backward compat ===")
s = load_world_seed()
assert s["company"]["runway_days"] == 10
print("PASS: backward compatible")

# Test 6: Server imports
print()
print("=== Test 6: imports ===")
from src.core.config.company_profile import build_company_profile
from src.core.world.seed_loader import SessionSeed
print(f"PASS: SessionSeed (from seed_loader) + build_company_profile (from company_profile) imports OK")

print()
print("ALL TESTS PASSED")
