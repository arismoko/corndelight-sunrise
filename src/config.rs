//! Corn Delight's config (`CornDelightConfig.java`: a NeoForge COMMON spec, section `general`, two booleans) and
//! the load conditions that read it.
//!
//! The file is NeoForge's TOML as NightConfig writes it (a `#` comment line above each section and key, keys
//! indented by a tab). Reading follows `ModConfigSpec#correct`: a missing key, or one whose value is not a
//! boolean, takes its default and the file is rewritten in that form; unknown lines are dropped on such a
//! rewrite; a file that reads cleanly is left alone. The engine names the file after the mod id:
//! `ported_corn_delight-common.toml` (reference `corn_delight-common.toml`, delta CA10).
//!
//! Both keys are read when data loads (`genCornFarm` gates the village farm pieces, `villagersTradeCorn` the
//! farmer trades): an edit applies on the next world load or `/reload`.

use mod_api::*;
use std::sync::atomic::{AtomicBool, Ordering};

pub const COMMON_FILE: &str = "ported_corn_delight-common.toml";

/// One boolean key: its name, comment and default (declaration order = file order).
struct Key {
    name: &'static str,
    comment: &'static str,
    default: bool,
    value: AtomicBool,
}

const SECTION: &str = "general";
const SECTION_COMMENT: &str = "General settings";

static KEYS: [Key; 2] = [
    Key {
        name: "genCornFarm",
        comment: "Should this mod add corn farm to plains and taiga village?",
        default: true,
        value: AtomicBool::new(true),
    },
    Key {
        name: "villagersTradeCorn",
        comment: "Should Novice and Apprentice Farmers trade this mod's crops? (May reduce chances of other trades \
                  appearing)",
        default: true,
        value: AtomicBool::new(true),
    },
];

pub fn gen_corn_farm() -> bool {
    KEYS[0].value.load(Ordering::Relaxed)
}

pub fn villagers_trade_corn() -> bool {
    KEYS[1].value.load(Ordering::Relaxed)
}

/// The file text for these values (NightConfig's layout).
fn render(values: &[bool]) -> String {
    let mut out = format!("#{SECTION_COMMENT}\n[{SECTION}]\n");
    for (key, value) in KEYS.iter().zip(values) {
        out.push_str(&format!("\t#{}\n\t{} = {}\n", key.comment, key.name, value));
    }
    out.push('\n');
    out
}

pub fn default_text() -> String {
    render(&KEYS.iter().map(|k| k.default).collect::<Vec<_>>())
}

/// Reads `text`: the values of both keys, and whether the file needs correcting.
fn parse(text: &str) -> (Vec<bool>, bool) {
    let mut found: Vec<Option<bool>> = vec![None; KEYS.len()];
    let mut bad = false;
    let mut section = String::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        if let Some(name) = line.strip_prefix('[').and_then(|l| l.strip_suffix(']')) {
            section = name.trim().to_owned();
            continue;
        }
        let Some((name, value)) = line.split_once('=') else {
            continue;
        };
        if section != SECTION {
            continue;
        }
        let value = value.split('#').next().unwrap_or("").trim();
        if let Some(i) = KEYS.iter().position(|k| k.name == name.trim()) {
            match value {
                "true" => found[i] = Some(true),
                "false" => found[i] = Some(false),
                _ => bad = true,
            }
        }
    }
    let missing = found.iter().any(Option::is_none);
    let values = KEYS
        .iter()
        .zip(&found)
        .map(|(k, v)| v.unwrap_or(k.default))
        .collect();
    (values, bad || missing)
}

/// Loads the file's text into the values; returns the corrected text when the file needs rewriting.
pub fn load(text: &str) -> Option<String> {
    let (values, correct) = parse(text);
    for (key, value) in KEYS.iter().zip(&values) {
        key.value.store(*value, Ordering::Relaxed);
    }
    correct.then(|| render(&values))
}

pub fn register(mod_id: &str, configs: &mut Vec<Config>) {
    configs.push(Config::new(mod_id, ConfigKind::Common, &default_text()).file(COMMON_FILE));
}

pub fn on_file(host: HostSide<'_>, mod_id: &str, file: &ConfigFile) {
    if file.mod_id != mod_id || file.file != COMMON_FILE {
        return;
    }
    // A failed rewrite (read-only folder) leaves the file as the player wrote it; the values are loaded anyway.
    if let Some(corrected) = load(&file.text)
        && let Ok(path) = ConfigPath::new(&file.file)
    {
        let files = match host {
            HostSide::Server(h) => h.config_files(),
            HostSide::Client(h) => h.config_files(),
        };
        let _ = files.write(&path, corrected.as_bytes());
    }
}

/// `ported_corn_delight:gen_corn_farm`: true while `genCornFarm` is (no arguments).
pub struct GenCornFarm;

impl LoadCondition for GenCornFarm {
    fn test(&self, _: &serde_json::Value) -> Result<bool, ConditionError> {
        Ok(gen_corn_farm())
    }
}

/// `ported_corn_delight:villagers_trade_corn`: true while `villagersTradeCorn` is (no arguments).
pub struct VillagersTradeCorn;

impl LoadCondition for VillagersTradeCorn {
    fn test(&self, _: &serde_json::Value) -> Result<bool, ConditionError> {
        Ok(villagers_trade_corn())
    }
}

pub fn register_load_conditions(event: &mut RegisterLoadConditionsEvent<'_>) {
    // A registration error refuses admission even if ignored; nothing to recover here.
    let _ = event.conditions.register(
        Identifier::parse(crate::ids::GEN_CORN_FARM).expect("valid id"),
        GenCornFarm,
    );
    let _ = event.conditions.register(
        Identifier::parse(crate::ids::VILLAGERS_TRADE_CORN).expect("valid id"),
        VillagersTradeCorn,
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_file_reads_clean() {
        let text = default_text();
        assert!(text.starts_with("#General settings\n[general]\n\t#Should this mod add corn farm"));
        assert_eq!(parse(&text), (vec![true, true], false));
    }

    #[test]
    fn edited_values_load_without_rewrite() {
        let text = default_text().replace("genCornFarm = true", "genCornFarm = false");
        assert_eq!(parse(&text), (vec![false, true], false));
    }

    #[test]
    fn invalid_or_missing_values_take_defaults_and_correct() {
        let text = "[general]\n\tgenCornFarm = \"no\"\n";
        let (values, correct) = parse(text);
        assert_eq!(values, vec![true, true]);
        assert!(correct);
        // Keys in another section do not count.
        let (values, correct) = parse("[other]\ngenCornFarm = false\nvillagersTradeCorn = false\n");
        assert_eq!(values, vec![true, true]);
        assert!(correct);
        // A kept valid value survives the correction.
        let (values, _) = parse("[general]\nvillagersTradeCorn = false\n");
        assert_eq!(values, vec![true, false]);
        assert_eq!(
            render(&values),
            default_text().replace("villagersTradeCorn = true", "villagersTradeCorn = false")
        );
    }
}
