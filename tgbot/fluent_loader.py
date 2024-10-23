from pathlib import Path
from typing import List

from fluent.runtime import FluentLocalization, FluentResourceLoader


class ReloadableFluentLocalization(FluentLocalization):
    def reload(self):
        self._bundle_cache.clear()
        self._bundle_it = self._iterate_bundles()


def get_fluent_localization(language: str = "ru") -> FluentLocalization:
    """
    Loads FTL files for chosen language
    :param language: language name, as passed from configuration outside
    :return: FluentLocalization object with loaded FTL files for chosen language
    """

    def read_dir(path: Path) -> List[str]:
        files = []
        for file in path.iterdir():
            if file.is_dir():
                files += read_dir(file)
            if file.suffix == ".ftl":
                files.append(str(file.absolute()))

        return files

    # Check "locales" directory on the previous level from this file
    locales_dir = Path(__file__).parent.parent.joinpath("locales")
    if not locales_dir.exists():
        err = '"locales" directory does not exist'
        raise FileNotFoundError(err)
    if not locales_dir.is_dir():
        err = '"locales" is not a directory'
        raise NotADirectoryError(err)

    locales_dir = locales_dir.absolute()
    locale_dir_found = False
    for directory in Path.iterdir(locales_dir):
        if directory.stem == language:
            locale_dir_found = True
            break
    if not locale_dir_found:
        err = f'Directory for "{language}" locale not found'
        raise FileNotFoundError(err)

    locale_files = read_dir(Path(locales_dir, language))
    l10n_loader = FluentResourceLoader(str(Path.joinpath(locales_dir, "{locale}")))

    return ReloadableFluentLocalization([language], locale_files, l10n_loader)
