//! Corn Delight — native Horizon port, an add-on of the Farmer's Delight port (`ported_farmersdelight`).
//! `Hooks` only dispatches; logic lives in modules.

mod ids;

use mod_api::*;

#[derive(Default)]
struct CornDelight;

#[mod_api::horizon_mod]
impl Hooks for CornDelight {
    fn register(&self, _registrar: &mut dyn Registrar, _: &RegistrationContext) {
        eprintln!("{}: base api {}", ids::MOD_NAMESPACE, base_api());
    }
}

/// The base mod's add-on API version this build was compiled against.
pub fn base_api() -> u32 {
    ported_farmersdelight::api::API_VERSION
}

#[cfg(test)]
mod tests {
    #[test]
    fn built_against_base_api_1() {
        assert_eq!(super::base_api(), 1);
    }
}
