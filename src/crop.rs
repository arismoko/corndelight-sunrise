//! The two-tall corn crop (`corn_crop`: CornCrop on MMLib's HighCropBlock, CD-06).
//!
//! Re-implemented from observed behaviour (MMLib has no licence file: nothing copied). A corn plant is a lower
//! block (`upper=false`) on farmland and, once grown, an upper block (`upper=true`) above it; each half has its
//! own `age` 0–7 and grows on its own (CQ6).
//!
//! - Random tick, at raw light ≥ 9: a half below age 7 grows one age with chance 1 / (⌊25 / growth speed⌋ + 1).
//!   A lower half whose age was at least 4 before this tick then rolls the same chance again and, on a hit,
//!   places an upper half (age 0) above it when the space is empty and an upper half could stand there.
//! - An upper half stands only on a lower corn half of age ≥ 4, at raw light ≥ 8 (sky view gives that too); a
//!   lower half keeps the crop rule of its template (farmland, light).
//! - Bone meal always succeeds and is refused only when the upper half (this one, or the one above this lower
//!   half) is fully grown. It adds 2–5 ages; past 7 the half stops at 7 and a lower half passes the rest on: it
//!   bone-meals an upper half already above it, or places one with the leftover age (total − 8).
//!
//! Pure decisions live in [`tick`], [`upper_survives`], [`bonemeal_valid`] and [`bonemeal`]; the Part only
//! reads the level, draws from its random in the reference's order and writes the result.
use mod_api::*;
use ported_farmersdelight::api::crop as fd_crop;

pub const CORN_CROP: &str = "corn_delight:corn_crop";
pub const MAX_AGE: u8 = 7;
/// `CornCrop#getGrowUpperAge`.
pub const GROW_UPPER_AGE: u8 = 4;

/// One corn half: its `age` and `upper`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Half {
    pub age: u8,
    pub upper: bool,
}

/// The `nextInt` bound of one growth roll: ⌊25 / speed⌋ + 1 (float division, truncated as Java's int cast).
pub fn roll_bound(speed: f32) -> i32 {
    (25.0f32 / speed) as i32 + 1
}

/// What a random tick does.
#[derive(Debug, PartialEq, Eq)]
pub struct TickPlan {
    /// The half's new age, when it grew.
    pub grow_to: Option<u8>,
    /// The upper-half roll hit: place an upper half (age 0) above if it fits there.
    pub try_upper: bool,
}

/// One random tick of `half`. `bright`: raw light ≥ 9. `roll()` is one growth roll (true = hit), called in the
/// reference's order: first for growth (only below max age), then for the upper half (only a lower half whose
/// age was ≥ 4 before the tick).
pub fn tick(half: Half, bright: bool, mut roll: impl FnMut() -> bool) -> TickPlan {
    let mut plan = TickPlan {
        grow_to: None,
        try_upper: false,
    };
    if !bright {
        return plan;
    }
    if half.age < MAX_AGE && roll() {
        plan.grow_to = Some(half.age + 1);
    }
    if !half.upper && half.age >= GROW_UPPER_AGE {
        plan.try_upper = roll();
    }
    plan
}

/// Whether an upper half survives on `below` (`None`: not a corn half). `lit`: raw light ≥ 8 at the upper half.
pub fn upper_survives(below: Option<Half>, lit: bool) -> bool {
    below.is_some_and(|b| !b.upper && lit && b.age >= GROW_UPPER_AGE)
}

/// `isValidBonemealTarget`: refused only when the relevant upper half is fully grown.
pub fn bonemeal_valid(this: Half, above: Option<Half>) -> bool {
    if let Some(up) = above {
        return up.age < MAX_AGE;
    }
    if this.upper {
        return this.age < MAX_AGE;
    }
    true
}

/// What bone meal does to the upper half.
#[derive(Debug, PartialEq, Eq)]
pub enum UpperBonemeal {
    None,
    /// Bone-meal the upper half above (when it is still a valid target).
    Pass,
    /// Place an upper half with this age (when it fits).
    Place(u8),
}

