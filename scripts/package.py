"""Package only generated HTML and assets for GitHub Pages."""
import argparse
import shutil
from pathlib import Path

from build import PAGES, SITE, build_site


def package_site(output: Path) -> None:
    if output.resolve() == SITE.resolve() or SITE.resolve().is_relative_to(output.resolve()) or output.resolve().is_relative_to(SITE.resolve()):
        raise ValueError('Publish directory must be separate from site/')
    if output.exists() and any(output.iterdir()):
        raise ValueError(f'{output} is not empty; use a fresh publish directory')
    build_site(check=True)
    output.mkdir(parents=True, exist_ok=True)
    for name in PAGES.values():
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SITE / name, destination)
    shutil.copytree(SITE / 'assets', output / 'assets')
    (output / '.nojekyll').touch()
    print(f'Packaged generated pages and assets in {output}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('dist'))
    args = parser.parse_args()
    try:
        package_site(args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, f'Packaging failed: {error}\n')
