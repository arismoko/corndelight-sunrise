//! Chest loot (CA2). Corn Delight adds its tables with MMLib's `add_loot_table` global loot
//! modifiers (`data/corn_delight/loot_modifiers/{village_house,shipwreck_loot}.json`): after the
//! chest's own pools, the extra table is rolled with the same context and its items are appended.
//! Global loot modifiers are not loaded here, so `loot_table_load` appends one pool to the chest
//! table whose single entry is the extra table: a one-entry pool with one roll draws nothing of its
//! own, so the same draws happen in the same order (the base appends FD's chest pools before this
//! runs, as FD's pools come before CD's modifier). Stack splitting never applies (counts ≤ 4).
use mod_api::serde_json::{Value, json};

const VILLAGE_HOUSE: &str = "corn_delight:village_house";
const SHIPWRECK_SUPPLY: &str = "corn_delight:shipwreck_supply";

/// The chest tables each modifier names (its `neoforge:loot_table_id` conditions).
pub const TARGETS: [(&str, &str); 6] = [
    (
        "minecraft:chests/village/village_plains_house",
        VILLAGE_HOUSE,
    ),
    (
        "minecraft:chests/village/village_desert_house",
        VILLAGE_HOUSE,
    ),
    (
        "minecraft:chests/village/village_savanna_house",
        VILLAGE_HOUSE,
    ),
    (
        "minecraft:chests/village/village_snowy_house",
        VILLAGE_HOUSE,
    ),
    (
        "minecraft:chests/village/village_taiga_house",
        VILLAGE_HOUSE,
    ),
    ("minecraft:chests/shipwreck_supply", SHIPWRECK_SUPPLY),
];

pub fn on_table_load(id: &str, table: &mut Value) {
    let Some((_, extra)) = TARGETS.iter().find(|(t, _)| *t == id) else {
        return;
    };
    let pool = json!({"rolls": 1, "entries": [{"type": "minecraft:loot_table", "value": extra}]});
    match table.get_mut("pools").and_then(Value::as_array_mut) {
        Some(pools) => pools.push(pool),
        None => table["pools"] = json!([pool]),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn extra_of(id: &str) -> Option<Value> {
        let mut t = json!({"type": "minecraft:chest", "pools": [{"rolls": 1, "entries": []}]});
        on_table_load(id, &mut t);
        let pools = t["pools"].as_array().unwrap();
        (pools.len() == 2).then(|| pools[1]["entries"][0]["value"].clone())
    }

    #[test]
    fn pools_appended_for_exactly_the_six_tables() {
        for house in ["plains", "desert", "savanna", "snowy", "taiga"] {
            assert_eq!(
                extra_of(&format!("minecraft:chests/village/village_{house}_house")),
                Some(json!("corn_delight:village_house"))
            );
        }
        assert_eq!(
            extra_of("minecraft:chests/shipwreck_supply"),
            Some(json!("corn_delight:shipwreck_supply"))
        );
        for other in [
            "minecraft:chests/village/village_butcher",
            "minecraft:chests/shipwreck_map",
            "minecraft:chests/shipwreck_treasure",
            "minecraft:chests/simple_dungeon",
            "farmersdelight:chests/fd_village_plains_house",
        ] {
            assert_eq!(extra_of(other), None, "{other}");
        }
    }

    #[test]
    fn pool_after_existing_pools_and_on_a_table_without_pools() {
        let mut t = json!({"type": "minecraft:chest"});
        on_table_load("minecraft:chests/shipwreck_supply", &mut t);
        assert_eq!(t["pools"].as_array().unwrap().len(), 1);
        assert_eq!(t["pools"][0]["rolls"], json!(1));
    }
}