/// `performBonemeal` with `increase` (2–5): the half's new age and what happens above. `above`: the corn half
/// above a lower half, if any.
pub fn bonemeal(this: Half, increase: u8, above: Option<Half>) -> (u8, UpperBonemeal) {
    let total = (this.age + increase).min(15);
    if total <= MAX_AGE {
        return (total, UpperBonemeal::None);
    }
    if this.upper {
        return (MAX_AGE, UpperBonemeal::None);
    }
    match above {
        Some(_) => (MAX_AGE, UpperBonemeal::Pass),
        None => (MAX_AGE, UpperBonemeal::Place(total - MAX_AGE - 1)),
    }
}

// ---------------------------------------------------------------- the Part

fn value<'a>(state: &'a str, key: &str) -> Option<&'a str> {
    let props = state.split_once('[')?.1.strip_suffix(']')?;
    props.split(',').find_map(|kv| {
        kv.split_once('=')
            .filter(|(k, _)| *k == key)
            .map(|(_, v)| v)
    })
}

/// The corn half of `state`, `None` for any other block.
fn half_of(level: &dyn LevelHost, state: BlockState) -> Option<Half> {
    let s = level.state_string(state)?;
    if s.split('[').next() != Some(CORN_CROP) {
        return None;
    }
    Some(Half {
        age: value(&s, "age")?.parse().ok()?,
        upper: value(&s, "upper")? == "true",
    })
}

fn half_at(level: &dyn LevelHost, pos: [i32; 3]) -> Option<Half> {
    level.block_state(pos).and_then(|s| half_of(level, s))
}

fn up(pos: [i32; 3], n: i32) -> [i32; 3] {
    [pos[0], pos[1] + n, pos[2]]
}

fn is_air(level: &dyn LevelHost, pos: [i32; 3]) -> bool {
    level.block_state(pos).is_some_and(|s| {
        matches!(
            level.state_block(s),
            Some("minecraft:air" | "minecraft:cave_air" | "minecraft:void_air")
        )
    })
}

fn state_of(level: &dyn LevelHost, half: Half) -> Option<BlockState> {
    let base = level.block_state_id(CORN_CROP)?;
    let s = level.state_with_property(base, "age", &half.age.to_string())?;
    level.state_with_property(s, "upper", if half.upper { "true" } else { "false" })
}

/// An upper half could be placed above the lower half at `lower_pos` whose age is `lower_age`: the space is
/// empty and the upper half would survive there.
fn upper_fits(level: &dyn LevelHost, lower_pos: [i32; 3], lower_age: u8) -> bool {
    let above = up(lower_pos, 1);
    is_air(level, above)
        && upper_survives(
            Some(Half {
                age: lower_age,
                upper: false,
            }),
            level.raw_brightness(above, 0) >= 8,
        )
}

pub struct CornCrop;

impl CornCrop {
    fn bonemeal_at(level: &mut dyn LevelWriteHost, pos: [i32; 3], this: Half, depth: u8) {
        let Some(increase) = fd_crop::next_int(level, 4).map(|n| n as u8 + 2) else {
            return;
        };
        let above = if this.upper {
            None
        } else {
            half_at(level, up(pos, 1))
        };
        let (age, upper) = bonemeal(this, increase, above);
        if let Some(s) = state_of(
            level,
            Half {
                age,
                upper: this.upper,
            },
        ) {
            level.set_block(
                pos,
                s,
                BlockUpdateFlags::NEIGHBORS | BlockUpdateFlags::CLIENTS,
            );
        }
        match upper {
            UpperBonemeal::None => {}
            UpperBonemeal::Pass => {
                if let Some(top) = above
                    && depth == 0
                    && bonemeal_valid(top, None)
                {
                    Self::bonemeal_at(level, up(pos, 1), top, depth + 1);
                }
            }
            UpperBonemeal::Place(top_age) => {
                if upper_fits(level, pos, age)
                    && let Some(s) = state_of(
                        level,
                        Half {
                            age: top_age,
                            upper: true,
                        },
                    )
                {
                    level.set_block(
                        up(pos, 1),
                        s,
                        BlockUpdateFlags::NEIGHBORS | BlockUpdateFlags::CLIENTS,
                    );
                }
            }
        }
    }
}

