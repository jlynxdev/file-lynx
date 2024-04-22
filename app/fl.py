import os
import platform
from datetime import datetime
import re
import typer
from rich.console import Console
from rich.table import Table
import datetime as dt
from filelynx import FileLynx
from utils import determine_type
from helptext import HelpText
from typing import Annotated, Optional
from enum import StrEnum

VERSION = '0.1.0'

app = typer.Typer(no_args_is_help=True,
                  rich_markup_mode='markdown',
                  epilog='Made with :heart: by [jlynxdev](https://github.com/jlynxdev)')
console = Console()
err_console = Console(stderr=True)
filelynx = FileLynx(os.getcwd())


def get_cwd() -> str:
    return os.getcwd()


def _convert_date_format(orig: str) -> str:
    cnv = orig.replace('month', '%b')
    cnv = cnv.replace('Month', '%B')
    cnv = cnv.replace('D', '%d')
    cnv = cnv.replace('M', '%m')
    cnv = cnv.replace('y', '%y')
    cnv = cnv.replace('Y', '%Y')
    if platform.system() == 'Windows':
        cnv = re.sub('(?<!%)(?<!%-)(?<!%#)d', '%#d', cnv)
        cnv = re.sub('(?<!%)(?<!%-)(?<!%#)m', '%#m', cnv)
    else:
        cnv = re.sub('(?<!%)(?<!%-)(?<!%#)d', '%-d', cnv)
        cnv = re.sub('(?<!%)(?<!%-)(?<!%#)m', '%-m', cnv)
    return cnv


def _convert_extensions_arg(extensions: str) -> list[str]:
    extension_filter = extensions.split(',')
    extension_filter = [ext.strip().lower() for ext in extension_filter]
    return extension_filter


def validate_mappings(mappings: list[str] | None) -> list[str] | None:
    if mappings is None or len(mappings) == 0:
        return mappings
    pattern = re.compile(r'^[^>]+?>[^>]+$')
    for mapping in mappings:
        if not pattern.match(mapping):
            raise typer.BadParameter(f'Mapping "{mapping}" has a wrong format. Must be [extension>folder_name]')
    return mappings


def validate_extensions(extensions: str | None) -> str | None:
    if extensions is None:
        return None
    if re.search(r'^[a-z0-9]+?(?:,[a-z0-9]+?)*$', extensions.lower()):
        return extensions
    else:
        raise typer.BadParameter(f'Value "{extensions}" has a wrong format. '
                                 f'Must be a comma-separated list of extensions, e.g. "extension1[,extension2]"')


def validate_date_format(date_format: str) -> str | None:
    if date_format is None:
        return None
    if re.search(r'^[\w\s\.-]+$', date_format):
        return date_format
    else:
        raise typer.BadParameter(f'Value "{date_format}" has a wrong format. '
                                 f'It can only contain letters, digits, spaces, "_", "." and "-" characters.')


class SubGroupBy(StrEnum):
    EXT = 'ext'
    DATE = 'date'


class SortBy(StrEnum):
    NAME = 'name'
    DATETIME = 'datetime'
    SIZE = 'size'


@app.command()
def show(
        dir_: Annotated[
            str,
            typer.Argument(metavar='dir', show_default='current working directory', help=HelpText.show_dir)
        ] = None,
        sort_by: Annotated[
            Optional[SortBy], typer.Option('--sort-by', '-s', case_sensitive=False,
                                           help=HelpText.show_sort_by)
        ] = None,
        extensions: Annotated[
            Optional[str],
            typer.Option('--extensions', '-e', callback=validate_extensions,
                         show_default='all', help=HelpText.extensions)
        ] = None,
        dirs: Annotated[bool, typer.Option('--dirs', '-d', help=HelpText.show_dirs)] = False,
        files: Annotated[bool, typer.Option('--files', '-f', help=HelpText.show_files)] = False,
        desc: Annotated[bool, typer.Option('--desc', help=HelpText.show_desc)] = False
) -> None:
    """
    Displays the contents of the current working directory.
    """
    if dir_ is None:
        filelynx.update_cwd()
    else:
        try:
            filelynx.set_dir(dir_)
        except ValueError:
            err_console.print(f'ERROR: path "{dir_}" does not is not a valid directory!')
    type_filter = None
    if dirs and files:
        type_filter = ['folder', 'file']
    elif dirs:
        type_filter = ['folder']
    elif files:
        type_filter = ['file']

    extension_filter = _convert_extensions_arg(extensions) if extensions else None

    children = filelynx.ls(type_filter=type_filter, extension_filter=extension_filter, sort_by=sort_by,
                           ascending=not desc)

    table = Table('Name', 'Type', 'Modified', 'Size', 'Extension')
    for child in children:
        name = child.name
        type_ = determine_type(child)
        mod = child.stat().st_mtime
        mod = dt.datetime.fromtimestamp(mod).strftime('%d/%m/%Y, %H:%M:%S')
        size = child.stat().st_size
        extension = child.suffix.lower()
        table.add_row(name, type_, mod, str(size), extension)
    console.print(table)


