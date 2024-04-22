import os
from datetime import datetime, date
from pathlib import Path
from utils import determine_type
from typing import Optional, Literal, Generator, List


class FileLynx:
    def __init__(self, cur_dir: str | Path):
        path = Path(cur_dir)
        if not path.exists():
            raise ValueError(f'{cur_dir} is not an existing path.')
        if not path.is_dir():
            raise ValueError(f'{cur_dir} is not a directory.')
        self.cur_dir = path

    def set_dir(self, new_dir: str | Path):
        """Sets the FileLynx's current directory to the one specified by `new_dir`.

        Args:
            new_dir: Directory to switch to.

        Returns:
            None

        Raises:
            ValueError: if `new_path` does not point to an existing directory.
        """
        new_path = Path(new_dir)
        if not new_path.exists():
            raise ValueError('[new_dir] argument is not an existing path.')
        if not new_path.is_dir():
            raise ValueError('[new_dir] argument is not a directory.')
        self.cur_dir = new_path

    def update_cwd(self) -> None:
        """Updates the FileLynx's current directory to the system's current working directory (cwd).

        Returns:
            None
        """
        self.cur_dir = Path(os.getcwd())

    def ls(
        self,
        type_filter: Optional[list[str]] = None,
        extension_filter: Optional[list[str]] = None,
        sort_by: Optional[Literal['name', 'datetime', 'size'] | str] = None,
        ascending: bool = True
    ) -> list[Path]:
        """Yields current directory contents.

        Args:
            type_filter: Specifies the type of child elements to display. Must be a list consisting of
                values "file", "folder". If None, no filtering will be applied.
            extension_filter: Specifies the file extensions of child elements to be shown. Does not affect folders.
                Must be a list consisting of extension names, e.g. "jpg", "txt", "docx" and others. Invalid extension
                names are ignored. If None, no filtering will be applied.
            sort_by: Defines the metric by which child elements should be sorted. Must be one of "name", "datetime"
                or "size". If None, default sorting will be used.
            ascending: Whether elements should be sorted in ascending or descending order.

        Returns:
            A sorted (and filtered) list of current directory's child Path objects.
        Raises:
            ValueError: if `type_filer` parameter contains items other than "file" or "folder";
                if `sort_by` parameter is anything else than "name", "datetime" or "size"
        """
        if type_filter:
            type_filter = [tf.lower() for tf in type_filter]
        if extension_filter:
            extension_filter = [ef.lower() for ef in extension_filter]
        if sort_by:
            sort_by = sort_by.lower()

        if type_filter and not set(type_filter).issubset({'file', 'folder'}):
            raise ValueError('[type_filter] parameter contains invalid items. Must be one of: "file", "folder".')
        if sort_by and sort_by not in ['name', 'datetime', 'size']:
            raise ValueError(f'"{sort_by}" is not a valid sorting key. Must be one of: "name", "datetime", "size".')

        if sort_by == 'name':
            sort_key = lambda f: f.stem.lower()
        elif sort_by == 'datetime':
            sort_key = lambda f: f.stat().st_mtime
        elif sort_by == 'size':
            sort_key = lambda f: f.stat().st_size
        else:
            sort_key = lambda f: f.stem.lower()

        sorted_ = sorted(self.cur_dir.iterdir(), key=sort_key, reverse=not ascending)

        to_display = []
        for child in sorted_:
            type_ = determine_type(child)
            if type_filter and type_ not in type_filter:
                continue
            if extension_filter and (child.suffix[1:].lower() not in extension_filter or child.suffix == ''):
                continue
            to_display.append(child)
        return to_display

    def subgroup(
            self,
            by: Literal['ext', 'date'] | str,
            ext_to_name_map: Optional[dict[str, str]] = None,
            dt_format: str = '%d-%m-%Y'
    ) -> int:
        """Groups files from `cur_dir` directory into separate subfolders based on a specified file metadata.

        Args:
            by: File metadata by which files should be grouped. Has to be one of ['ext', 'date'].
                ext - file extension,
                date - file creation/modification date
            ext_to_name_map: An optional mapping of file extensions to subfolder names
                (e.g. `{'txt': 'Text', 'jpg': 'Images'}`). If not given, file extension names will be used as
                subfolder names. Taken into account only when `by` parameter is set to 'ext'.
            dt_format: Sets the datetime formatting for subfolder names. Accepts format codes from the 1989 C standard,
                e.g. "%d/%m/%Y". Taken into account only when `by` parameter is set to 'date'.

        Returns:
            The number of subfolders created.

        Raises:
            ValueError: If `by` is anything else than "ext" or "date".
        """
        if by:
            by = by.lower()
        if ext_to_name_map:
            ext_to_name_map = {k.lower(): v for k, v in ext_to_name_map.items()}

        if by not in ['ext', 'date']:
            raise ValueError('[by] parameter contains an invalid subgrouping condition.')

        files = [f for f in self.cur_dir.iterdir() if f.is_file()]
        subfolders = 0

        if by == 'ext':
            for f in files:
                # exists_count = 1
                if ext_to_name_map and f.suffix[1:].lower() in ext_to_name_map:
                    subfolder_name = ext_to_name_map[f.suffix[1:].lower()]
                else:
                    subfolder_name = f.suffix[1:].lower()

                extension_dir = self.cur_dir / subfolder_name
                if not extension_dir.exists():
                    extension_dir.mkdir()
                    subfolders += 1
                new_path = extension_dir / f.name
                if new_path.exists():
                    new_path = new_path.with_stem(f'{new_path.stem} (1)')
                    # exists_count += 1
                f.replace(new_path)

        elif by == 'date':
            for f in files:
                subfolder_name = date.fromtimestamp(f.stat().st_mtime).strftime(dt_format)

                extension_dir = self.cur_dir / subfolder_name
                if not extension_dir.exists():
                    extension_dir.mkdir()
                    subfolders += 1
                new_path = extension_dir / f.name
                if new_path.exists():
                    new_path = new_path.with_stem(f'{new_path.stem} (1)')
                f.replace(new_path)

        return subfolders

    def batch_rename(
            self,
            new_name: str,
            sep: str = '_',
            numerator_start: int = 1,
            numerator_first: bool = False,
            zero_pad: int = 0,
            extension_filter: Optional[list[str]] = None,
            after: datetime = datetime.min,
            before: datetime = datetime.max,
            sort_by: Literal['name', 'datetime', 'size'] | str | None = None,
            ascending: bool = True,
    ) -> int:
        """Renames all files in the current directory to `new_name` with the specified numbering applied.

        The name and numerator are separated with underscore "_" by default. This can be modified by the `sep`
        parameter. So, the resulting filenames would look like: {name}_{numerator} or {numerator}_{name}.

        Certain filtering options can be applied to limit the number of files that will be renamed. Files can also be
        sorted in various ways which will influence the numerator's numbering order

        Args:
            new_name: New name's stem.
            sep: Specifies the separator i.e. the symbols that'll appear between `new_name` and the numerator.
            numerator_start: Defines the starting point of files' numbering. Can't be less than zero.
            numerator_first: Whether numbering should be placed before the name stem. False by default.
            zero_pad: Specifies the length of zero-padding applied to file numbering. By default, no padding is applied.
            extension_filter: A list of file extensions which limits the files selected for renaming. By default, files
                with any extension will be renamed.
            after: Only files with last_modified datetime later than this one will be renamed. No filtering by default.
            before: Only files with last_modified datetime earlier than this one will be renamed.
                No filtering by default.
            sort_by: Defines the metric by which child elements should be sorted. Must be one of "name", "datetime"
                or "size". None by default - no sorting will be used.
            ascending: Whether elements should be sorted in ascending or descending order. Ignored if `sort_by` is None.

        Returns:
            The number of files renamed.

        Raises:
            ValueError: if `before` argument is an earlier datetime than `after`;
                if `sort_by` is anything else than "name", "datetime" or "size";
                if `numerator_start` is less than zero
        """
        if extension_filter:
            extension_filter = [ef.lower() for ef in extension_filter]
        if sort_by:
            sort_by = sort_by.lower()

        if after > before:
            raise ValueError('[before] argument can\'t be less than [after].')
        if sort_by and sort_by.lower() not in ['name', 'datetime', 'size']:
            raise ValueError('[sort_by] argument contains an invalid sorting key.')
        if numerator_start < 0:
            raise ValueError('[numerator_start] cannot be below zero.')

        filtered = []
        for f in self.cur_dir.iterdir():
            if not f.is_file():
                continue
            if extension_filter and f.suffix[1:].lower() not in extension_filter:
                continue
            f_mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if f_mtime < after or f_mtime > before:
                continue
            filtered.append(f)

        sort_key = None
        if sort_by:
            sort_by = sort_by.lower()
        if sort_by == 'name':
            sort_key = lambda f: f.stem.lower()
        elif sort_by == 'datetime':
            sort_key = lambda f: f.stat().st_mtime
        elif sort_by == 'size':
            sort_key = lambda f: f.stat().st_size

        if sort_key:
            filtered_sorted = sorted(filtered, key=sort_key, reverse=not ascending)
        else:
            filtered_sorted = filtered

        counter = 0

        numerator = numerator_start
        exists_counter = 1
        for f in filtered_sorted:
            if numerator_first:
                new_name_stem = '{}{}{}'.format(str(numerator).zfill(zero_pad), sep, new_name)
            else:
                new_name_stem = '{}{}{}'.format(new_name, sep, str(numerator).zfill(zero_pad))
            new_path = f.with_stem(new_name_stem)
            while new_path.exists():
                new_path = new_path.with_stem(f'{new_name_stem} ({exists_counter})')
                exists_counter += 1
            f.rename(new_path)
            numerator += 1
            counter += 1

        return counter


if __name__ == '__main__':
    fl = FileLynx('D:/temp/fl-tests/')
    # fl.batch_rename('image', zero_pad=4, sep=' - ')
    lst = list(fl.ls(type_filter=['ahguh']))
    print(lst)