#[crate::engine::part]
impl BlockPart for CornCrop {
    fn random_tick(&self, level: &mut dyn LevelWriteHost, event: &mut RandomTickEvent) -> Flow {
        let pos = [event.pos.x, event.pos.y, event.pos.z];
        let Some(half) = half_of(level, event.state) else {
            return Flow::Continue;
        };
        let bright = level.raw_brightness(pos, 0) >= 9;
        let bound = roll_bound(fd_crop::growth_speed(level, event.state, pos));
        let plan = tick(half, bright, || fd_crop::next_int(level, bound) == Some(0));
        if let Some(age) = plan.grow_to
            && let Some(s) = state_of(
                level,
                Half {
                    age,
                    upper: half.upper,
                },
            )
        {
            level.set_block(pos, s, BlockUpdateFlags::CLIENTS);
        }
        if plan.try_upper
            && upper_fits(level, pos, plan.grow_to.unwrap_or(half.age))
            && let Some(s) = state_of(
                level,
                Half {
                    age: 0,
                    upper: true,
                },
            )
        {
            level.set_block(
                up(pos, 1),
                s,
                BlockUpdateFlags::NEIGHBORS | BlockUpdateFlags::CLIENTS,
            );
        }
        Flow::Cancel
    }

    /// Upper halves need the lower corn half; lower halves keep the template's crop rule.
    fn can_survive(&self, level: &dyn LevelHost, event: &mut CanSurviveEvent) -> Option<bool> {
        let pos = [event.pos.x, event.pos.y, event.pos.z];
        let below = half_at(level, up(pos, -1))?;
        Some(upper_survives(
            Some(below),
            level.raw_brightness(pos, 0) >= 8,
        ))
    }

    fn is_valid_bonemeal_target(
        &self,
        level: LevelSide,
        event: &mut IsValidBonemealTargetEvent,
    ) -> Option<bool> {
        let (LevelSide::Server(level) | LevelSide::Client(level)) = level;
        let pos = [event.pos.x, event.pos.y, event.pos.z];
        let this = half_of(level, event.state)?;
        Some(bonemeal_valid(this, half_at(level, up(pos, 1))))
    }

    fn is_bonemeal_success(&self, _: &mut dyn LevelRandomHost, event: &mut IsBonemealSuccessEvent) {
        event.success = true;
    }

    fn perform_bonemeal(&self, level: &mut dyn LevelWriteHost, event: &mut PerformBonemealEvent) {
        let pos = [event.pos.x, event.pos.y, event.pos.z];
        if let Some(this) = half_of(level, event.state) {
            Self::bonemeal_at(level, pos, this, 0);
        }
    }
}

pub fn register(registrar: &mut dyn Registrar) {
    let key = registrar.block_key(CORN_CROP);
    registrar.block_part(key, CornCrop);
}

#[cfg(test)]
mod tests {
    use super::*;

    const fn lower(age: u8) -> Half {
        Half { age, upper: false }
    }
    const fn upper(age: u8) -> Half {
        Half { age, upper: true }
    }

