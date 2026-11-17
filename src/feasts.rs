//! The nachos block and the popcorn box (CD-11), both FD feasts through the base's `api::feast`.
//!
//! - `NachosBlock` (BlockRegistry.NACHOS_BLOCK) is `FeastBlock(cake properties, nachos_bowl, true)`
//!   with its own outline (declared): FD's feast as it stands, FD Refabricated 26.3 semantics (CA6).
//! - `PopcornBoxBlock` is `FeastBlock(yellow wool, caramel_popcorn, true)` overriding `useItemOn`
//!   with its own `takeServing` (restated here in my words; the rest of `FeastBlock` — rigid floor,
//!   comparator, pathfinding — stays the base's):
//!   * no servings left: the wool-break sound (players, 0.8/0.8) and the block breaks with drops;
//!   * an empty hand: one serving fewer, a caramel popcorn into the inventory (dropped when full);
//!     taking the last one also gives a paper and removes the block (no drops, no break effects);
//!     then the generic armour-equip sound (blocks, 1/1);
//!   * anything in hand: "Use your bare hand to grab popcorn." on the action bar, with the
//!     serving's crafting remainder's name as an argument the text never shows (CQ2), and the use
//!     passes on (to the item, then to the other hand).
use mod_api::*;
use ported_farmersdelight::api::feast::{self, FeastSpec};

pub const NACHOS_BLOCK: &str = "corn_delight:nachos_block";
pub const POPCORN_BOX: &str = "corn_delight:popcorn_box";
const NACHOS_BOWL: &str = "corn_delight:nachos_bowl";
const CARAMEL_POPCORN: &str = "corn_delight:caramel_popcorn";
const PAPER: &str = "minecraft:paper";
const BARE_HAND: &str = "corn_delight.block.popcorn.bearhand";
const SOUND_SERVE: &str = "minecraft:item.armor.equip_generic";
const SOUND_EMPTY: &str = "minecraft:block.wool.break";

fn nachos_serving(_: u32) -> Option<&'static str> {
    Some(NACHOS_BOWL)
}

fn popcorn_serving(_: u32) -> Option<&'static str> {
    Some(CARAMEL_POPCORN)
}

pub fn register(registrar: &mut dyn Registrar) {
    feast::register(
        registrar,
        NACHOS_BLOCK,
        FeastSpec {
            serving_item: nachos_serving,
            has_leftovers: true,
            serving_particles: true,
            servings_property: "servings",
        },
    );
    feast::register_custom(
        registrar,
        POPCORN_BOX,
        FeastSpec {
            serving_item: popcorn_serving,
            has_leftovers: true,
            serving_particles: true,
            servings_property: "servings",
        },
        popcorn_use,
        popcorn_predict,
    );
}

// ---------------------------------------------------------------- the popcorn box's rule

/// What one use of the popcorn box does.
#[derive(Debug, PartialEq, Eq)]
pub enum Popcorn {
    /// No servings left: break it with drops.
    BreakEmpty,
    /// Take one serving; `last`: it was the last, so a paper too and the block goes.
    Serve { last: bool },
    /// Something in the hand: the bare-hand message, and the use passes on.
    BareHand,
}

pub fn decide(servings: u32, hand_empty: bool) -> Popcorn {
    if servings == 0 {
        Popcorn::BreakEmpty
    } else if hand_empty {
        Popcorn::Serve {
            last: servings == 1,
        }
    } else {
        Popcorn::BareHand
    }
}

fn empty(held: Option<&ItemStack>) -> bool {
    held.is_none_or(|s| s.count() == 0)
}

/// The client's answer (useItemOn runs takeServing on the client too and answers SUCCESS when it
/// acts); a pass lets the client try the item and then the other hand.
fn popcorn_predict(servings: u32, held: Option<&ItemStack>) -> InteractionResult {
    match decide(servings, empty(held)) {
        Popcorn::BareHand => InteractionResult::Pass,
        _ => InteractionResult::Success,
    }
}

fn popcorn_use(
    host: &mut dyn ServerHost,
    click: &BlockClick<'_>,
    state: BlockState,
    spec: &FeastSpec,
    _: ParticleKey,
) -> InteractionResult {
    let Some(player) = host.players().acting_player() else {
        return InteractionResult::Pass;
    };
    let Some(level) = host.level(click.dimension.key().id()) else {
        return InteractionResult::Pass;
    };
    let pos = click.pos;
    let at = [
        pos[0] as f64 + 0.5,
        pos[1] as f64 + 0.5,
        pos[2] as f64 + 0.5,
    ];
    let servings = feast::servings(&*host, state, spec);
    match decide(servings, empty(click.stack)) {
        Popcorn::BreakEmpty => {
            level.play_sound(host, SOUND_EMPTY, at, SoundSource::Players, 0.8, 0.8, None);
            let _ = level.destroy_block(host, pos, true, None, false);
            InteractionResult::Success
        }
        Popcorn::Serve { last } => {
            host.set_block_property_with(
                pos,
                spec.servings_property,
                &(servings - 1).to_string(),
                3,
            );
            give(host, player, CARAMEL_POPCORN);
            if last {
                give(host, player, PAPER);
                let _ = level.remove_block(host, pos, false);
            }
            level.play_sound(host, SOUND_SERVE, at, SoundSource::Blocks, 1.0, 1.0, None);
            InteractionResult::Success
        }
        Popcorn::BareHand => {
            // CQ2: the argument is `serving.getCraftingRemainingItem().getHoverName()`; caramel popcorn
            // has no remainder, so it is the empty stack's name, and the text has no placeholder.
            let remainder = Text::translate("block.minecraft.air", vec![]);
            let _ = player.action_bar(host, Text::translate(BARE_HAND, vec![remainder]));
            InteractionResult::TryWithEmptyHand
        }
    }
}

/// `Inventory.add`, else `Player.drop`.
fn give(host: &mut dyn ServerHost, player: PlayerRef, id: &str) {
    let Some(stack) = Identifier::parse(id)
        .ok()
        .and_then(|i| host.item_key(&i))
        .and_then(|k| ItemStack::new(k, 1))
    else {
        return;
    };
    let _ = host.transaction(|host, tx| {
        let resource = ItemResource::of(&stack);
        let inserted = player
            .entity()
            .capability(host, &ENTITY_ITEMS, ())
            .map_or(0, |inv| inv.insert_any(host, tx, &resource, 1));
        if inserted < 1 {
            let _ = player.drop_stack(host, stack.clone(), false);
        }
        Ok::<_, ()>(())
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn popcorn_decision_table() {
        // (servings, empty hand) → outcome, from PopcornBoxBlock#takeServing.
        assert_eq!(decide(0, true), Popcorn::BreakEmpty);
        assert_eq!(decide(0, false), Popcorn::BreakEmpty);
        assert_eq!(decide(4, true), Popcorn::Serve { last: false });
        assert_eq!(decide(2, true), Popcorn::Serve { last: false });
        assert_eq!(decide(1, true), Popcorn::Serve { last: true });
        for s in 1..=4 {
            assert_eq!(decide(s, false), Popcorn::BareHand);
        }
    }
}
