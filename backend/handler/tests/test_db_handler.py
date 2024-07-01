from handler.auth import auth_handler
from handler.database import (
    db_platform_handler,
    db_rom_handler,
    db_save_handler,
    db_screenshot_handler,
    db_state_handler,
    db_user_handler,
)
from models.assets import Save, Screenshot, State
from models.platform import Platform
from models.rom import Rom
from models.user import Role, User
from sqlalchemy.exc import IntegrityError


def test_platforms():
    platform = Platform(
        name="test_platform", slug="test_platform_slug", fs_slug="test_platform_slug"
    )
    db_platform_handler.add_platform(platform)

    platforms = db_platform_handler.get_platforms()
    assert len(platforms) == 1

    platform = db_platform_handler.get_platform_by_fs_slug(platform.fs_slug)
    assert platform.name == "test_platform"

    db_platform_handler.purge_platforms([])
    platforms = db_platform_handler.get_platforms()
    assert len(platforms) == 0


def test_roms(rom: Rom, platform: Platform):
    db_rom_handler.add_rom(
        Rom(
            platform_id=rom.platform_id,
            name="test_rom_2",
            slug="test_rom_slug_2",
            file_name="test_rom_2",
            file_name_no_tags="test_rom_2",
            file_name_no_ext="test_rom_2",
            file_extension="zip",
            file_path=f"{platform.slug}/roms",
            file_size_bytes=1000.0,
        )
    )

    with db_rom_handler.session.begin() as session:
        roms = session.scalars(db_rom_handler.get_roms(platform_id=platform.id)).all()
        assert len(roms) == 2

    rom = db_rom_handler.get_rom(roms[0].id)
    assert rom is not None
    assert rom.file_name == "test_rom.zip"

    db_rom_handler.update_rom(roms[1].id, {"file_name": "test_rom_2_updated"})
    rom_2 = db_rom_handler.get_rom(roms[1].id)
    assert rom_2 is not None
    assert rom_2.file_name == "test_rom_2_updated"

    db_rom_handler.delete_rom(rom.id)

    with db_rom_handler.session.begin() as session:
        roms = session.scalars(db_rom_handler.get_roms(platform_id=platform.id)).all()
        assert len(roms) == 1

    db_rom_handler.purge_roms(rom_2.platform_id, [rom_2.id])

    with db_rom_handler.session.begin() as session:
        roms = session.scalars(db_rom_handler.get_roms(platform_id=platform.id)).all()
        assert len(roms) == 0


def test_utils(rom: Rom, platform: Platform):
    with db_rom_handler.session.begin() as session:
        roms = session.scalars(db_rom_handler.get_roms(platform_id=platform.id)).all()
        assert (
            db_rom_handler.get_rom_by_filename(
                platform_id=platform.id, file_name=rom.file_name
            ).id
            == roms[0].id
        )


def test_users(admin_user):
    db_user_handler.add_user(
        User(
            username="new_user",
            hashed_password=auth_handler.get_password_hash("new_password"),
        )
    )

    all_users = db_user_handler.get_users()
    assert len(all_users) == 2

    new_user = db_user_handler.get_user_by_username("new_user")
    assert new_user.username == "new_user"
    assert new_user.role == Role.VIEWER
    assert new_user.enabled

    db_user_handler.update_user(new_user.id, {"role": Role.EDITOR})

    new_user = db_user_handler.get_user(new_user.id)
    assert new_user.role == Role.EDITOR

    db_user_handler.delete_user(new_user.id)

    all_users = db_user_handler.get_users()
    assert len(all_users) == 1

    try:
        new_user = db_user_handler.add_user(
            User(
                username="test_admin",
                hashed_password=auth_handler.get_password_hash("new_password"),
                role=Role.ADMIN,
            )
        )
    except IntegrityError as e:
        assert "Duplicate entry 'test_admin' for key" in str(e)


def test_saves(save: Save, platform: Platform, admin_user: User):
    db_save_handler.add_save(
        Save(
            rom_id=save.rom_id,
            user_id=admin_user.id,
            file_name="test_save_2.sav",
            file_name_no_tags="test_save_2",
            file_name_no_ext="test_save_2",
            file_extension="sav",
            emulator="test_emulator",
            file_path=f"{platform.slug}/saves/test_emulator",
            file_size_bytes=1.0,
        )
    )

    rom = db_rom_handler.get_rom(save.rom_id)
    assert rom is not None
    assert len(rom.saves) == 2

    save = db_save_handler.get_save(rom.saves[0].id)
    assert save.file_name == "test_save.sav"

    db_save_handler.update_save(save.id, {"file_name": "test_save_2.sav"})
    save = db_save_handler.get_save(save.id)
    assert save.file_name == "test_save_2.sav"

    db_save_handler.delete_save(save.id)

    rom = db_rom_handler.get_rom(save.rom_id)
    assert rom is not None
    assert len(rom.saves) == 1


def test_states(state: State, platform: Platform, admin_user: User):
    db_state_handler.add_state(
        State(
            rom_id=state.rom_id,
            user_id=admin_user.id,
            file_name="test_state_2.state",
            file_name_no_tags="test_state_2",
            file_name_no_ext="test_state_2",
            file_extension="state",
            file_path=f"{platform.slug}/states",
            file_size_bytes=1.0,
        )
    )

    rom = db_rom_handler.get_rom(state.rom_id)
    assert rom is not None
    assert len(rom.states) == 2

    state = db_state_handler.get_state(rom.states[0].id)
    assert state.file_name == "test_state.state"

    db_state_handler.update_state(state.id, {"file_name": "test_state_2.state"})
    state = db_state_handler.get_state(state.id)
    assert state.file_name == "test_state_2.state"

    db_state_handler.delete_state(state.id)

    rom = db_rom_handler.get_rom(state.rom_id)
    assert rom is not None
    assert len(rom.states) == 1


def test_screenshots(screenshot: Screenshot, platform: Platform, admin_user: User):
    db_screenshot_handler.add_screenshot(
        Screenshot(
            rom_id=screenshot.rom_id,
            user_id=admin_user.id,
            file_name="test_screenshot_2.png",
            file_name_no_tags="test_screenshot_2",
            file_name_no_ext="test_screenshot_2",
            file_extension="png",
            file_path=f"{platform.slug}/screenshots",
            file_size_bytes=1.0,
        )
    )

    rom = db_rom_handler.get_rom(screenshot.rom_id)
    assert rom is not None
    assert len(rom.screenshots) == 2

    screenshot = db_screenshot_handler.get_screenshot(rom.screenshots[0].id)
    assert screenshot.file_name == "test_screenshot.png"

    db_screenshot_handler.update_screenshot(
        screenshot.id, {"file_name": "test_screenshot_2.png"}
    )
    screenshot = db_screenshot_handler.get_screenshot(screenshot.id)
    assert screenshot.file_name == "test_screenshot_2.png"

    db_screenshot_handler.delete_screenshot(screenshot.id)

    rom = db_rom_handler.get_rom(screenshot.rom_id)
    assert rom is not None
    assert len(rom.screenshots) == 1
