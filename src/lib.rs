//! Corn Delight — native Horizon port, an add-on of the Farmer's Delight port (`ported_farmersdelight`).
//! `Hooks` only dispatches; logic lives in modules.

mod config;
mod crop;
mod ids;

use mod_api::*;

#[derive(Default)]
struct CornDelight;

#[mod_api::horizon_mod]
impl Hooks for CornDelight {
    fn register_load_conditions(
        &self,
        _: &RegistrationContext,
        event: &mut RegisterLoadConditionsEvent<'_>,
    ) {
        config::register_load_conditions(event);
    }

    fn register_configs(&self, _: HostSide<'_>, event: &mut RegisterConfigsEvent<'_>) {
        config::register(ids::MOD_ID, event.configs);
    }

    fn config_loading(&self, host: HostSide<'_>, event: &mut ConfigLoadingEvent<'_>) {
        config::on_file(host, ids::MOD_ID, event.config);
    }

    fn config_reloading(&self, host: HostSide<'_>, event: &mut ConfigReloadingEvent<'_>) {
        config::on_file(host, ids::MOD_ID, event.config);
    }

    fn register(&self, registrar: &mut dyn Registrar, _: &RegistrationContext) {
        eprintln!("{}: base api {}", ids::MOD_NAMESPACE, base_api());
        crop::register(registrar);
        // Wild corn is FD's WildCropBlock(SATURATION, 8) (BlockRegistry.WILD_CORN): the base's wild-crop behaviour.
        ported_farmersdelight::api::wild_crop::register(
            registrar,
            ids::WILD_CORN,
            "minecraft:saturation",
            8,
        );
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