    /// Rolls answered from a script; panics if the reference would not draw that many.
    fn script(hits: &[bool]) -> impl FnMut() -> bool + '_ {
        let mut i = 0;
        move || {
            let h = hits[i];
            i += 1;
            h
        }
    }

    fn run(half: Half, bright: bool, hits: &[bool]) -> (TickPlan, usize) {
        let mut n = 0;
        let mut s = script(hits);
        let plan = tick(half, bright, || {
            n += 1;
            s()
        });
        (plan, n)
    }

    #[test]
    fn dark_draws_nothing() {
        assert_eq!(
            run(lower(2), false, &[]),
            (
                TickPlan {
                    grow_to: None,
                    try_upper: false
                },
                0
            )
        );
        assert_eq!(run(lower(5), false, &[]).1, 0);
    }

    #[test]
    fn young_lower_grows_with_one_roll() {
        assert_eq!(
            run(lower(0), true, &[true]),
            (
                TickPlan {
                    grow_to: Some(1),
                    try_upper: false
                },
                1
            )
        );
        assert_eq!(
            run(lower(3), true, &[false]),
            (
                TickPlan {
                    grow_to: None,
                    try_upper: false
                },
                1
            )
        );
    }

    #[test]
    fn upper_roll_uses_the_age_before_the_tick() {
        // Age 3 growing to 4 does not roll for the upper half in the same tick.
        assert_eq!(
            run(lower(3), true, &[true]),
            (
                TickPlan {
                    grow_to: Some(4),
                    try_upper: false
                },
                1
            )
        );
        // Age 4: two rolls.
        assert_eq!(
            run(lower(4), true, &[false, true]),
            (
                TickPlan {
                    grow_to: None,
                    try_upper: true
                },
                2
            )
        );
        assert_eq!(
            run(lower(4), true, &[true, true]),
            (
                TickPlan {
                    grow_to: Some(5),
                    try_upper: true
                },
                2
            )
        );
        assert_eq!(
            run(lower(6), true, &[true, false]),
            (
                TickPlan {
                    grow_to: Some(7),
                    try_upper: false
                },
                2
            )
        );
    }

    #[test]
    fn mature_lower_still_rolls_for_the_upper() {
        assert_eq!(
            run(lower(7), true, &[true]),
            (
                TickPlan {
                    grow_to: None,
                    try_upper: true
                },
                1
            )
        );
        assert_eq!(
            run(lower(7), true, &[false]),
            (
                TickPlan {
                    grow_to: None,
                    try_upper: false
                },
                1
            )
        );
    }

    #[test]
    fn upper_half_grows_alone() {
        assert_eq!(
            run(upper(4), true, &[true]),
            (
                TickPlan {
                    grow_to: Some(5),
                    try_upper: false
                },
                1
            )
        );
        assert_eq!(
            run(upper(7), true, &[]),
            (
                TickPlan {
                    grow_to: None,
                    try_upper: false
                },
                0
            )
        );
    }

    #[test]
    fn roll_bounds() {
        assert_eq!(roll_bound(1.0), 26);
        assert_eq!(roll_bound(10.0), 3); // moist farmland row
        assert_eq!(roll_bound(4.0), 7);
        assert_eq!(roll_bound(5.5), 5);
    }

    #[test]
    fn upper_survival() {
        assert!(upper_survives(Some(lower(4)), true));
        assert!(upper_survives(Some(lower(7)), true));
        assert!(!upper_survives(Some(lower(3)), true));
        assert!(!upper_survives(Some(lower(5)), false));
        assert!(!upper_survives(Some(upper(7)), true));
        assert!(!upper_survives(None, true));
    }

    #[test]
    fn bonemeal_targets() {
        assert!(bonemeal_valid(lower(7), None)); // no upper above: always (even fully grown)
        assert!(bonemeal_valid(lower(2), Some(upper(3))));
        assert!(!bonemeal_valid(lower(7), Some(upper(7))));
        assert!(!bonemeal_valid(lower(3), Some(upper(7))));
        assert!(bonemeal_valid(upper(6), None));
        assert!(!bonemeal_valid(upper(7), None));
    }

    #[test]
    fn bonemeal_within_the_half() {
        assert_eq!(bonemeal(lower(0), 2, None), (2, UpperBonemeal::None));
        assert_eq!(bonemeal(lower(2), 5, None), (7, UpperBonemeal::None));
        assert_eq!(bonemeal(upper(1), 3, None), (4, UpperBonemeal::None));
    }

    #[test]
    fn bonemeal_overflow() {
        // 6 + 2 = 8: lower to 7, a new upper half at 8 - 8 = 0.
        assert_eq!(bonemeal(lower(6), 2, None), (7, UpperBonemeal::Place(0)));
        // 7 + 5 = 12: upper half at age 4.
        assert_eq!(bonemeal(lower(7), 5, None), (7, UpperBonemeal::Place(4)));
        // An upper half already above: it is bone-mealed in turn.
        assert_eq!(
            bonemeal(lower(5), 4, Some(upper(2))),
            (7, UpperBonemeal::Pass)
        );
        // An upper half caps at 7 and passes nothing on.
        assert_eq!(bonemeal(upper(6), 5, None), (7, UpperBonemeal::None));
    }

    #[test]
    fn state_values() {
        assert_eq!(
            value("corn_delight:corn_crop[age=4,upper=true]", "upper"),
            Some("true")
        );
        assert_eq!(
            value("corn_delight:corn_crop[age=4,upper=true]", "age"),
            Some("4")
        );
        assert_eq!(value("corn_delight:corn_crop", "age"), None);
    }
}