@app.command(name='groupby')
def group_by(
        by: Annotated[SubGroupBy, typer.Argument(help=HelpText.groupby_by, case_sensitive=False, show_default=False)],
        ext_to_name_map: Annotated[
            list[str], typer.Option('--map', '-m', callback=validate_mappings,
                                    show_default='extensions names', help=HelpText.groupby_map)
        ] = [],
        date_format: Annotated[
            str,
            typer.Option('--format', '-f', callback=validate_date_format,
                         help=HelpText.groupby_date_format)
        ] = 'D-M-Y'
) -> None:
    """Groups files from the current working directory into subfolders.

    Possible to group by either file extension (by=ext) or file's last modified date (by=date).

    [--map, -m] option can be specified multiple times. It's used to specify the subfolder name for each file
    extension. By default, file extension names will be used as subfolder names. It takes a value of the following
    format: "[extension]>[folder_name]".

    The [--format, -f] option defines the date formatting to be used while naming subfolders. It can consist of
    the following symbols: lowercase and uppercase letters, digits, spaces, "_", ".", and "-". Provides the following
    wildcards:

    - d - day of month,

    - D - zero-padded day of month,

    - m - month number,

    - M - zero-padded month number,

    - month - abbreviated month name,

    - Month - full month name,

    - y - the last two digits of year,

    - Y - full year

    """
    filelynx.update_cwd()

    if ext_to_name_map is None:
        map_ = None
    else:
        map_ = dict()
        for mapping in ext_to_name_map:
            extension, folder_name = mapping.split('>')
            map_[extension.strip().lower()] = folder_name.strip()

    date_format = _convert_date_format(date_format)

    num_created = filelynx.subgroup(by, ext_to_name_map=map_, dt_format=date_format)

    console.print(f'{num_created} subfolders successfully created!')


@app.command(name='batchrename')
def batch_rename(
        name: Annotated[str, typer.Argument(help='New name to use while renaming.', show_default=False)],
        sep: Annotated[str, typer.Option('--sep', help=HelpText.br_sep)] = '_',
        num_start: Annotated[
            int,
            typer.Option('--num-start', '-S', help=HelpText.br_num_start,
                         rich_help_panel=HelpText.num_sets)
        ] = 1,
        num_first: Annotated[
            bool,
            typer.Option('--num-first', '-F', help=HelpText.br_num_first,
                         rich_help_panel=HelpText.num_sets)
        ] = False,
        pad: Annotated[
            int,
            typer.Option('--pad', '-p', help=HelpText.br_pad,
                         rich_help_panel=HelpText.num_sets)
        ] = 0,
        extensions: Annotated[
            Optional[str],
            typer.Option('--extensions', '-e', callback=validate_extensions,
                         help=HelpText.extensions, show_default='all', rich_help_panel=HelpText.f_s_opt)
        ] = None,
        after: Annotated[
            Optional[str],
            typer.Option('--after', '-a', help=HelpText.br_after,
                         rich_help_panel=HelpText.f_s_opt)
        ] = None,
        before: Annotated[
            Optional[str],
            typer.Option('--before', '-b', help=HelpText.br_before,
                         rich_help_panel=HelpText.f_s_opt)
        ] = None,
        sort_by: Annotated[
            Optional[SortBy],
            typer.Option('--sort-by', '-s', case_sensitive=False, help=HelpText.br_sort_by,
                         rich_help_panel=HelpText.f_s_opt)
        ] = None,
        desc: Annotated[
            bool,
            typer.Option('--desc', help=HelpText.br_desc, rich_help_panel=HelpText.f_s_opt)
        ] = False
) -> None:
    """Renames all files in the current directory with specified numbering applied.

    The resulting filenames will look something like: "{NAME}{SEP}{NUMERATOR}" or "{NUMERATOR}{SEP}{NAME}".
    """
    filelynx.update_cwd()

    extension_filter = _convert_extensions_arg(extensions) if extensions else None

    if after:
        try:
            after_dt = datetime.strptime(after, '%d-%m-%Y_%H:%M:%S')
        except ValueError:
            raise typer.BadParameter(f'value "{after}" must match format "%d-%m-%Y_%H:%M:%S"')
    else:
        after_dt = datetime.min
    if before:
        try:
            before_dt = datetime.strptime(before, '%d-%m-%Y_%H:%M:%S')
        except ValueError:
            raise typer.BadParameter(f'value "{before}" must match format "%d-%m-%Y_%H:%M:%S"')
    else:
        before_dt = datetime.max

    num_renamed = filelynx.batch_rename(name, sep=sep, numerator_start=num_start, numerator_first=num_first,
                                        zero_pad=pad, extension_filter=extension_filter, after=after_dt,
                                        before=before_dt, sort_by=sort_by, ascending=not desc)

    print(f'Renamed {num_renamed} files successfully!')


@app.callback(invoke_without_command=True)
def main(
        ctx: typer.Context,
        show_version: Annotated[bool, typer.Option('--version', help=HelpText.show_version)] = False,
) -> None:
    """:floppy_disk:  **FileLynx** :floppy_disk:  - a handy file organisation tool
    """
    if ctx.invoked_subcommand is not None:
        return
    if show_version:
        print(f'FileLynx version: {VERSION}')


if __name__ == '__main__':
    app()
